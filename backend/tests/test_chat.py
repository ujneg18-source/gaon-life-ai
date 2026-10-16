"""LLM/임베딩 대역으로 권한·구조화·필수 시연과 실패 경로를 과금 없이 검증한다."""

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
    def lookup(self, source, article, keyword=None):
        return [
            c.payload()
            for c in load_chunks(PROJECT_ROOT / "data/kb")
            if c.source_path.endswith(source)
            and c.article == article
            and (keyword is None or keyword in c.chunk_text)
        ]

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
        if name == "tone_answer":
            import json
            import re

            # 업무 사실은 그대로 두고 내부 코드만 제거하는 말투 모델 대역이다.
            answer = json.loads(text)["fact_answer"]
            answer = re.sub(r"\s*\(CV-0\d\)", "", answer)
            return {"answer": answer.replace(" · ", ", ")}
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
    assert "서류 7건을 제출했고, 추가로 받아야 할 서류가 1건" in first["answer"]
    assert "수술확인서" in first["answer"] and "진단일" in first["answer"]
    assert "CV-" not in first["answer"]
    assert "C18.7" in first["answer"] and "세분류" in first["answer"]
    assert "1일 차이" in first["answer"]
    assert first["suggested_actions"][0]["label"] == "보완 요청 작성"
    assert (
        "보상에서 제외될 가능성" in second["answer"]
        and "처방전에는 해당 약품이 없어요" in second["answer"]
    )
    assert any(
        "rider2" in c["source_path"] and c["article"].startswith("제4조")
        for c in second["citations"]
    )
    assert "김유정 고객님" in third["answer"] and "병원 원무과" in third["answer"]
    assert fourth["refused"]
    for answer in answers:
        ChatAnswer.model_validate(answer)


def test_demo_display_sources_and_refusal(client):
    """평가 원본을 보존하면서 화면 근거/링크가 본문에만 대응하는지 확인한다."""
    setup_chat(client)
    answers = [
        client.post("/api/chat", json={"message": q, "claim_id": "GA-2610-0482"}).json()
        for q in QUESTIONS
    ]
    first, second, third, fourth = answers
    assert [c["article"] for c in first["display_citations"]] == ["제3조 ③", "제4조 ③ 2호", "제5조"]
    assert all("10_claims" not in c["source_path"] for c in first["display_citations"])
    assert all(r["label"] and "이슈 " not in r["label"] for r in first["display_claim_refs"])
    assert "관련 서류 원문" not in first["answer"]
    assert "(일반의약품)" not in first["answer"]
    assert len(second["display_citations"]) == 1
    assert [r["label"] for r in second["display_claim_refs"]] == ["종합비타민정 보상 여부"]
    assert third["answer"].startswith("[가온생명] 김유정 고객님")
    assert third["display_citations"][0]["article"] == "2장"
    assert fourth["answer"].startswith(
        "지급 여부와 금액은 제가 판단할 수 없어요. 지급 심사 담당자가 결정하는 부분이에요."
    )
    assert "- 보완 요청: 수술확인서" in fourth["answer"]
    assert "- 확인 필요: 질병분류기호 세분류, 진단일과 병리 보고일" in fourth["answer"]
    assert "- 보상 제외 가능성: 종합비타민정" in fourth["answer"]
    assert fourth["answer"].endswith("이 항목들이 정리되면 지급 심사로 이관하시면 돼요.")
    assert fourth["display_citations"][0]["article"] == "10장"
    for answer in answers:
        assert "③항" not in answer["answer"]
        assert "CV-" not in "".join(c["display_quote"] for c in answer["display_citations"])


def test_source_table_is_display_only():
    from app.agent.display import readable_quote
    from app.config import Settings

    original = "| 규칙 | 확인 사항 |\n| --- | --- |\n| CV-01 | 날짜 비교 |"
    shown = readable_quote(original, Settings())
    assert "규칙: 진단일과 병리 보고일 비교" in shown
    assert "확인 사항: 날짜 비교" in shown
    assert "|" not in shown and "CV-01" in original


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


