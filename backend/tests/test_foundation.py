"""기반 계약 검증: 설정, 건강 확인, 테이블 연결 무결성을 실제 DB에서 확인한다."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.config import Settings
from app.main import create_app
from app.models import Claim


def test_health_and_tables(tmp_path):
    config = Settings(_env_file=None, DB_URL=f"sqlite:///{tmp_path / 'test.db'}")
    with TestClient(create_app(config)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        tables = set(inspect(client.app.state.engine).get_table_names())
        assert tables == {
            "users",
            "process_jobs",
            "claims",
            "documents",
            "fields",
            "issues",
            "supplement_requests",
            "audit_logs",
            "settings",
            "required_doc_rules",
            "cross_check_rules",
            "kcd_codes",
            "drug_catalog",
        }
        with Session(client.app.state.engine) as session:
            session.add(Claim(id="TEST", customer_name="가상", policy_no="DEMO", assignee_id=999))
            with pytest.raises(IntegrityError):
                session.commit()


def test_settings_env_and_secret(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("UPSTAGE_API_KEY=fictional-secret\nMAX_FILES_PER_CLAIM=7\n")
    monkeypatch.setenv("MAX_FILES_PER_CLAIM", "9")
    config = Settings(_env_file=env)
    assert config.MAX_FILES_PER_CLAIM == 9
    assert "fictional-secret" not in repr(config)
    assert config.UPSTAGE_API_KEY.get_secret_value() == "fictional-secret"
