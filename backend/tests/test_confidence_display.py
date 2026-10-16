"""원본 Extract JSON 문자열 점수를 항목별 읽기 모델로 연결한다."""

import json

from sqlmodel import Session

from app.models import Document
from app.services.workspace import field_confidences
from tests.test_review_api import prepare


def test_field_scores_parse_string_and_array_without_context_or_classify_score():
    raw = {
        "extract": {
            "choices": [
                {
                    "confidence_score": json.dumps(
                        {
                            "patient_name": {"_value": 0.998, "_ctx": 0.4},
                            "items": [{"amount": {"_value": 0.72, "_ctx": 0.3}}],
                            "invalid": {"_value": True},
                            "outside": {"_value": 2},
                        }
                    )
                }
            ]
        },
        "classify": {"confidence_score": 0.99},
    }
    assert field_confidences(raw) == {"patient_name": 0.998, "items[0].amount": 0.72}
    assert field_confidences({"extract": {"choices": [{"confidence_score": "broken"}]}}) == {}
    assert field_confidences({"classify": {"confidence_score": 0.99}}) == {}


def test_claim_fields_expose_actual_extraction_score_only(client):
    base, data = prepare(client)
    doc = next(row for row in data["documents"] if row["doc_type"] == "diagnosis")
    with Session(client.app.state.engine) as session:
        stored = session.get(Document, doc["id"])
        raw = dict(stored.raw_result)
        raw["extract"] = {
            "choices": [{"confidence_score": '{"patient_name":{"_value":0.998,"_ctx":0.8}}'}]
        }
        stored.raw_result = raw
        session.add(stored)
        session.commit()
    fields = client.get(base).json()["fields"]
    field = next(f for f in fields if f["document_id"] == doc["id"] and f["key"] == "patient_name")
    assert field["confidence_score"] == 0.998
    assert all(f["confidence_score"] is None for f in fields if f["method"] == "data")