def test_intent_dispatch_reads_only_resolved_claim(client):
    setup_chat(client)
    with Session(client.app.state.engine) as s:
        from app.models import User

        tools = Tools(s, s.get(User, 1), client.app.state.settings, FakeKB())
        seen = []
        original = tools.call

        def record(name, args):
            seen.append((name, args))
            return original(name, args)

        tools.call = record
        ChatAgent(client.app.state.settings, FakeSolar(), tools).run(QUESTIONS[0], "GA-2610-0482")
        assert {n for n, _ in seen} >= {"get_claim", "get_claim_issues"}
        assert all(a.get("claim_id") in {None, "GA-2610-0482"} for _, a in seen)


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


def test_general_rules_do_not_require_customer_or_invent_claim_id(client):
    from app.schemas.chat import Route

    class GeneralSolar(FakeSolar):
        def structured(self, messages, schema, name):
            return Route(
                intent="claim_check",
                customer_name=None,
                claim_id="GA-INVENTED",
                item_name=None,
                doc_types=[],
                query="일반 필수서류 기준",
            ).model_dump()

    with Session(client.app.state.engine) as session:
        from app.models import User

        agent = ChatAgent(
            client.app.state.settings,
            GeneralSolar(),
            Tools(session, session.get(User, 1), client.app.state.settings, FakeKB()),
        )
        route = agent.classify({"message": "진료 서류 제출 기준을 알려줘", "history": []})["route"]
        assert route.intent == "policy_qa" and route.claim_id is None


def test_policy_ratios_and_whitespace_citations_but_no_payment_commitment():
    from app.schemas.chat import Route

    hit = {
        "doc_name": "가상 약관",
        "article": "제4조",
        "source_path": "data/kb/gaon/example.md",
        "is_mock": True,
        "chunk_text": "일반 약관 기준\n가입금액의 20%를 기준으로 검토한다.",
    }

    class PolicySolar:
        text = "가상 약관의 일반 기준은 20%예요. 개별 지급은 담당자가 결정해요."

        def structured(self, *args):
            from app.agent.rag import chunk_id

            return {
                "answer": self.text,
                "used_chunk_ids": [chunk_id(hit)],
                "quotes": [{"chunk_id": chunk_id(hit), "quote": self.quote}],
            }

        quote = hit["chunk_text"]

    solar = PolicySolar()
    agent = ChatAgent(None, solar, None)
    state = {
        "message": "일반 약관 기준",
        "route": Route(
            intent="policy_qa",
            customer_name=None,
            claim_id=None,
            item_name=None,
            doc_types=[],
            query="기준",
        ),
        "evidence": {"hits": [hit]},
    }
    answer = agent.answer(state)["result"]
    assert "20%" in answer.answer and answer.citations[0].quote == hit["chunk_text"]
    solar.quote = "일반 약관 기준 가입금액의 20%를 기준으로 검토한다."
    assert not agent.answer(state)["result"].citations  # 개행도 원문과 다른 인용은 버린다.
    solar.quote = hit["chunk_text"]
    solar.text = "보험금 20만원이 지급됩니다."
    assert agent.answer(state)["result"].answer == "관련 규정을 찾지 못했어요"


def test_workload_counts_only_assigned_claims(client):
    from app.models import Claim, ClaimStatus, User

    with Session(client.app.state.engine) as session:
        a = session.get(Claim, "GA-2610-0482")
        a.status = ClaimStatus.NEEDS_REVIEW
        b = session.get(Claim, "GA-2610-0477")
        b.status = ClaimStatus.SUPPLEMENT
        c = session.get(Claim, "GA-2610-0471")
        c.status = ClaimStatus.NEEDS_REVIEW
        c.assignee_id = 2
        session.add_all([a, b, c])
        session.commit()
        tool = Tools(session, session.get(User, 1), client.app.state.settings, FakeKB())
        assert tool.get_workload() == {"needs_review": 1, "supplement": 1, "total": 2}


