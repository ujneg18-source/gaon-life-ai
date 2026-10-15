"""정규화·근거 좌표·형식 검증을 API 없이 검사한다."""

import json

from sqlmodel import Session

from app.config import PROJECT_ROOT
from app.schemas.documents import DOCUMENT_SCHEMAS
from app.schemas.to_upstage import to_extract_schema
from app.services.normalize import completion_values, normal_scalar, normalize_document

BOX = [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.1}, {"x": 0.2, "y": 0.2}, {"x": 0.1, "y": 0.2}]


def test_extract_schemas_have_no_refs_nested_arrays_or_nullable():
    def check(node, array=False):
        assert "$ref" not in node and "anyOf" not in node and "format" not in node
        if node.get("type") == "array":
            assert not array
            check(node["items"], True)
        for v in node.get("properties", {}).values():
            check(v, array)

    for model in DOCUMENT_SCHEMAS.values():
        schema = to_extract_schema(model)
        assert all(
            p["type"] in {"string", "integer", "number", "array"}
            for p in schema["properties"].values()
        )
        check(schema)
        assert len(json.dumps(schema)) < 15000


def test_normalize_code_date_money_and_format(client):
    values = json.loads(
        (PROJECT_ROOT / "data/samples/kim_yujeong/answers/01_diagnosis.json").read_text()
    )
    values.update(diagnosis_code="c 187", diagnosis_date="2026.9.18")
    parsed = {
        "elements": [
            {"page": 1, "content": {"html": "김유정 C18.7 2026.09.18"}, "coordinates": BOX}
        ]
    }
    extras = {
        "diagnosis_code": {
            "_value": "C18.7",
            "confidence": "low",
            "word_coordinates": BOX,
            "page": 1,
        }
    }
    with Session(client.app.state.engine) as session:
        result = normalize_document("diagnosis", values, extras, parsed, 1, session=session)
    field = next(f for f in result.fields if f.key == "diagnosis_code")
    assert result.values["diagnosis_date"] == "2026-09-18"
    assert field.value == "C18.7" and field.source_found and field.bbox == BOX
    assert field.review_reasons == ["low_conf"]
    assert result.kcd_names["diagnosis_code"] == "구불결장의 악성 신생물"
    assert normal_scalar("amount", "841,600원") == 841600
    values["diagnosis_date"] = "2026-02-30"
    bad = normalize_document("diagnosis", values, {}, parsed, 1)
    assert "format" in next(f for f in bad.fields if f.key == "diagnosis_date").review_reasons


def test_data_no_model_confidence_and_parse_fallback():
    values = {
        "patient_name": "가상 고객",
        "period_start": "2026-09-22",
        "period_end": "2026-09-29",
        "inpatient_days": 8,
        "items": [
            {"name": "수술", "category": "처치 및 수술료", "amount": "3,200,000", "covered": True}
        ],
    }
    result = normalize_document("medical_detail", values, {}, {}, 2, is_data=True)
    assert result.values["items"][0]["category"] == "surgery"
    assert all(
        f.source_found and f.extract_conf is None and not f.review_reasons for f in result.fields
    )
    parsed = {
        "elements": [{"page": 2, "content": {"html": "<p>가상 고객</p>"}, "coordinates": BOX}]
    }
    result = normalize_document("other", {"patient_name": "가상 고객"}, {}, parsed, 3)
    assert result.fields[0].page == 2 and result.fields[0].bbox == BOX
    missing = normalize_document("other", {}, {}, {}, 4)
    assert "format" in missing.fields[0].review_reasons


def test_tool_call_extras_and_items():
    response = {
        "choices": [
            {
                "message": {
                    "content": '{"patient_name":"가상"}',
                    "tool_calls": [
                        {
                            "function": {
                                "name": "additional_values",
                                "arguments": '{"patient_name":{"_value":"가상","confidence":"high"}}',
                            }
                        }
                    ],
                }
            }
        ]
    }
    values, extras = completion_values(response)
    result = normalize_document("other", values, extras, {}, 1)
    assert result.fields[0].extract_conf == "high"
    assert result.fields[0].review_reasons == ["not_in_source"]
