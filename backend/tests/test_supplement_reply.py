"""회신 업로드→새 문서 처리→CV-04 해소→회신 완료의 실제 API 흐름을 검증한다."""

from sqlmodel import Session

from app.config import PROJECT_ROOT
from app.models import ExtractedField, SupplementRequest, SupplementStatus
from tests.test_review_api import prepare


def test_surgery_reply_preserves_originals_and_resolves_cv04(client):
    base, data = prepare(client)
    # 기존 값의 담당자 확정은 회신 처리에서 삭제하거나 재추출하면 안 된다.
    field = next(f for f in data["fields"] if f["key"] == "patient_name")
    client.patch(f"/api/fields/{field['id']}", json={"confirmed_value": "김유정"})
    row = client.post(base + "/supplements").json()
    client.post(f"/api/supplements/{row['id']}/send")
    path = PROJECT_ROOT / "data/samples/kim_yujeong/supplement/수술확인서.png"
    response = client.post(
        base + "/documents", files=[("files", ("수술확인서.png", path.read_bytes(), "image/png"))]
    )
    assert response.status_code == 200
    after = client.get(base).json()
    assert after["submitted_count"] == 8 and after["status"] == "needs_review"
    assert not any(i["rule_id"] == "CV-04" and i["status"] == "open" for i in after["issues"])
    with Session(client.app.state.engine) as session:
        assert session.get(ExtractedField, field["id"]).confirmed_by is not None
        assert session.get(SupplementRequest, row["id"]).status == SupplementStatus.RECEIVED
    # 같은 파일을 다시 올려도 문서가 9장으로 늘어나지 않는다.
    client.post(
        base + "/documents", files=[("files", ("again.png", path.read_bytes(), "image/png"))]
    )
    assert client.get(base).json()["submitted_count"] == 8