def test_claim_check_never_calls_general_search(client):
    setup_chat(client)

    class NoGeneralSearch(FakeKB):
        def search(self, *args, **kwargs):
            raise AssertionError("청구 조회에 일반 검색 금지")

    with Session(client.app.state.engine) as s:
        from app.models import User

        agent = ChatAgent(
            client.app.state.settings,
            FakeSolar(),
            Tools(s, s.get(User, 1), client.app.state.settings, NoGeneralSearch()),
        )
        answer = agent.run(QUESTIONS[0], "GA-2610-0482")
        assert "서류 7건을 제출했고, 추가로 받아야 할 서류가 1건" in answer.answer
        assert {c.article for c in answer.citations} == {"2장", "4장"}
        focused = agent.run("김유정 고객 진단서 질병코드 뭐로 읽혔어?", "GA-2610-0482")
        assert all(c.article == "5장" for c in focused.citations)


def test_claim_layout_merges_code_causes_and_preserves_info(client):
    from app.agent.tone import violations

    setup_chat(client)
    answer = client.post(
        "/api/chat", json={"message": QUESTIONS[0], "claim_id": "GA-2610-0482"}
    ).json()
    body = answer["answer"]
    assert body.startswith("김유정(GA-2610-0482) 고객님")
    assert body.count("GA-2610-0482") == 1
    assert body.count("질병분류기호 확인") == 1
    assert "보완 요청이 필요합니다." in body and "불일치로 보지 않았습니다." in body
    assert "\n\n① " in body and "\n\n④ " in body
    assert not violations(body, "claim_check")
    assert body.index("질병분류기호 확인") < body.index("보상 여부") < body.index("입원일수 차이")


def test_empty_and_complete_claim_do_not_invent_missing_documents(client):
    from app.agent.claim_answer import render_claim

    config = client.app.state.settings
    claim = {"customer_name": "가상고객", "claim_id": "GA-2610-9999", "submitted_count": 2}
    complete = render_claim(claim, [], [], config)
    assert "추가로 받을 서류는 없습니다." in complete and "추가 서류:" not in complete
    claim["submitted_count"] = 0
    empty = render_claim(claim, [], [], config)
    assert "아직 서류를 제출하지 않았습니다" in empty
    assert "추가로 받을 서류는 없습니다" not in empty


def test_refusal_without_context_has_followup_button_and_one_manual_source(client):
    setup_chat(client)
    from app.agent.kb import load_chunks

    class LookupKB(FakeKB):
        def lookup(self, path, article, term=""):
            return [
                c.payload()
                for c in load_chunks(PROJECT_ROOT / "data/kb")
                if c.source_path.endswith(path) and c.article == article and term in c.chunk_text
            ]

    client.app.state.chat_factory = lambda s, u, c: ChatAgent(
        c, FakeSolar(), Tools(s, u, c, LookupKB())
    )
    answer = client.post("/api/chat", json={"message": "지급해도 돼?"}).json()
    assert answer["refused"] and len(answer["citations"]) == 1
    assert answer["citations"][0]["article"] == "10장"
    assert answer["suggested_actions"][0]["label"] == "남은 확인 항목 보기"
    privacy = client.post("/api/chat", json={"message": "주민등록번호 알려줘"}).json()
    assert privacy["refused"] and privacy["citations"][0]["article"] == "9장"


@pytest.mark.parametrize("original", ["제4조 ③항 2호", "제4조 제3항 제2호", "제4조 ③ 제2호"])
def test_article_display_address(original):
    from app.agent.display import address

    assert address(original) == "제4조 ③ 2호"


def test_display_never_mixes_coverage_sections():
    from types import SimpleNamespace

    from app.agent.display import present
    from app.config import Settings
    from app.services.coverage import citation

    config = Settings()
    chunk = next(
        c
        for c in load_chunks(config.KB_PATH)
        if "rider2_" in c.source_path
        and c.coverage_section == "상해비급여"
        and c.article == "제4조"
    )
    raw = ChatAnswer(
        answer=f"해당 사항을 확인해 주세요. (특별약관2 상해 비급여 {chunk.address})",
        intent="policy_qa",
        citations=[citation(chunk.payload())],
        claim_refs=[],
        suggested_actions=[],
        refused=False,
    )
    result = present(SimpleNamespace(config=config), {"result": raw})["result"]
    assert result.display_citations
    assert all(c.coverage_section == "상해비급여" for c in result.display_citations)
    assert raw.display_citations is None
