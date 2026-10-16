"""말투 재생성 횟수와 안전·메타데이터 보존을 실제 HTTP 없이 고정한다."""

import json

import pytest

from app.agent.graph import ChatAgent
from app.agent.tone import TONE_PROMPT, payment_assertion, violations
from app.schemas.chat import Action, ChatAnswer, Citation, ClaimRef
from app.scripts.tone_grade import grade_tone


@pytest.mark.parametrize(
    "text,pattern",
    [
        ("CV-04 확인 필요", "internal_term"),
        ("claim_check 처리", "internal_term"),
        ("서류 접수 → 검토", "arrow"),
        ("누락·불일치·확인", "middle_dot_list"),
        ("서류 추가 확인 필요.", "noun_ending"),
    ],
)
def test_prohibited_tone_patterns(text, pattern):
    assert pattern in violations(text)


def test_kcd_legal_addresses_and_sentences_are_not_internal_codes():
    text = "진단서의 C18.7을 확인해야 해요. 특별약관 제4조 ③항 2호에 해당하는지 살펴봐야 해요. 원본과 처방전을 확인해 주세요."
    assert not violations(text)
    assert "예시1" in TONE_PROMPT and "예시3" in TONE_PROMPT


def result(text):
    return ChatAnswer(
        answer=text,
        intent="policy_qa",
        citations=[
            Citation(
                doc_name="업무 매뉴얼",
                article="4장",
                source_path="data/kb/gaon/10_claims_manual.md",
                is_mock=True,
                quote="원문",
            )
        ],
        claim_refs=[ClaimRef(claim_id="GA-2610-0482", issue_id=1)],
        suggested_actions=[Action(label="보완 요청 작성", action="draft_supplement:GA-2610-0482")],
        refused=False,
    )


def test_single_retry_then_log_only_and_metadata_unchanged(caplog):
    class BadSolar:
        calls = 0

        def structured(self, *args):
            self.calls += 1
            return {"answer": "CV-04 확인 필요"}

    solar = BadSolar()
    agent = ChatAgent(None, solar, None)
    original = result("CV-04 확인 필요")
    final = agent.tone({"result": original})["result"]
    assert solar.calls == 2  # 최초 문장화1회와 금지 패턴 재생성1회, 추가 호출 없음.
    assert final.model_dump(exclude={"answer"}) == original.model_dump(exclude={"answer"})
    assert "chat_tone_remaining" in caplog.text
    assert "GA-2610" not in caplog.text and "CV-04" not in caplog.text


def test_initial_render_stops_without_retry_when_patterns_are_clear():
    class GoodSolar:
        calls = 0

        def structured(self, *args):
            self.calls += 1
            return {
                "answer": "추가 서류가 필요해요. 마지막 페이지가 빠져 있어요. 발급 기관에 요청해 주세요."
            }

    solar = GoodSolar()
    agent = ChatAgent(None, solar, None)
    answer = agent.tone({"result": result("추가 확인 필요")})["result"]
    assert solar.calls == 1 and not violations(answer.answer)


@pytest.mark.parametrize(
    "candidate",
    [
        "지급액은 100만원이에요.",
        "이번에 100만원을 받아요.",
        "확인이 필요해요. 원본을 봐야 해요. 담당자가 확인해 주세요.",
    ],
)
def test_payment_assertion_or_missing_number_cannot_replace_facts(candidate):
    class UnsafeSolar:
        def structured(self, *args):
            return {"answer": candidate}

    agent = ChatAgent(None, UnsafeSolar(), None)
    original = result("접수된 서류는 7장이고 필요한 서류는 8장이에요.")
    assert agent.tone({"result": original})["result"].answer == original.answer
    assert not payment_assertion("일반 약관 기준은 가입금액의 20%예요.")


def test_tone_judge_separate_from_gist_and_does_not_receive_gold():
    class Judge:
        def structured(self, messages, schema, name):
            assert name == "tone_grade"
            assert "answer_gist" not in json.loads(messages[-1]["content"])
            return {
                "score": 4,
                "naturalness": 4,
                "no_internal_terms": 5,
                "conclusion_first": 4,
                "reason": "자연스러워요.",
            }

    assert grade_tone(Judge(), "별도 예시", "답변")["score"] == 4


def test_natural_day_count_keeps_numeric_fact():
    from app.agent.tone import protected_numbers

    assert protected_numbers("1일 차이") == protected_numbers("하루 차이")


def test_tone_metric_does_not_change_existing_quality_scores():
    from app.scripts.eval_chat import aggregate, measure

    question = {"type": "refusal", "expected_sources": []}
    answer = {"intent": "refusal", "refused": True, "answer": "결정할 수 없어요.", "citations": []}
    metrics = measure(question, answer, [], {}, {"score": 1, "reason": "거절"})
    old = aggregate([{"metrics": metrics}])
    metrics.update(
        {
            "tone": {"score": 4, "naturalness": 4, "no_internal_terms": 5, "conclusion_first": 4},
            "tone_violations": [],
        }
    )
    new = aggregate([{"metrics": metrics}])
    assert new["tone_score_mean"] == 4 and new["tone_pattern_pass"] == 1
    assert new["gist_accuracy"] == old["gist_accuracy"] == 1
    assert new["refusal_accuracy"] == old["refusal_accuracy"] == 1
    assert new["citation_precision_micro"] == old["citation_precision_micro"]


def test_document_heading_dot_exception_is_scoped_and_business_terms_allowed():
    assert "middle_dot_list" not in violations(
        "① 진단서 · 조직검사 결과지: 날짜 확인\n원본을 확인해 주세요.", "claim_check"
    )
    assert "middle_dot_list" in violations(
        "① 지급 · 금액: 판단\n원본을 확인해 주세요.", "claim_check"
    )
    assert "middle_dot_list" in violations(
        "① 진단서 · 조직검사 결과지: 날짜 확인\n원본을 확인해 주세요.", "policy_qa"
    )
    assert "noun_ending" not in violations("이관")
    assert "internal_term" in violations("FIELD-diagnosis-code 확인")


def test_opt_in_solar_cache_prevents_second_request_and_records_cost(client, tmp_path):
    import httpx

    from app.agent.solar import Solar

    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "model": "solar-pro4",
                "usage": {"prompt_tokens": 10, "completion_tokens": 2},
                "choices": [{"finish_reason": "stop", "message": {"content": "{}"}}],
            },
        )

    config = client.app.state.settings.model_copy(
        update={
            "CACHE_PATH": tmp_path,
            "SOLAR_RESPONSE_CACHE": True,
            "SOLAR_USAGE_PATH": tmp_path / "usage.jsonl",
        }
    )
    solar = Solar(config, httpx.MockTransport(respond))
    assert solar.post(config.SOLAR_CHAT_PATH, {"model": "solar-pro4"}) == solar.post(
        config.SOLAR_CHAT_PATH, {"model": "solar-pro4"}
    )
    assert len(calls) == 1
    rows = [json.loads(line) for line in config.SOLAR_USAGE_PATH.read_text().splitlines()]
    assert [r["event"] for r in rows] == ["api_call", "cache_hit"]
    assert "Authorization" not in config.SOLAR_USAGE_PATH.read_text()
    assert config.__class__(SOLAR_USAGE_PATH="").SOLAR_USAGE_PATH is None
