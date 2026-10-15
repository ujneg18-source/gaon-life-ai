"""엔진 테스트는 임시 DB·설정으로 격리하고, 기본 테스트에서 실제 HTTP를 금지한다."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from scripts.seed import seed_database


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        _env_file=None,
        DB_URL=f"sqlite:///{tmp_path / 'test.db'}",
        DATA_PATH=tmp_path,
        UPLOAD_PATH=tmp_path / "uploads",
        CACHE_PATH=tmp_path / "cache",
    )
    with TestClient(create_app(settings)) as client:
        seed_database(client.app.state.engine, settings)
        yield client


@pytest.fixture(autouse=True)
def block_real_http(request, monkeypatch):
    """자동 테스트에서 캐시를 놓쳐도 실제 과금 호출로 이어지지 않도록 전송 계층을 막는다."""
    if request.node.get_closest_marker("live"):
        return
    import httpx

    def denied(*args, **kwargs):
        raise AssertionError("실제 HTTP 금지: MockTransport를 사용하거나 -m live로 분리하세요.")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", denied)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", denied)
