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


def test_fixed_letter_variables_and_regeneration(client, monkeypatch):
    """별도 Solar 문구 대신 챗봇의 실제 누락 조회/템플릿 결과와 완전히 일치해야 한다."""
    import httpx

    from app.models import User
    from app.services.supplement import claim_supplement_draft

    def no_solar(*args, **kwargs):
        raise AssertionError("안내 문자 생성에서 외부 LLM을 호출하면 안 된다")

    base, _data = prepare(client)
    monkeypatch.setattr(httpx.Client, "post", no_solar)
    # TestClient.post도 httpx를 상속하므로 API 자체는 transport가 아닌 request로 실행한다.
    response = client.request("POST", base + "/supplements")
    assert response.status_code == 200
    row = response.json()
    with Session(client.app.state.engine) as session:
        user = session.get(User, 1)
        config = client.app.state.settings
        expected = claim_supplement_draft(session, user, config, row["claim_id"], row["doc_types"])
    assert row["message"] == expected["draft_text"]
    assert row["message_source"] == "fixed_template"
    assert row["message"].startswith("안녕하세요. 김유정 고객님!")
    assert row["claim_id"] in row["message"]
    assert "가입 상품:" in row["message"] and "접수일:" in row["message"]
    assert len(row["message"]) > 400
    assert "수술받으신 병원 원무과" in row["message"]
    assert "편리한 제출" not in row["message"]
    assert (
        client.patch(
            f"/api/supplements/{row['id']}", json={"message": "이전 안내 문구"}
        ).status_code
        == 200
    )
    refreshed = client.request("POST", base + "/supplements").json()
    assert refreshed["id"] == row["id"]
    assert refreshed["message"] == expected["draft_text"]


def test_supplement_list_is_scoped_to_selected_claim(client):
    """다른 고객으로 전환하면 이전 고객의 초안이 목록/편집기에 섞이지 않는다."""
    base, _data = prepare(client)
    created = client.post(base + "/supplements").json()
    others = [
        row for row in client.get("/api/claims").json()["items"] if row["id"] != created["claim_id"]
    ]
    other = others[0]
    assert client.get("/api/supplements", params={"claim_id": other["id"]}).json() == []
    own = client.get("/api/supplements", params={"claim_id": created["claim_id"]}).json()
    assert len(own) == 1 and own[0]["customer_name"] == created["customer_name"]
    assert client.post(f"/api/claims/{other['id']}/supplements").status_code == 409
    with Session(client.app.state.engine) as session:
        claim = session.get(Claim, created["claim_id"])
        claim.assignee_id = 2
        session.add(claim)
        session.commit()
    assert (
        client.get("/api/supplements", params={"claim_id": created["claim_id"]}).status_code == 403
    )


def test_fixed_templates_cover_all_supported_documents(client):
    from app.models import User
    from app.services.presentation import document_label
    from app.services.supplement import claim_supplement_draft

    prepare(client)
    config = client.app.state.settings
    with Session(client.app.state.engine) as session:
        for code in config.UPSTAGE_DOC_CLASSES:
            generated = claim_supplement_draft(
                session, session.get(User, 1), config, "GA-2610-0482", [code]
            )
            assert generated["draft_text"]
            assert document_label(code, config) in generated["draft_text"]
            assert "{customer_name}" not in generated["draft_text"]
            assert len(generated["draft_text"]) <= config.SUPPLEMENT_MAX_CHARS


def test_sent_history_uses_real_audit_time_and_cannot_regenerate(client):
    base, _ = prepare(client)
    draft = client.post(base + "/supplements").json()
    assert draft["created_at"] and draft["sent_at"] is None and draft["received_at"] is None
    client.post(f"/api/supplements/{draft['id']}/send")
    history = client.get("/api/supplements", params={"claim_id": draft["claim_id"]}).json()
    assert history[0]["sent_at"]
    assert client.post(base + "/supplements").status_code == 409
