"""부분 코드와 행별 급여 판단의 회귀 검증."""

from app.services.normalize import normalize_document


def test_longer_code_forces_review_even_if_high():
    values = {
        "patient_name": "가상",
        "diagnosis_code": "C18",
        "diagnosis_name": "가상",
        "diagnosis_date": "2026-09-18",
    }
    parsed = {"elements": [{"content": {"html": "가상 C18.7 2026.09.18"}}]}
    result = normalize_document(
        "diagnosis", values, {"diagnosis_code": {"confidence": "high"}}, parsed, 1
    )
    code = next(f for f in result.fields if f.key == "diagnosis_code")
    assert not code.source_found and "원문과 다름(세분류 누락)" in code.review_reasons


def test_pharmacy_covered_from_same_row_not_whole_document():
    values = {
        "patient_name": "가상",
        "items": [
            {"drug_name": "약A", "covered": False, "amount": 10},
            {"drug_name": "약B", "covered": True, "amount": 20},
        ],
    }
    parsed = {
        "elements": [
            {
                "id": 1,
                "page": 1,
                "content": {
                    "html": "<table><tr><td>품명</td><td>구분</td></tr><tr><td>약A</td><td>급여</td></tr><tr><td>약B</td><td>비급여</td></tr></table>"
                },
            }
        ]
    }
    extras = {"items": [{"covered": {"confidence": "low"}}, {"covered": {"confidence": "low"}}]}
    result = normalize_document("pharmacy_receipt", values, extras, parsed, 1)
    assert [x["covered"] for x in result.values["items"]] == [True, False]
    covered = [f for f in result.fields if f.key.endswith(".covered")]
    assert all(f.source_found and f.extract_conf is None and not f.review_reasons for f in covered)
    assert len(result.evidence) == 2
