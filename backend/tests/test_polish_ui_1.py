"""빈 접수와 서류 접수 후 검사, 기존 DB 보정의 보존성을 확인한다."""

from sqlmodel import Session, select

from app.models import Claim, ClaimStatus, Customer, Issue, IssueKind
from scripts.polish_ui_1 import apply_polish
from tests.test_review_api import prepare


def test_empty_claim_skips_engine_and_resolves_old_automatic_issues(client, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("빈 접수는 검토 엔진을 실행하면 안 됩니다.")

    monkeypatch.setattr("app.services.rules.evaluate_claim", forbidden)
    monkeypatch.setattr("app.services.workspace.evaluate_claim", forbidden)
    with Session(client.app.state.engine) as s:
        claim = s.get(Claim, "GA-2610-0482")
        claim.status = ClaimStatus.SUPPLEMENT
        s.add(claim)
        s.add(
            Issue(
                claim_id=claim.id,
                kind=IssueKind.MISSING,
                rule_id="REQ-old",
                title="이전 자동 이슈",
                detail="",
            )
        )
        s.commit()
    apply_polish(client.app.state.engine, client.app.state.settings)
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    data = client.get("/api/claims?status=pending").json()
    assert data["counts"]["pending"] == 13 and data["counts"]["supplement"] == 0
    assert len(data["items"]) == 13
    assert not any(
        i["status"] == "open" for i in client.get("/api/claims/GA-2610-0482/issues").json()
    )
    assert client.post("/api/claims/GA-2610-0482/process").status_code == 422


def test_polish_preserves_kim_and_removes_seed_patterns(client):
    base, before = prepare(client)
    before_issues = {
        (i["rule_id"], i["kind"], tuple(i["doc_ids"]))
        for i in before["issues"]
        if i["status"] == "open"
    }
    apply_polish(client.app.state.engine, client.app.state.settings)
    after = client.get(base).json()
    assert after["submitted_count"] == 7 and after["required_count"] == 8
    assert before_issues == {
        (i["rule_id"], i["kind"], tuple(i["doc_ids"]))
        for i in after["issues"]
        if i["status"] == "open"
    }
    assert client.get("/api/claims").json()["counts"]["pending"] == 12
    assert not any("시연용" in i["detail"] or "참조어 기준" in i["detail"] for i in after["issues"])
    with Session(client.app.state.engine) as s:
        birthdays = [c.birth_date for c in s.exec(select(Customer)).all()]
        times = [c.received_at for c in s.exec(select(Claim)).all()]
        assert len(set(birthdays)) == 10 and len(set(times)) == 13
