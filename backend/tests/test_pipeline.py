"""실제 라우트·DB·작업 실행을 통과하되 외부 HTTP만 모킹하는 통합 테스트."""

from engine_fakes import app_files, install_fake
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import create_app
from app.models import Claim, Document, ExtractedField, Issue, ProcessJob

URL = "/api/claims/GA-2610-0482"


def prepare(client, fail=False):
    calls = install_fake(client.app, fail_extract=fail)
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    assert client.post(URL + "/documents", files=app_files()).status_code == 200
    assert client.post(URL + "/silson24").status_code == 200
    return calls


def test_complete_pipeline_idempotent_retry_and_audit(client):
    calls = prepare(client)
    first = client.post(URL + "/process")
    assert first.status_code == 202
    status = client.get(URL + "/process/status", params={"job_id": first.json()["job_id"]}).json()
    assert status["state"] == "done" and status["progress"] == 100
    assert status["result"]["claim_status"] == "supplement" and status["result"]["issue_count"] == 3
    assert len(calls) == 12
    with Session(client.app.state.engine) as session:
        assert len(session.exec(select(Document)).all()) == 7
        ids = {i.id for i in session.exec(select(Issue)).all()}
        fields = session.exec(select(ExtractedField)).all()
        assert any(f.method == "data" and f.extract_conf is None for f in fields)
        assert any(f.bbox is not None and f.method == "parse" for f in fields)
    assert client.post(URL + "/process").status_code == 202
    assert len(calls) == 12  # 재실행해도 성공 응답을 전부 재사용한다.
    with Session(client.app.state.engine) as session:
        assert {i.id for i in session.exec(select(Issue)).all()} == ids
    logs = client.get(URL + "/logs").json()
    assert {"upload", "silson24_receive", "process_start", "process_done"} <= {
        l["action"] for l in logs
    }


def test_failure_visible_never_auto_pass_and_secret_not_in_result(client):
    prepare(client, True)
    assert client.post(URL + "/process").status_code == 202
    status = client.get(URL + "/process/status").json()
    assert status["state"] == "failed" and len(status["errors"]) == 4
    assert status["result"]["claim_status"] != "auto_pass"
    assert "mock-secret" not in str(status)
    assert "process_failed" in {l["action"] for l in client.get(URL + "/logs").json()}


def test_upload_validation_role_busy_and_restart_recovery(client):
    assert client.post(URL + "/documents", files=app_files()).status_code == 401
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    assert client.post(URL + "/process").status_code == 422
    assert (
        client.post(
            URL + "/documents", files=[("files", ("x.png", b"not png", "image/png"))]
        ).status_code
        == 422
    )
    assert (
        client.post(
            URL + "/documents", files=[("files", ("x.txt", b"text", "text/plain"))]
        ).status_code
        == 415
    )
    assert client.post(URL + "/documents", files=app_files()).status_code == 200
    assert client.post(URL + "/documents", files=app_files()).status_code == 200
    with Session(client.app.state.engine) as session:
        assert len(session.exec(select(Document)).all()) == 4
        session.add(ProcessJob(id="queued-job", claim_id="GA-2610-0482", actor_id=1))
        session.commit()
    assert client.post(URL + "/process").status_code == 409
    assert client.post(URL + "/documents", files=app_files()).status_code == 409
    assert client.post(URL + "/silson24").status_code == 409
    with TestClient(create_app(client.app.state.settings)) as restarted:
        restarted.post("/api/auth/demo-login", json={"role": "reviewer"})
        status = restarted.get(URL + "/process/status").json()
        assert status["state"] == "failed" and status["errors"][0]["code"] == "process_interrupted"
    client.post("/api/auth/demo-login", json={"role": "admin"})
    assert client.post(URL + "/process").status_code == 403
    assert client.post(URL + "/documents", files=app_files()).status_code == 403


def test_status_cannot_read_another_claim_and_limits(client):
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    assert client.get(URL + "/process/status").json()["state"] == "idle"
    assert client.get(URL + "/process/status?job_id=missing").status_code == 404
    client.app.state.settings.UPLOAD_MAX_BYTES = 4
    assert client.post(URL + "/documents", files=app_files()).status_code == 413
    with Session(client.app.state.engine) as session:
        claim = session.get(Claim, "GA-2610-0482")
        claim.assignee_id = 2
        session.add(claim)
        session.commit()
    assert client.get(URL + "/process/status").status_code == 403


def test_pdf_page_limit_and_atomic_batch_validation(client):
    from io import BytesIO

    from pypdf import PdfWriter

    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    mixed = app_files()[:1] + [("files", ("invalid.png", b"invalid", "image/png"))]
    assert client.post(URL + "/documents", files=mixed).status_code == 422
    with Session(client.app.state.engine) as s:
        assert not s.exec(select(Document)).all()
    writer = PdfWriter()
    for _ in range(8):
        writer.add_blank_page(width=100, height=100)
    output = BytesIO()
    writer.write(output)
    assert (
        client.post(
            URL + "/documents",
            files=[("files", ("eight.pdf", output.getvalue(), "application/pdf"))],
        ).status_code
        == 200
    )
    assert client.post(URL + "/silson24").status_code == 422  # 파일 4개여도 총 11페이지는 거절한다.
