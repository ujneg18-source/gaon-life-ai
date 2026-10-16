"""관리자에게만 명시적 시연 초기화를 허용한다."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from app.auth import AdminUser, CurrentUser, SessionDep
from app.routers.settings import ensure_idle
from app.services.demo_reset import read_revision, reset_demo

router = APIRouter(tags=["demo"])


class ResetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: bool


@router.get("/demo/state")
def demo_state(user: CurrentUser, request: Request):
    return {"revision": read_revision(request.app.state.settings)}


@router.post("/demo/reset")
def demo_reset(payload: ResetInput, user: AdminUser, session: SessionDep, request: Request):
    config = request.app.state.settings
    if not payload.confirm:
        raise HTTPException(422, "시연 초기화를 확인해 주세요.")
    if not config.DEMO_MODE:
        raise HTTPException(403, "시연 모드에서만 초기화할 수 있습니다.")
    ensure_idle(session)
    session.rollback()  # 현재 조회 트랜잭션이 새 시드 쓰기를 잠그지 않게 종료한다.
    try:
        result = reset_demo(config)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None
    request.session.clear()
    return result
