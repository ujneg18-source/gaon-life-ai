"""데모 인증 API: 실제 계정 가입·비밀번호 인증은 이번 PoC 범위가 아니다."""

from fastapi import APIRouter, HTTPException, Request, Response
from sqlmodel import select

from app.auth import CurrentUser, SessionDep
from app.models import ActorType, AuditLog, Role, User
from app.schemas.auth import DemoLoginInput, UserPublic

router = APIRouter(tags=["auth"])


@router.post("/auth/demo-login", response_model=UserPublic)
def demo_login(payload: DemoLoginInput, request: Request, session: SessionDep):
    """데모 시드 계정만 선택하고 이전 세션을 지워 역할 전환 시 값이 섞이지 않게 한다."""
    settings = request.app.state.settings
    email = (
        settings.DEMO_ADMIN_EMAIL if payload.role == Role.ADMIN else settings.DEMO_REVIEWER_EMAIL
    )
    user = session.exec(select(User).where(User.email == email, User.role == payload.role)).first()
    if user is None:
        raise HTTPException(status_code=503, detail="데모 계정이 없습니다. 시드를 실행해 주세요.")
    request.session.clear()
    request.session[settings.SESSION_USER_KEY] = user.id
    session.add(
        AuditLog(
            actor_type=ActorType.USER, actor_id=user.id, action="login", detail={"role": user.role}
        )
    )
    session.commit()
    return user


@router.get("/me", response_model=UserPublic)
def me(user: CurrentUser):
    """브라우저 새로고침 시 서버 세션으로 로그인 상태를 복구한다."""
    return user


@router.post("/auth/logout", status_code=204)
def logout(request: Request, user: CurrentUser, session: SessionDep):
    """브라우저 세션 쿠키를 만료시키고 역할 전환 전 로그아웃을 기록한다."""
    request.session.clear()
    session.add(AuditLog(actor_type=ActorType.USER, actor_id=user.id, action="logout"))
    session.commit()
    return Response(status_code=204)
