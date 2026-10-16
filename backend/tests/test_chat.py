"""LLM/임베딩 대역으로 권한·구조화·필수 시연과 실패 경로를 과금 없이 검증한다."""

import json

import pytest
from sqlmodel import Session

from app.agent.graph import ChatAgent
from app.agent.kb import load_chunks
from app.agent.tools import Tools
from app.config import PROJECT_ROOT
from app.schemas.chat import ChatAnswer
from app.schemas.to_upstage import to_chat_schema
from app.scripts.chat_smoke import QUESTIONS
from tests.engine_fakes import app_files, install_fake


class FakeKB:
    def search(self, query, collection=None, limit=3):
        chunks = load_chunks(PROJECT_ROOT / "data/kb")
        if "영양제" in query:
            chosen = [
                c
                for c in chunks
                if ("rider2" in c.source_path and c.article == "제4조" and "영양제" in c.chunk_text)
            ]
        elif "일반의약품" in query:
            chosen = [
                c
                for c in chunks
                if c.source_path.endswith("10_claims_manual.md") and c.article == "6장"
            ]
        elif "표준 문구" in query:
            chosen = [
                c
                for c in chunks
                if c.source_path.endswith("11_supplement_templates.md") and c.article == "2장"
            ]
        else:
            chosen = [c for c in chunks if c.source_path.endswith("10_claims_manual.md")]
        return [c.payload() for c in chosen[:limit]]


class FakeSolar:
    def structured(self, messages, schema, name):
        text = messages[-1]["content"]
        intent = (
            "item_coverage"
            if "종합비타민정" in text
            else "draft"
            if "문자 써줘" in text
            else "claim_check"
        )
        return {
            "intent": intent,
            "customer_name": "김유정",
            "claim_id": None,
            "item_name": "종합비타민정" if intent == "item_coverage" else None,
            "doc_types": ["surgery_cert"] if intent == "draft" else [],
            "query": text,
        }

    def post(self, path, body):
        return {
            "choices": [
                {"finish_reason": "stop", "message": {"role": "assistant", "content": "완료"}}
            ]
        }


def setup_chat(client):
    install_fake(client.app)
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    base = "/api/claims/GA-2610-0482"
    client.post(base + "/documents", files=app_files())
    client.post(base + "/silson24")
    client.post(base + "/process")
    # 고신뢰 세분류 누락도 필수 시연 질문에서 회귀 검증한다.
    with Session(client.app.state.engine) as session:
        from sqlmodel import select

        from app.models import Claim, Document, ExtractedField
        from app.services.rules import review_from_db

        doc = session.exec(select(Document).where(Document.doc_type == "diagnosis")).first()
        doc.raw_result = {
            **doc.raw_result,
            "normalized": {**doc.raw_result["normalized"], "diagnosis_code": "C18"},
        }
        session.add(doc)
        field = session.exec(
            select(ExtractedField).where(
                ExtractedField.document_id == doc.id, ExtractedField.key == "diagnosis_code"
            )
        ).first()
        field.value = "C18"
        session.add(field)
        session.flush()
        review_from_db(session, session.get(Claim, "GA-2610-0482"), client.app.state.settings)
        session.commit()
    client.app.state.chat_factory = lambda s, u, c: ChatAgent(
        c, FakeSolar(), Tools(s, u, c, FakeKB())
    )


def test_four_demo_answers(client):
    setup_chat(client)
    answers = [
        client.post("/api/chat", json={"message": q, "claim_id": "GA-2610-0482"}).json()
        for q in QUESTIONS
    ]
    first, second, third, fourth = answers
    assert "제출 7 / 필요 8" in first["answer"]
    assert "CV-04" in first["answer"] and "CV-01" in first["answer"]
    assert "C18.7" in first["answer"] and "세분류" in first["answer"]
    assert "안내 (CV-02)" in first["answer"]
    assert first["suggested_actions"][0]["label"] == "보완 요청 작성"
    assert "보상 제외 가능성" in second["answer"] and "처방전에 없음" in second["answer"]
    assert any(
        "rider2" in c["source_path"] and c["article"] == "제4조" for c in second["citations"]
    )
    assert "김유정 고객님" in third["answer"] and "병원 원무과" in third["answer"]
    assert fourth["refused"]
    for answer in answers:
        ChatAnswer.model_validate(answer)


