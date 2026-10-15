"""T-03 권한 검증에 필요한 설정 API. 운영 화면·재검사는 T-14에서 연결한다."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import AdminUser, CurrentUser, SessionDep
from app.models import ActorType, AuditLog, ReviewSettings

router = APIRouter(tags=["settings"])


class SettingsPatch(BaseModel):
    """알려진 설정만 수정한다. 필드가 빠진 것과 false를 구분하기 위해 nullable로 둔다."""

    model_config = ConfigDict(extra="forbid")
    review_on_low_conf: bool | None = None
    review_on_not_in_source: bool | None = None
    auto_pass_threshold: float | None = Field(default=None, ge=0, le=1)


def load_settings(session: SessionDep) -> ReviewSettings:
    """없는 기본값을 API에서 몰래 만들지 않고 시드 실행을 안내한다."""
    settings = session.get(ReviewSettings, 1)
    if settings is None:
        raise HTTPException(status_code=503, detail="기본 설정이 없습니다. 시드를 실행해 주세요.")
    return settings


@router.get("/settings", response_model=ReviewSettings)
def get_review_settings(user: CurrentUser, session: SessionDep):
    """로그인한 담당자도 현재 적용 기준을 읽을 수 있다."""
    return load_settings(session)


@router.patch("/settings", response_model=ReviewSettings)
def patch_review_settings(payload: SettingsPatch, user: AdminUser, session: SessionDep):
    """실제 관리자 API에 의존성을 적용해 403 동작을 검증한다."""
    row = load_settings(session)
    changes = payload.model_dump(exclude_unset=True)
    if any(value is None for value in changes.values()):
        raise HTTPException(status_code=422, detail="설정은 null로 지울 수 없습니다.")
    before = {key: getattr(row, key) for key in changes}
    for key, value in changes.items():
        setattr(row, key, value)
    session.add(row)
    session.add(
        AuditLog(
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="setting_change",
            detail={"before": before, "after": changes},
        )
    )
    session.commit()
    session.refresh(row)
    return row
