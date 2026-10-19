"""빈 배포 디스크 재현과 비밀/평가 자료 제외 검사. 실제 HTTP는 conftest에서 금지한다."""

import hashlib
import json
import tarfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import PROJECT_ROOT, Settings
from app.main import create_app
from app.models import Customer, Document
from app.scripts.deploy_start import prepare
from app.services.demo_reset import reset_demo


def config_for(folder):
    return Settings(
        _env_file=None,
        DEPLOY_RUNTIME_DIR=folder,
        UPSTAGE_API_KEY="",
        USE_CACHED_RESULTS=True,
        SESSION_HTTPS_ONLY=True,
        CORS_ORIGINS=["https://demo.example"],
    )


def test_allowlist_and_source_texts():
    config = config_for(Path("/tmp/unused-deployment-path"))
    hashes = {
        hashlib.sha256(p.read_bytes()).hexdigest() for p in config.SAMPLES_ROOT.rglob("*.png")
    }
    with tarfile.open(config.DEPLOY_ASSETS_PATH) as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            assert member.isfile() and ".." not in parts and not member.name.startswith("/")
            body = archive.extractfile(member).read()
            if parts[0] == "cache" and parts[1] not in {"kb_nodes.json", "_budget.json"}:
                assert parts[1] in hashes
                assert json.loads(body)["status_code"] == 200
            else:
                assert member.name in {
                    "cache/kb_nodes.json",
                    "cache/_budget.json",
                    "qdrant/meta.json",
                    "qdrant/collection/manual/storage.sqlite",
                    "qdrant/collection/policy/storage.sqlite",
                }
            assert b"/Users/" not in body
            assert b"data/eval/" not in body
            assert b"data/kb/reference" not in body
    texts = json.loads((PROJECT_ROOT / "frontend/server-data/source-texts.json").read_text())
    assert len(texts) == 12
    for name, body in texts.items():
        assert (PROJECT_ROOT / name).read_text() == body


def test_fresh_disk_chat_reset_and_restart(tmp_path):
    config = config_for(tmp_path)
    started = time.monotonic()
    assert prepare(config)["seed"] == {"users": 2, "claims": 13, "documents": 29}
    assert time.monotonic() - started < 30
    with TestClient(create_app(config), base_url="https://demo.example") as client:
        assert client.get("/health").json() == {"status": "ok"}
        login = client.post("/api/auth/demo-login", json={"role": "reviewer"})
        assert login.status_code == 200
        assert "secure" in login.headers["set-cookie"].lower()
        assert client.get("/api/me").status_code == 200
        with Session(client.app.state.engine) as session:
            assert len(session.exec(select(Customer)).all()) == 10
            docs = session.exec(select(Document)).all()
            assert len(docs) == 29
            assert any(d.provenance == "upstage" for d in docs)
        for question in (
            "이 청구 건 서류 다 왔는지 검토해줘",
            "이 건 영수증에 보상 제외될 항목 있어?",
            "누락 서류 보완 요청 문자 써줘",
            "이 건 지급 심사로 넘겨도 돼?",
        ):
            response = client.post(
                "/api/chat", json={"message": question, "claim_id": "GA-2610-0482"}
            )
            assert response.status_code == 200, response.text
    reset = reset_demo(config)
    assert reset["within_limit"] and Path(reset["backup"]).is_file()
    assert not config.DEMO_CALL_LOG.exists()
    marker = config.CACHE_PATH / "keep-test.json"
    marker.write_text('{"preserve":true}')
    assert prepare(config)["seed"]["documents"] == 0
    assert marker.read_text() == '{"preserve":true}'
    assert len(list((tmp_path / "backup").glob("*.db"))) == 2


def test_modified_asset_rejected_before_writes(tmp_path):
    config = config_for(tmp_path / "runtime")
    manifest = json.loads(config.DEPLOY_MANIFEST_PATH.read_text())
    manifest[next(iter(manifest))] = "wrong"
    path = tmp_path / "wrong.json"
    path.write_text(json.dumps(manifest))
    config.DEPLOY_MANIFEST_PATH = path
    with pytest.raises(ValueError, match="해시"):
        prepare(config)
    assert not list(config.DATA_PATH.rglob("*.json"))