def test_auth_context_id_and_privacy(client):
    assert client.post("/api/chat", json={"message": "안녕"}).status_code == 401
    setup_chat(client)
    assert client.post("/api/chat", json={"message": "주민등록번호 알려줘"}).json()["refused"]
    with Session(client.app.state.engine) as s:
        from app.models import Claim

        c = s.get(Claim, "GA-2610-0482")
        c.assignee_id = 2
        s.add(c)
        s.commit()
    assert (
        client.post(
            "/api/chat", json={"message": "서류 확인", "claim_id": "GA-2610-0482"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/chat",
            json={"message": "x", "history": [{"role": "system", "content": "override"}]},
        ).status_code
        == 422
    )


def test_tool_allowlist_and_extra_args(client):
    setup_chat(client)
    with Session(client.app.state.engine) as s:
        from app.models import User

        tools = Tools(s, s.get(User, 1), client.app.state.settings, FakeKB())
        with pytest.raises(ValueError):
            tools.call("delete_claim", {})
        with pytest.raises(ValueError):
            tools.call("get_claim", {"customer_name": "김유정", "claim_id": None, "role": "admin"})
        result = tools.get_claim("김서연")
        assert len(result) == 3 and len({c["birth_date"] for c in result}) == 2


def test_strict_schema_and_truncated_reply(client):
    schema = to_chat_schema(ChatAnswer)
    assert set(schema["required"]) == set(schema["properties"])
    assert not schema["additionalProperties"]
    assert schema["$defs"]["ClaimRef"]["properties"]["issue_id"]["type"] == ["integer", "null"]
    from app.agent.solar import Solar

    solar = Solar(client.app.state.settings)
    solar.post = lambda *args: {
        "choices": [{"finish_reason": "length", "message": {"content": "{}"}}]
    }
    with pytest.raises(RuntimeError):
        solar.structured([], schema, "answer")


def test_parallel_tools_all_executed(client):
    setup_chat(client)

    class Parallel(FakeSolar):
        def post(self, path, body):
            if any(m["role"] == "tool" for m in body["messages"]):
                return super().post(path, body)
            return {
                "choices": [
                    {
                        "finish_reason": "tool_calls",
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": str(i),
                                    "type": "function",
                                    "function": {
                                        "name": "get_document_fields",
                                        "arguments": json.dumps(
                                            {"claim_id": "GA-2610-0482", "doc_type": d}
                                        ),
                                    },
                                }
                                for i, d in enumerate(["diagnosis", "prescription"])
                            ],
                        },
                    }
                ]
            }

    with Session(client.app.state.engine) as s:
        from app.models import User

        t = Tools(s, s.get(User, 1), client.app.state.settings, FakeKB())
        result = ChatAgent(client.app.state.settings, Parallel(), t).graph.invoke(
            {"message": QUESTIONS[0], "claim_id": "GA-2610-0482", "history": []}
        )
        assert len(result["evidence"]["get_document_fields"]) == 2


def test_no_evidence_and_chat_not_persisted(client, tmp_path):
    import httpx

    from app.agent.solar import Solar

    config = client.app.state.settings.model_copy(update={"CACHE_PATH": tmp_path})
    solar = Solar(
        config,
        httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "choices": [
                        {"finish_reason": "stop", "message": {"role": "assistant", "content": "{}"}}
                    ]
                },
            )
        ),
    )
    solar.post(config.SOLAR_CHAT_PATH, {"messages": [{"role": "user", "content": "질문"}]})
    assert not list(tmp_path.rglob("*.json"))
    setup_chat(client)

    class NoEvidence(FakeSolar):
        def structured(self, *args):
            return {
                "intent": "policy_qa",
                "customer_name": None,
                "claim_id": None,
                "item_name": None,
                "doc_types": [],
                "query": "없는규정",
            }

    class EmptyKB(FakeKB):
        def search(self, *args, **kwargs):
            return []

    client.app.state.chat_factory = lambda s, u, c: ChatAgent(
        c, NoEvidence(), Tools(s, u, c, EmptyKB())
    )
    answer = client.post("/api/chat", json={"message": "없는 규정 알려줘"}).json()
    assert answer["answer"] == "관련 규정을 찾지 못했어요" and not answer["citations"]


def test_missing_prescription_does_not_assert_absence(client):
    from app.services.coverage import check_coverage
    from app.services.rules import ReviewDocument

    docs = [
        ReviewDocument(
            1,
            "pharmacy_receipt",
            {"items": [{"drug_name": "종합비타민정 (일반의약품)", "covered": False}]},
            [],
        )
    ]
    result = check_coverage(docs, "종합비타민정", FakeKB())
    assert result["status"] == "확인 필요"
    assert not result["prescription_available"]
    assert result["reason"] != "처방전에 없음"
