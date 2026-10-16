"""가드 선실행·번역 추가·유한 재시도를 과금 없이 회귀 검증한다."""

import pytest

from app.agent.graph import ChatAgent
from app.agent.guardrails import refusal_reason
from app.agent.tools import Tools
from app.services.normalize import normalize_document


@pytest.mark.parametrize(
    "message",
    [
        "이거 지급해도 돼?",
        "김유정 고객 지급해도 돼?",
        "지급액 계산해줘",
        "보험금 얼마 받아?",
        "보험사기 같아?",
        "주민등록번호 알려줘",
    ],
)
def test_guard_before_llm(message):
    class NoLLM:
        def structured(self, *args):
            raise AssertionError("금지 요청에 LLM 호출")

    result = ChatAgent(None, NoLLM(), None).classify({"message": message})
    assert result["route"].intent == "refusal"


@pytest.mark.parametrize(
    "message",
    [
        "보험금은 며칠 안에 지급돼?",
        "갑상선암도 암 진단금 100% 나와?",
        "실손 영양제 보상돼?",
        "계약 두 달 후 암 진단은?",
    ],
)
def test_general_policy_questions_allowed(message):
    assert refusal_reason(message) is None


def test_added_translation_is_flagged_but_source_translation_is_not():
    source = "Adenocarcinoma, moderately differentiated"

    def field(text):
        result = normalize_document(
            "pathology",
            {"patient_name": "가상고객", "pathology_result": source + " (중등도 분화 선암)"},
            {},
            {"elements": [{"content": {"text": text}}]},
            1,
        )
        return next(f for f in result.fields if f.key == "pathology_result")

    assert "원문과 다름(번역·보정 의심)" in field(source).review_reasons
    assert not field(source).source_found
    assert "원문과 다름(번역·보정 의심)" not in field(source + " (중등도 분화 선암)").review_reasons


def test_tools_only_retry_once_and_log_without_arguments(caplog):
    t = Tools(None, None, None, None)
    seen = []

    def fail(name, args):
        seen.append(1)
        raise ValueError("private detail")

    t.call = fail
    with pytest.raises(RuntimeError, match="확인하지 못했어요"):
        t.call_with_retry("get_claim", {})
    assert len(seen) == 2 and "private detail" not in caplog.text
    assert "attempt=1" in caplog.text and "attempt=2" in caplog.text


def test_model_cannot_refuse_explicit_allowed_document_read(client):
    from app.schemas.chat import Route

    class WrongRefusal:
        def structured(self, *args):
            return Route(
                intent="refusal",
                customer_name=None,
                claim_id=None,
                item_name=None,
                doc_types=[],
                query="서류 조회",
            ).model_dump()

    a = ChatAgent(client.app.state.settings, WrongRefusal(), None)
    assert (
        a.classify({"message": "김유정 고객 진단일이랑 병리 보고일 왜 문제야?"})["route"].intent
        == "claim_check"
    )
    assert a.classify({"message": "김유정 고객 지급해도 돼?"})["route"].intent == "refusal"
