"""모의 발송의 단방향 상태·설정 재검사·배정/관리자 권한을 검증한다."""

from sqlmodel import Session, select

from app.models import AuditLog, Claim, ExtractedField
from tests.test_review_api import prepare


def test_supplement_draft_edit_send_and_permissions(client):
    base, _data = prepare(client)
    draft = client.post(base + "/supplements")
    assert draft.status_code == 200
    row = draft.json()
    assert row["doc_types"] == ["surgery_cert"] and row["status"] == "draft"
    assert client.post(base + "/supplements").json()["id"] == row["id"]
    url = f"/api/supplements/{row['id']}"
    assert client.patch(url, json={"message": "가상 안내문", "channel": "sms"}).status_code == 200
    assert client.post(url + "/send").json()["status"] == "sent_mock"
    assert client.post(url + "/send").json()["status"] == "sent_mock"
    assert client.patch(url, json={"message": "다시 수정"}).status_code == 409
    with Session(client.app.state.engine) as s:
        assert (
            len(s.exec(select(AuditLog).where(AuditLog.action == "supplement_send_mock")).all())
            == 1
        )
        claim = s.get(Claim, "GA-2610-0482")
        claim.assignee_id = 2
        s.add(claim)
        s.commit()
    assert client.get("/api/supplements").json() == []
    assert client.post(url + "/send").status_code == 403
    client.post("/api/auth/demo-login", json={"role": "admin"})
    assert len(client.get("/api/supplements").json()) == 1
    assert client.post(url + "/send").status_code == 403


def test_admin_flags_rules_reinspection_and_reopen(client):
    base, data = prepare(client)
    field = next(f for f in data["fields"] if f["key"] == "patient_name")
    with Session(client.app.state.engine) as s:
        f = s.get(ExtractedField, field["id"])
        f.review_reasons = ["low_conf", "not_in_source", "format"]
        s.add(f)
        s.commit()
    assert client.patch("/api/settings", json={"review_on_format": False}).status_code == 403
    client.post("/api/auth/demo-login", json={"role": "admin"})
    r = client.patch(
        "/api/settings",
        json={
            "review_on_low_conf": False,
            "review_on_not_in_source": False,
            "review_on_format": False,
        },
    )
    assert r.status_code == 200
    issues = client.get(base + "/issues").json()
    assert not any(i["rule_id"] == "FIELD-patient_name" and i["status"] == "open" for i in issues)
    assert client.patch("/api/settings", json={"review_on_format": True}).status_code == 200
    assert any(
        i["rule_id"] == "FIELD-patient_name" and i["status"] == "open"
        for i in client.get(base + "/issues").json()
    )
    rules = client.get("/api/rules/required-docs").json()
    rule = next(r for r in rules if r["claim_type"] == "cancer_diagnosis")
    assert (
        client.put(
            "/api/rules/required-docs",
            json=[{"id": rule["id"], "doc_types": ["diagnosis", "pathology", "imaging_report"]}],
        ).status_code
        == 200
    )
    assert client.get(base).json()["required_count"] == 9
    assert (
        client.put(
            "/api/rules/required-docs", json=[{"id": rule["id"], "doc_types": ["fake"]}]
        ).status_code
        == 422
    )
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    assert client.put("/api/rules/required-docs", json=[]).status_code == 403


def test_solar_template_cache_and_model_response(client):
    import httpx
    from pydantic import SecretStr

    from app.services.supplement import draft_message

    config = client.app.state.settings.model_copy(
        update={"UPSTAGE_API_KEY": SecretStr("test"), "USE_CACHED_RESULTS": False}
    )
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "김가상 고객님, DEMO-1 건 수술확인서를 제출해 주세요."}}
                ]
            },
        )

    transport = httpx.MockTransport(respond)
    assert (
        draft_message(config, "김가상", "DEMO-1", ["수술확인서"], transport=transport)[1] == "solar"
    )
    assert (
        draft_message(config, "김가상", "DEMO-1", ["수술확인서"], transport=transport)[1]
        == "solar_cached"
    )
    assert len(calls) == 1
    assert (
        draft_message(
            config.model_copy(update={"USE_CACHED_RESULTS": True}),
            "이가상",
            "DEMO-2",
            ["수술확인서"],
            transport=transport,
        )[1]
        == "standard_template"
    )
    assert len(calls) == 1
