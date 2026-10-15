"""외부 HTTP를 모킹해 비용·실패·동시 실행과 캐시 전용 모드를 검증한다."""

import json
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr

from app.config import Settings
from app.services.upstage import UpstageClient, UpstageError


@pytest.fixture
def setup(tmp_path):
    path = tmp_path / "sample.png"
    Image.new("RGB", (20, 30), "white").save(path)
    config = Settings(
        _env_file=None,
        UPSTAGE_API_KEY=SecretStr("not-a-real-key"),
        CACHE_PATH=tmp_path / "cache",
        UPSTAGE_RETRY_DELAY_SEC=0,
    )
    return config, path


def test_v1_payloads_cache_and_schema_change(setup):
    config, path = setup
    requests = []

    def handle(request):
        requests.append(request)
        if "document-digitization" not in str(request.url):
            body = json.loads(request.content)
            if "information-extraction" in str(request.url):
                assert body["confidence"] is True and body["location"] is True
                assert body["location_granularity"] == "word"
            else:
                assert len(body["response_format"]["json_schema"]["schema"]["oneOf"]) == 24
        else:
            assert b'name="document"' in request.content and b"force" in request.content
        return httpx.Response(200, json={"model": "mock", "content": "safe"})

    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    with UpstageClient(config, transport=httpx.MockTransport(handle)) as client:
        client.classify(path)
        client.parse(path)
        client.extract(path, schema, "diagnosis")
        client.classify(path)
        client.parse(path)
        client.extract(path, schema, "diagnosis")
        assert len(requests) == 3 and client.cache_hits == 3
        client.extract(path, {**schema, "description": "changed"}, "diagnosis")
        assert len(requests) == 4
        assert client.budget()["reserved_pages"] == 4
    assert all("/v1/" in str(r.url) for r in requests)
    offline = config.model_copy(
        update={"USE_CACHED_RESULTS": True, "UPSTAGE_API_KEY": SecretStr("")}
    )
    with UpstageClient(offline) as client:
        client.parse(path)
        with pytest.raises(UpstageError, match="cache_miss"):
            client.extract(path, {}, "new")


def test_retry_429_and_never_retry_read_timeout(setup):
    config, path = setup
    calls = []

    def handle(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, json={"error": "busy"})
        return httpx.Response(200, json={"elements": []})

    with UpstageClient(config, transport=httpx.MockTransport(handle)) as client:
        client.parse(path)
        assert len(calls) == 2 and client.budget()["reserved_pages"] == 2

    def timeout(request):
        raise httpx.ReadTimeout("do not expose request secrets")

    with UpstageClient(config, transport=httpx.MockTransport(timeout)) as client:
        with pytest.raises(UpstageError, match="ambiguous_network_failure"):
            client.classify(path)
        with pytest.raises(UpstageError, match="ambiguous_previous_request"):
            client.classify(path)
        assert client.requests_made == 1


def test_budget_and_concurrent_deduplication(setup):
    config, path = setup
    config.UPSTAGE_PAGE_LIMIT = 1

    def run(_):
        with UpstageClient(
            config, transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"ok": True}))
        ) as client:
            return client.parse(path)

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(run, range(2))) == [{"ok": True}] * 2
    with UpstageClient(config) as client:
        with pytest.raises(UpstageError, match="page_budget_exceeded"):
            client.classify(path)
        assert client.budget()["reserved_pages"] == 1


def test_errors_are_cached_and_secret_redacted(setup):
    config, path = setup
    key = config.UPSTAGE_API_KEY.get_secret_value()
    with UpstageClient(
        config, transport=httpx.MockTransport(lambda r: httpx.Response(403, json={"error": key}))
    ) as client:
        with pytest.raises(UpstageError, match="http_403"):
            client.parse(path)
        with pytest.raises(UpstageError, match="cached_http_403"):
            client.parse(path)
        assert client.requests_made == 1
    assert all(key not in p.read_text() for p in config.CACHE_PATH.rglob("*.json"))
