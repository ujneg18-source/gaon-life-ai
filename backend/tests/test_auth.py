"""쿠키 발급·변조·역할 변경과 관리자 API 거절을 검증한다."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.auth import require_claim_access
from app.config import Settings
from app.main import create_app
from app.models import AuditLog, Claim, Role, User
from scripts.seed import seed_database


@pytest.fixture
def client(tmp_path):
    settings = Settings(_env_file=None, DB_URL=f"sqlite:///{tmp_path / 'auth.db'}")
    with TestClient(create_app(settings)) as client:
        seed_database(client.app.state.engine, settings)
        yield client


def test_login_me_logout_and_role_switch(client):
    assert client.get("/api/me").status_code == 401
    result = client.post("/api/auth/demo-login", json={"role": "reviewer"})
    assert result.status_code == 200
    assert result.json()["name"] == "한지원"
    cookie = result.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert client.get("/api/me").json()["role"] == "reviewer"
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/me").status_code == 401
    assert client.post("/api/auth/demo-login", json={"role": "admin"}).json()["name"] == "오세린"
    assert client.get("/api/me").json()["role"] == "admin"


def test_admin_guard_and_audit(client):
    assert client.patch("/api/settings", json={"review_on_low_conf": False}).status_code == 401
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    assert client.get("/api/settings").status_code == 200
    assert client.patch("/api/settings", json={"review_on_low_conf": False}).status_code == 403
    client.post("/api/auth/demo-login", json={"role": "admin"})
    result = client.patch("/api/settings", json={"review_on_low_conf": False})
    assert result.status_code == 200 and result.json()["review_on_low_conf"] is False
    assert client.patch("/api/settings", json={"auto_pass_threshold": 2}).status_code == 422
    assert client.patch("/api/settings", json={"review_on_low_conf": None}).status_code == 422
    with Session(client.app.state.engine) as session:
        logs = session.exec(select(AuditLog).where(AuditLog.action == "setting_change")).all()
        assert len(logs) == 1 and logs[0].detail["before"]["review_on_low_conf"] is True


def test_tampered_cookie_and_invalid_role(client):
    client.cookies.set("gaon_session", "tampered")
    assert client.get("/api/me").status_code == 401
    assert client.post("/api/auth/demo-login", json={"role": "owner"}).status_code == 422
    assert client.post("/api/auth/demo-login", json={"role": "admin", "id": 1}).status_code == 422


def test_foreign_origin_rejected(client):
    assert (
        client.post(
            "/api/auth/demo-login",
            json={"role": "admin"},
            headers={"Origin": "https://untrusted.example"},
        ).status_code
        == 403
    )


def test_role_is_loaded_from_db(client):
    client.post("/api/auth/demo-login", json={"role": "admin"})
    with Session(client.app.state.engine) as session:
        user = session.exec(select(User).where(User.role == Role.ADMIN)).one()
        user.role = Role.REVIEWER
        session.add(user)
        session.commit()
    assert client.patch("/api/settings", json={"review_on_low_conf": False}).status_code == 403


def test_claim_access_uses_assignment(client):
    from fastapi import HTTPException

    with Session(client.app.state.engine) as session:
        reviewer = session.exec(select(User).where(User.role == Role.REVIEWER)).one()
        admin = session.exec(select(User).where(User.role == Role.ADMIN)).one()
        other = User(email="other@gaon.demo", name="가상 담당자", role=Role.REVIEWER)
        session.add(other)
        session.commit()
        assert require_claim_access("GA-2610-0482", reviewer, session).assignee_id == reviewer.id
        assert isinstance(require_claim_access("GA-2610-0482", admin, session), Claim)
        with pytest.raises(HTTPException) as error:
            require_claim_access("GA-2610-0482", other, session)
        assert error.value.status_code == 403
