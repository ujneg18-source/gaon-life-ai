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
        ("김유정 고객님 관련해서 해야 하는 업무 리스트 좀 뽑아줘", "claim_check"),
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


def test_workload_and_development_visibility(client):
    from app.models import Claim

    setup_chat(client)
    with Session(client.app.state.engine) as s:
        tool = Tools(s, s.get(User, 1), client.app.state.settings, FakeKB())
        assert tool.get_workload()["supplement"] == 1
        claim = s.get(Claim, "GA-2610-0482")
        claim.assignee_id = 2
        s.add(claim)
        s.commit()
        assert tool.get_workload()["total"] == 0
    client.post("/api/auth/demo-login", json={"role": "admin"})
    config = client.app.state.settings
    config.SHOW_DEV_BADGE = True
    config.DEMO_MODE = True
    assert client.get("/api/claims/GA-2610-0482").json()["development_origin"] is None
    config.DEMO_MODE = False
    assert client.get("/api/claims/GA-2610-0482").json()["development_origin"]
    counts = client.get("/api/claims").json()["counts"]
    assert sum(v for k, v in counts.items() if k != "total") == counts["total"]


def test_submitted_draft_is_customer_text_only(client):
    setup_chat(client)
    data = client.post(
        "/api/chat", json={"message": "진단서 보완 요청 문자 써줘", "claim_id": "GA-2610-0482"}
    ).json()
    assert "진단서를 이미 제출했어요" in data["answer"]
    assert "필요하시다면" not in data["answer"]
    assert data["draft_text"].startswith("[가온생명] 김유정 고객님")
    assert "이미 제출" not in data["draft_text"]


def test_disabled_patient_comparison_not_displayed(client):
    from app.models import CrossCheckRule

    setup_chat(client)
    with Session(client.app.state.engine) as s:
        rule = s.get(CrossCheckRule, "CV-05")
        rule.enabled = False
        s.add(rule)
        s.commit()
    data = client.get("/api/claims/GA-2610-0482").json()
    assert not any(r["title"] == "환자명" for r in data["comparisons"])
    merged = next(i for i in data["display_issues"] if i["rule_id"] == "FIELD-diagnosis_code")
    assert merged["related_ids"]


def test_unknown_named_document_does_not_request_missing_instead(client):
    setup_chat(client)
    data = client.post(
        "/api/chat",
        json={"message": "장기요양확인서 보완 요청 문자 써줘", "claim_id": "GA-2610-0482"},
    ).json()
    assert data["draft_text"] is None and "템플릿" in data["answer"]


def test_unknown_context_question_still_uses_model_scope_decision(client):
    from app.agent.graph import ChatAgent
    from tests.test_chat import FakeSolar

    class RefusingSolar(FakeSolar):
        called = False

        def structured(self, messages, schema, name):
            self.called = True
            return {
                "intent": "refusal",
                "customer_name": None,
                "claim_id": None,
                "item_name": None,
                "doc_types": [],
                "query": "범위 밖 질문",
            }

    setup_chat(client)
    with Session(client.app.state.engine) as s:
        solar = RefusingSolar()
        agent = ChatAgent(
            client.app.state.settings,
            solar,
            Tools(s, s.get(User, 1), client.app.state.settings, FakeKB()),
        )
        result = agent.classify(
            {"message": "이 건 내일 운세를 알려줘", "claim_id": "GA-2610-0482", "history": []}
        )
        assert solar.called and result["route"].intent == "refusal"


def test_processing_is_preserved_only_while_documents_are_unprocessed():
    claim = SimpleNamespace(status=ClaimStatus.PROCESSING)
    assert (
        claim_status(claim, [SimpleNamespace(status="processing")], [], [object()])
        == ClaimStatus.PROCESSING
    )
    assert (
        claim_status(claim, [SimpleNamespace(status="extracted")], [], [object()])
        == ClaimStatus.SUPPLEMENT
    )


def test_search_customer_name_id_and_claim_number(client):
    """안내된 세 검색 기준이 실제 데이터와 연결되며 계약번호를 오인하지 않는다."""
    setup_chat(client)
    claim = client.get("/api/claims/GA-2610-0482").json()
    for query in [claim["customer_name"], claim["customer"]["id"].lower(), claim["id"]]:
        response = client.get("/api/claims", params={"q": query})
        assert response.status_code == 200
        assert claim["id"] in {row["id"] for row in response.json()["items"]}
    assert client.get("/api/claims", params={"q": claim["policy_no"]}).json()["items"] == []
