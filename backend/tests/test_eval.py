"""평가 수치가 높은 쪽으로 왜곡되지 않도록 0분모·부분 정답·누락 인용을 고정한다."""

from app.scripts.eval_chat import aggregate, measure, prohibited, source_pair
from app.scripts.eval_extract import confusion


def test_retrieval_partial_and_wrong_citation_are_not_full_credit():
    q = {
        "type": "policy_qa",
        "expected_sources": [{"doc": "a", "article": "제1조"}, {"doc": "b", "article": "제2조"}],
    }
    a = {
        "intent": "policy_qa",
        "refused": False,
        "answer": "기준을 확인해요.",
        "citations": [{"doc_name": "A", "article": "제1조"}, {"doc_name": "C", "article": "제3조"}],
    }
    m = measure(
        q,
        a,
        [{"doc_name": "A", "article": "제1조"}],
        {"a": "A", "b": "B"},
        {"score": 1, "reason": "테스트"},
    )
    assert m["recall_at_3"] == 0.5
    assert m["citation_correct"] == 1 and m["citation_total"] == 2
    assert not m["citation_pass"]
    summary = aggregate([{"metrics": m}])
    assert summary["recall_at_3_macro"] == 0.5
    assert summary["citation_precision_micro"] == 0.5


def test_no_sources_is_na_and_missing_citation_is_failure():
    a = {"intent": "refusal", "refused": True, "answer": "범위 밖이에요.", "citations": []}
    m = measure(
        {"type": "refusal", "expected_sources": []}, a, [], {}, {"score": 1, "reason": "테스트"}
    )
    assert m["recall_at_3"] is None and m["citation_pass"]
    assert aggregate([{"metrics": m}])["citation_precision_micro"] is None
    m = measure(
        {"type": "policy_qa", "expected_sources": [{"doc": "a", "article": "제1조"}]},
        a,
        [],
        {},
        {"score": 0, "reason": "테스트"},
    )
    assert not m["citation_pass"] and not m["intent_correct"] and not m["refusal_correct"]
    assert source_pair({"source_path": "data/kb/a", "article": "제1조"}, {"a": "A"}) == (
        "A",
        "제1조",
    )


def test_prohibited_payment_and_general_limit_are_distinct():
    assert prohibited("보험금이 지급됩니다.")
    assert prohibited("지급 가능합니다.")
    assert prohibited("지급액은 500만원이에요.")
    assert not prohibited("약관 기준은 50%, 1일 10만원 한도이며 지급 심사 담당자가 결정합니다.")


def test_extract_confusion_counts_wrong_values_not_business_issues():
    rows = [
        {"wrong": True, "flagged": True},
        {"wrong": True, "flagged": False},
        {"wrong": False, "flagged": True},
        {"wrong": False, "flagged": False},
    ]
    m = confusion(rows)
    assert [m[k] for k in ["tp", "fp", "fn", "tn"]] == [1, 1, 1, 1]
    assert m["precision"] == m["recall"] == m["accuracy"] == 0.5
    m = confusion([{"wrong": False, "flagged": False}])
    assert m["precision"] is None and m["recall"] is None


def test_distinct_articles_and_acceptable_do_not_relax_strict_score():
    q = {
        "type": "policy_qa",
        "expected_sources": [{"doc": "a", "article": "제1조"}, {"doc": "a", "article": "제2조"}],
        "acceptable_sources": [
            {"doc": "a", "article": "제1조"},
            {"doc": "a", "article": "제2조"},
            {"doc": "b", "article": "제7조"},
        ],
    }
    hits = [{"doc_name": "A", "article": a} for a in ["제1조 ①", "제1조 ②", "제1조 ③", "제2조"]]
    answer = {
        "intent": "policy_qa",
        "refused": False,
        "answer": "기준 안내",
        "citations": [{"doc_name": "B", "article": "제7조"}],
    }
    m = measure(q, answer, hits, {"a": "A", "b": "B"}, {"score": 1, "reason": "test"})
    assert m["recall_at_3"] == 0.5 and m["recall_article_at_3"] == 1
    assert m["citation_correct"] == 0 and m["citation_correct_acceptable"] == 1
