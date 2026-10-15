"""정답 기반 모의 전자 데이터의 연결·중복·접근 범위를 실제 DB에서 확인한다."""

import json

from sqlmodel import Session, select

from app.config import PROJECT_ROOT
from app.models import AuditLog, Claim, Document


def test_attach_three_documents_idempotently(client):
    url = "/api/claims/GA-2610-0482/silson24"
    assert client.post(url).status_code == 401
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    first = client.post(url)
    assert first.status_code == 200
    assert {d["doc_type"] for d in first.json()["documents"]} == {
        "medical_receipt",
        "medical_detail",
        "prescription",
    }
    assert client.post(url).json() == first.json()
    with Session(client.app.state.engine) as session:
        docs = session.exec(select(Document)).all()
        assert len(docs) == 3
        for doc in docs:
            expected = next(
                (PROJECT_ROOT / "data/samples/kim_yujeong/answers").glob(f"*_{doc.doc_type}.json")
            )
            data = json.loads(expected.read_text())
            assert all(
                doc.raw_result["data"][k] == v for k, v in data.items() if not k.startswith("_")
            )
        assert (
            len(session.exec(select(AuditLog).where(AuditLog.action == "silson24_receive")).all())
            == 1
        )
        claim = session.get(Claim, "GA-2610-0482")
        claim.assignee_id = 2
        session.add(claim)
        session.commit()
    assert client.post(url).status_code == 403


def test_no_fixture_and_admin_read_only(client):
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    assert client.post("/api/claims/GA-2610-0477/silson24").status_code == 404
    client.post("/api/auth/demo-login", json={"role": "admin"})
    assert client.post("/api/claims/GA-2610-0482/silson24").status_code == 403
