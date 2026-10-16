"""원본 권한·확정값 재검사·이슈 확인 이력의 실제 연결을 검증한다."""

from sqlmodel import Session, select

from app.models import AuditLog, Claim, ExtractedField
from tests.engine_fakes import app_files, install_fake


def prepare(client):
    install_fake(client.app)
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    base = "/api/claims/GA-2610-0482"
    client.post(base + "/documents", files=app_files())
    client.post(base + "/silson24")
    assert client.post(base + "/process").status_code == 202
    return base, client.get(base).json()


def test_document_field_confirmation_and_issue_resolution(client):
    base, data = prepare(client)
    doc = next(d for d in data["documents"] if d["doc_type"] == "diagnosis")
    assert client.get(f"/api/documents/{doc['id']}/image").headers["content-type"] == "image/png"
    assert client.get(f"/api/documents/{doc['id']}").json()["fields"]
    electronic = next(d for d in data["documents"] if d["source"] == "silson24")
    assert client.get(f"/api/documents/{electronic['id']}/image").status_code == 200
    field = next(
        f for f in data["fields"] if f["document_id"] == doc["id"] and f["key"] == "diagnosis_date"
    )
    assert (
        client.patch(f"/api/fields/{field['id']}", json={"confirmed_value": "bad"}).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/fields/{field['id']}", json={"confirmed_value": "2026-09-23"}
        ).status_code
        == 200
    )
    changed = client.get(base).json()
    assert not any(i["rule_id"] == "CV-01" and i["status"] == "open" for i in changed["issues"])
    with Session(client.app.state.engine) as s:
        stored = s.get(ExtractedField, field["id"])
        assert stored.value == "2026-09-18" and stored.confirmed_value == "2026-09-23"
        assert s.exec(select(AuditLog).where(AuditLog.action == "field_confirm")).first()
    issue = next(i for i in changed["issues"] if i["status"] == "open" and i["kind"] != "missing")
    assert client.post(f"/api/issues/{issue['id']}/resolve").json()["status"] == "resolved"
    assert client.post(f"/api/issues/{issue['id']}/resolve").status_code == 200
    client.post("/api/auth/demo-login", json={"role": "admin"})
    assert (
        client.patch(
            f"/api/fields/{field['id']}", json={"confirmed_value": "2026-09-24"}
        ).status_code
        == 403
    )
    assert client.post(f"/api/issues/{issue['id']}/resolve").status_code == 403
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    with Session(client.app.state.engine) as s:
        c = s.get(Claim, "GA-2610-0482")
        c.assignee_id = 2
        s.add(c)
        s.commit()
    assert client.get(f"/api/documents/{doc['id']}/image").status_code == 403
