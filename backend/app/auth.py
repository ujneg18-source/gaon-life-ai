"""서명된 httpOnly 세션과 역할 의존성. 클라이언트가 보낸 역할을 권한 근거로 쓰지 않는다."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlmodel import Session

from app.db import get_session
from app.models import Claim, Role, User

SessionDep = Annotated[Session, Depends(get_session)]


def current_user(request: Request, session: SessionDep) -> User:
    """쿠키에는 사용자 ID만 두고, 매 요청에서 DB의 현재 역할을 다시 확인한다."""
    user_id = request.session.get(request.app.state.settings.SESSION_USER_KEY)
    user = session.get(User, user_id) if isinstance(user_id, int) else None
    if user is None:
        raise HTTPException(status_code=401, detail="데모 로그인이 필요합니다.")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_admin(user: CurrentUser) -> User:
    """메뉴 숨김과 별개로 서버에서 관리자 권한을 강제한다."""
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="관리자만 사용할 수 있습니다.")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


def require_claim_access(claim_id: str, user: CurrentUser, session: SessionDep) -> Claim:
    """후속 청구 API도 같은 배정 범위를 쓰도록 공통화한다. 관리자는 조회 가능하다."""
    claim = session.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="청구 건을 찾을 수 없습니다.")
    if user.role != Role.ADMIN and claim.assignee_id != user.id:
        raise HTTPException(status_code=403, detail="배정된 청구만 조회할 수 있습니다.")
    return claim
