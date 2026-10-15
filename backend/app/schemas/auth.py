"""인증 입출력 DTO. DB 전체 객체 대신 허용된 공개 필드만 응답한다."""

from pydantic import BaseModel, ConfigDict

from app.models import Role


class DemoLoginInput(BaseModel):
    """두 데모 역할만 허용한다. 이메일이나 임의 사용자 ID 로그인은 제공하지 않는다."""

    model_config = ConfigDict(extra="forbid")
    role: Role


class UserPublic(BaseModel):
    """프론트 상단 표시용 사용자 객체. 세션 서명이나 환경 설정은 포함하지 않는다."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    role: Role
