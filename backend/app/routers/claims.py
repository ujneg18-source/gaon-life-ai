"""청구 변경 API. 서버 의존성에서 배정 범위와 역할을 함께 확인한다."""

from fastapi import APIRouter, Request

from app.auth import ClaimWrite, CurrentUser, SessionDep
from app.services.silson24 import attach_silson24

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("/{claim_id}/silson24")
def receive_silson24(claim: ClaimWrite, user: CurrentUser, session: SessionDep, request: Request):
    """허용된 가상 청구에 정형 데이터 3종을 붙인다. 파일 경로는 응답에 노출하지 않는다."""
    docs = attach_silson24(session, claim, request.app.state.settings, user.id)
    return {
        "is_mock": True,
        "documents": [
            {"id": doc.id, "doc_type": doc.doc_type, "source": doc.source, "status": doc.status}
            for doc in docs
        ],
    }
