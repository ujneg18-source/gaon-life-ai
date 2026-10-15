"""화면용 조회의 배정 범위·동명이인·실제 집계와 단계 저장을 검증한다."""

from sqlmodel import Session

from app.models import Claim


def test_list_detail_search_and_permissions(client):
    assert client.get("/api/claims").status_code == 401
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    response = client.get("/api/claims").json()
    assert response["counts"]["total"] == 13 and len(response["items"]) == 13
    assert len(client.get("/api/claims?q=김서연").json()["items"]) == 3
    assert (
        len(
            {
                c["customer"]["birth_date"]
                for c in client.get("/api/claims?q=김서연").json()["items"]
            }
        )
        == 2
    )
    assert client.patch("/api/claims/GA-2610-0482", json={"step": 2}).json() == {"step": 2}
    assert client.patch("/api/claims/GA-2610-0482", json={"step": 5}).status_code == 422
    assert client.post("/api/claims/GA-2610-0482/submit").status_code == 409
    assert client.get("/api/claims/GA-2610-0482").json()["submitted_count"] == 0
    with Session(client.app.state.engine) as s:
        claim = s.get(Claim, "GA-2610-0482")
        claim.assignee_id = 2
        s.add(claim)
        s.commit()
    assert client.get("/api/claims/GA-2610-0482").status_code == 403
    assert client.get("/api/claims").json()["counts"]["total"] == 12
    client.post("/api/auth/demo-login", json={"role": "admin"})
    assert client.get("/api/claims").json()["counts"]["total"] == 13
    assert client.patch("/api/claims/GA-2610-0482", json={"step": 0}).status_code == 403


def test_detail_with_extracted_fields_is_read_only(client):
    """ORM 상태를 복제하지 않아 원문 대조 재계산이 읽기 조회를 깨뜨리지 않는다."""
    from tests.engine_fakes import app_files, install_fake

    install_fake(client.app)
    client.post("/api/auth/demo-login", json={"role": "reviewer"})
    base = "/api/claims/GA-2610-0482"
    assert client.post(base + "/documents", files=app_files()).status_code == 200
    assert client.post(base + "/silson24").status_code == 200
    assert client.post(base + "/process").status_code == 202
    first = client.get(base)
    assert first.status_code == 200
    assert first.json()["submitted_count"] == 7
    assert first.json()["required_count"] == 8
    assert first.json()["fields"] == client.get(base).json()["fields"]
