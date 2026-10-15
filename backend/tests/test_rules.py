"""정답 파일은 테스트 입력에만 쓴다. 엔진은 기대 이슈를 읽지 않는다."""

import json
from collections import Counter

from sqlmodel import Session, select

from app.config import PROJECT_ROOT
from app.models import (
    Claim,
    ClaimStatus,
    Confidence,
    CrossCheckRule,
    DocumentStatus,
    RequiredDocRule,
    ReviewSettings,
)
from app.services.normalize import normalize_document
from app.services.rules import ReviewDocument, evaluate_claim


def inputs():
    docs = []
    for i, path in enumerate(
        sorted((PROJECT_ROOT / "data/samples/kim_yujeong/answers").glob("0*.json")), 1
    ):
        data = json.loads(path.read_text())
        result = normalize_document(data["doc_type"], data, {}, {}, i, is_data=True)
        docs.append(ReviewDocument(i, data["doc_type"], result.values, result.fields))
    return docs


def evaluate(client, docs, **kwargs):
    with Session(client.app.state.engine) as s:
        claim = s.get(Claim, "GA-2610-0482")
        return evaluate_claim(
            claim,
            docs,
            list(s.exec(select(RequiredDocRule)).all()),
            list(s.exec(select(CrossCheckRule)).all()),
            s.get(ReviewSettings, 1),
            client.app.state.settings,
            **kwargs,
        )


def test_answers_match_expected_issues_without_api(client):
    docs = inputs()
    report = evaluate(client, docs)
    expected = json.loads(
        (PROJECT_ROOT / "data/samples/kim_yujeong/answers/_claim.json").read_text()
    )
    expected = {
        (i["kind"], i["rule"])
        for i in expected["expected_issues"]
        if i["kind"] in {"missing", "mismatch"}
    }
    assert {(i.kind.value, i.rule_id) for i in report.issues} == expected
    assert Counter(i.kind.value for i in report.issues) == {"missing": 1, "mismatch": 2}
    assert len(report.required) == 8 and report.status == ClaimStatus.SUPPLEMENT
    assert (
        "cross_check" in next(f for f in docs[0].fields if f.key == "diagnosis_date").review_reasons
    )
    code = next(f for f in docs[0].fields if f.key == "diagnosis_code")
    code.extract_conf = Confidence.LOW
    code.review_reasons = ["low_conf"]
    report = evaluate(client, docs)
    assert Counter(i.kind.value for i in report.issues) == {
        "missing": 1,
        "mismatch": 2,
        "low_conf": 1,
    }


def test_cv03_cv05_and_failed_document(client):
    docs = inputs()
    docs[1].values["pathology_result"] = "Benign tissue"
    docs[2].values["patient_name"] = "다른 가상 고객"
    docs[6].status = DocumentStatus.FAILED
    report = evaluate(client, docs)
    assert {"CV-03", "CV-05", "PIPELINE"} <= {i.rule_id for i in report.issues}


def test_normal_auto_pass_and_format_still_routes_with_switches_off(client):
    docs = inputs()
    docs[0].values["diagnosis_date"] = "2026-09-21"
    docs[2].values["stay_days"] = 8
    docs[4].values["items"] = [{"category": "exam", "name": "검사", "amount": 100}]
    report = evaluate(client, docs)
    assert not report.issues and report.status == ClaimStatus.AUTO_PASS
    field = docs[0].fields[0]
    field.review_reasons = ["format", "low_conf", "not_in_source"]
    with Session(client.app.state.engine) as s:
        settings = s.get(ReviewSettings, 1)
        settings.review_on_low_conf = False
        settings.review_on_not_in_source = False
        s.add(settings)
        s.commit()
    report = evaluate(client, docs)
    assert len(report.issues) == 1 and report.issues[0].kind.value == "format"
    assert report.status == ClaimStatus.NEEDS_REVIEW
