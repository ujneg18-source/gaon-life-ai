"""상태 전이와 청구 맥락, 초안 경계를 실제 HTTP 없이 검증한다."""

from types import SimpleNamespace

import pytest
from sqlmodel import Session

from app.agent.tools import Tools
from app.models import ClaimStatus, User
from app.services.claim_status import claim_status
from tests.test_chat import FakeKB, setup_chat


@pytest.mark.parametrize(
    "missing,kind,status,actor,expected",
    [
        (True, "missing", "resolved", 1, "supplement"),
        (False, "mismatch", "open", None, "needs_review"),
        (False, "mismatch", "resolved", 1, "ready_review"),
        (False, "info", "open", None, "auto_pass"),
    ],
)
def test_status_transitions(missing, kind, status, actor, expected):
    issue = SimpleNamespace(kind=kind, status=status, resolved_by=actor)
    claim = SimpleNamespace(status=ClaimStatus.AUTO_PASS)
    assert claim_status(claim, [object()], [issue], [issue] if missing else []) == expected
    assert claim_status(claim, [], [issue], []) == ClaimStatus.PENDING


def test_resolving_all_keeps_missing(client):
    setup_chat(client)
    base = "/api/claims/GA-2610-0482"
    for issue in client.get(base).json()["issues"]:
        assert client.post(f"/api/issues/{issue['id']}/resolve").status_code == 200
    after = client.get(base).json()
    assert after["status"] == "supplement"
    assert any(i["kind"] == "missing" and i["status"] == "open" for i in after["issues"])
    row = next(c for c in client.get("/api/claims").json()["items"] if c["id"] == after["id"])
    assert row["status"] == after["status"]
    assert client.post(base + "/submit").status_code == 409


@pytest.mark.parametrize(
    "message,intent",
    [
        ("이 청구 건 서류 다 왔는지 검토해줘", "claim_check"),
        ("이 건 영수증에 보상 제외될 항목 있어?", "item_coverage"),
        ("누락 서류 보완 요청 문자 써줘", "draft"),
        ("이 건 지급 심사로 넘겨도 돼?", "claim_check"),
    ],
)
def test_context_questions(client, message, intent):
    setup_chat(client)
    response = client.post("/api/chat", json={"message": message, "claim_id": "GA-2610-0482"})
    assert response.status_code == 200 and response.json()["intent"] == intent
    assert {r["claim_id"] for r in response.json()["claim_refs"]} <= {"GA-2610-0482"}


def test_templates_and_comparisons(client):
    setup_chat(client)
    with Session(client.app.state.engine) as s:
        tool = Tools(s, s.get(User, 1), client.app.state.settings, FakeKB())
        result = tool.draft_supplement("GA-2610-0482", ["diagnosis"])
        assert result["draft_text"].startswith("[가온생명] 김유정 고객님") and result[
            "submitted"
        ] == ["진단서"]
        unsupported = tool.draft_supplement("GA-2610-0482", ["bankbook"])
        assert unsupported["draft_text"] is None and "템플릿" in unsupported["message"]
    result = client.get("/api/claims/GA-2610-0482").json()
    assert any(r["result"] == "match" for r in result["comparisons"])
    assert any(r["title"] == "입원일수" and r["result"] == "info" for r in result["comparisons"])
    assert result["development_origin"] is None
