"""시연 초기화·기한·캐시 우선: 실제 HTTP는 사용하지 않는다."""

import sqlite3
import time
from threading import Event

import httpx
import pytest
from sqlmodel import Session, select

from app.agent.solar import Solar
from app.models import Claim, SupplementRequest
from app.services.demo_deadline import cached_deadline
from app.services.demo_reset import read_revision, reset_demo


def reset_config(client, tmp_path):
    config = client.app.state.settings.model_copy(
        update={
            "QDRANT_PATH": tmp_path / "qdrant",
            "KB_STRUCTURE_PATH": tmp_path / "cache/kb_nodes.json",
            "MOCK_SILSON24_PATH": tmp_path / "silson24",
        }
    )
    for name in config.KB_COLLECTIONS:
        (config.QDRANT_PATH / "collection" / name).mkdir(parents=True)
    config.CACHE_PATH.mkdir(exist_ok=True)
    config.KB_STRUCTURE_PATH.write_text("{}")
    return config


def test_reset_backups_and_preserves_assets(client, tmp_path):
    config = reset_config(client, tmp_path)
    cache = config.CACHE_PATH / "keep.json"
    cache.write_text('{"cached":true}')
    with Session(client.app.state.engine) as session:
        claim = session.get(Claim, "GA-2610-0482")
        claim.review_note = "보존할 백업 메모"
        claim.step = 2
        session.add(claim)
        session.commit()
    first = reset_demo(config)
    second = reset_demo(config)
    assert first["backup"] != second["backup"]
    with sqlite3.connect(first["backup"]) as backup:
        assert (
            backup.execute("select review_note from claims where id='GA-2610-0482'").fetchone()[0]
            == "보존할 백업 메모"
        )
    with Session(client.app.state.engine) as session:
        claim = session.get(Claim, "GA-2610-0482")
        assert claim.review_note == "" and claim.step == 0
        assert not session.exec(select(SupplementRequest)).all()
    assert cache.read_text() == '{"cached":true}'
    assert config.KB_STRUCTURE_PATH.read_text() == "{}"
    assert read_revision(config) == second["revision"] != first["revision"]
    assert first["within_limit"] and first["seed"]["documents"] == 29


def test_reset_checks_assets_and_mode(client, tmp_path):
    config = reset_config(client, tmp_path)
    config.KB_STRUCTURE_PATH.unlink()
    with pytest.raises(ValueError, match="시연 자산"):
        reset_demo(config)
    assert not (tmp_path / "backup").exists()
    with pytest.raises(ValueError, match="시연 모드"):
        reset_demo(config.model_copy(update={"DEMO_MODE": False}))


def test_reset_api_permissions_and_confirmation(client, tmp_path):
    client.app.state.settings = reset_config(client, tmp_path)
    assert client.post("/api/demo/reset", json={"confirm": True}).status_code == 401
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    assert client.post("/api/demo/reset", json={"confirm": True}).status_code == 403
    client.post("/api/auth/demo-login", json={"role": "admin"})
    assert client.post("/api/demo/reset", json={"confirm": False}).status_code == 422
    result = client.post("/api/demo/reset", json={"confirm": True})
    assert result.status_code == 200 and result.json()["within_limit"]
    assert client.get("/api/me").status_code == 401


def test_deadline_and_failure_fallback(client):
    config = client.app.state.settings.model_copy(update={"DEMO_API_DEADLINE_SEC": 0.03})
    done = Event()

    def slow():
        done.wait(1)
        return {"late": True}

    started = time.monotonic()
    try:
        assert cached_deadline(config, slow, lambda: {"cached": True}, "test") == {"cached": True}
        assert time.monotonic() - started < 0.5
    finally:
        done.set()

    try:
        done.clear()
        with pytest.raises(RuntimeError, match="demo_api_deadline"):
            cached_deadline(config, slow, lambda: None, "test")
    finally:
        done.set()

    def failed():
        raise RuntimeError("offline")

    assert cached_deadline(config, failed, lambda: {"cached": True}, "test") == {"cached": True}
    with pytest.raises(RuntimeError, match="offline"):
        cached_deadline(config, failed, lambda: None, "test")


def test_solar_cache_first_and_call_counter(client, tmp_path):
    config = client.app.state.settings.model_copy(
        update={
            "SOLAR_RESPONSE_CACHE": True,
            "USE_CACHED_RESULTS": False,
            "DEMO_CALL_LOG": tmp_path / "calls.jsonl",
        }
    )
    result = {"choices": [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}]}
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=result)

    solar = Solar(config, httpx.MockTransport(respond))
    assert solar.post(config.SOLAR_CHAT_PATH, {"messages": []}) == result
    assert solar.post(config.SOLAR_CHAT_PATH, {"messages": []}) == result
    assert len(calls) == 1
    assert len(config.DEMO_CALL_LOG.read_text().splitlines()) == 1
    assert "Authorization" not in config.DEMO_CALL_LOG.read_text()
