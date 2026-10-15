"""문서 원본과 사람의 확인을 연결한다. 모든 객체 ID에서 청구 배정 권한을 다시 확인한다."""

import re
from copy import deepcopy
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.auth import CurrentUser, SessionDep, require_claim_access
from app.models import (
    ActorType,
    AuditLog,
    Document,
    DocumentSource,
    ExtractedField,
    Issue,
    IssueStatus,
    Role,
    utc_now,
)
from app.schemas.documents import DOCUMENT_SCHEMAS, CommonDoc
from app.services.normalize import canonical, normal_scalar
from app.services.rules import review_from_db, set_nested
from app.services.workspace import detail

router = APIRouter(tags=["review"])


def access(row, user, session, *, write=False):
    if row is None:
        raise HTTPException(404, "항목을 찾을 수 없습니다.")
    claim = require_claim_access(row.claim_id, user, session)
    if write and user.role != Role.REVIEWER:
        raise HTTPException(403, "배정 담당자만 변경할 수 있습니다.")
    return claim


@router.get("/documents/{doc_id}")
def document_info(doc_id: int, user: CurrentUser, session: SessionDep, request: Request):
    doc = session.get(Document, doc_id)
    claim = access(doc, user, session)
    data = detail(session, claim, request.app.state.settings)
    return {
        **next(d for d in data["documents"] if d["id"] == doc_id),
        "fields": [f for f in data["fields"] if f["document_id"] == doc_id],
    }


@router.get("/documents/{doc_id}/image")
def document_image(doc_id: int, user: CurrentUser, session: SessionDep, request: Request):
    doc = session.get(Document, doc_id)
    access(doc, user, session)
    config = request.app.state.settings
    path = Path(doc.file_path).resolve()
    if doc.source == DocumentSource.SILSON24:
        # 전자 수신의 원본은 JSON이다. 대응하는 가상 서식 이미지만 표시하고 화면에 이를 명시한다.
        if not path.is_relative_to(config.MOCK_SILSON24_PATH.resolve()):
            raise HTTPException(404, "가상 원본이 없습니다.")
        path = config.SAMPLE_PATH / "png" / (path.stem + ".png")
    elif not path.is_relative_to(config.UPLOAD_PATH.resolve()):
        raise HTTPException(404, "허용된 원본이 아닙니다.")
    if not path.is_file():
        raise HTTPException(404, "원본 파일이 없습니다.")
    return FileResponse(path, headers={"Cache-Control": "private, no-store"})


class FieldPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed_value: str = Field(min_length=1, max_length=2000)


@router.patch("/fields/{field_id}")
def confirm_field(
    field_id: int, payload: FieldPatch, user: CurrentUser, session: SessionDep, request: Request
):
    field = session.get(ExtractedField, field_id)
    if field is None:
        raise HTTPException(404, "추출 항목이 없습니다.")
    doc = session.get(Document, field.document_id)
    claim = access(doc, user, session, write=True)
    try:
        value = normal_scalar(field.key, payload.confirmed_value)
        normalized = deepcopy(doc.raw_result.get("normalized", {}))
        set_nested(normalized, field.key, value)
        try:
            DOCUMENT_SCHEMAS.get(doc.doc_type, CommonDoc).model_validate(normalized)
        except ValidationError as error:
            # 기존 다른 오류 때문에 올바른 수정까지 막지는 않는다. 변경한 셀의 오류만 거절한다.
            parts = re.findall(r"[^.\[\]]+", field.key)
            if any([str(p) for p in e["loc"]] == parts for e in error.errors()):
                raise ValueError("해당 항목의 형식을 확인해 주세요.") from None
    except (ValueError, TypeError, IndexError, KeyError):
        raise HTTPException(422, "확정값의 날짜·코드·금액 형식을 확인해 주세요.") from None
    before = field.confirmed_value if field.confirmed_value is not None else field.value
    field.confirmed_value = canonical(value) if isinstance(value, bool) else str(value)
    field.confirmed_by = user.id
    session.add(field)
    session.add(
        AuditLog(
            claim_id=claim.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="field_confirm",
            detail={
                "field_id": field.id,
                "key": field.key,
                "before": before,
                "after": field.confirmed_value,
            },
        )
    )
    session.flush()
    review_from_db(session, claim, request.app.state.settings)
    session.commit()
    return {"id": field.id, "confirmed_value": field.confirmed_value}


@router.post("/issues/{issue_id}/resolve")
def resolve_issue(issue_id: int, user: CurrentUser, session: SessionDep, request: Request):
    issue = session.get(Issue, issue_id)
    claim = access(issue, user, session, write=True)
    if issue.status == IssueStatus.OPEN:
        issue.status = IssueStatus.RESOLVED
        issue.resolved_by = user.id
        issue.resolved_at = utc_now()
        session.add(issue)
        session.add(
            AuditLog(
                claim_id=claim.id,
                actor_type=ActorType.USER,
                actor_id=user.id,
                action="issue_resolve",
                detail={"issue_id": issue.id, "rule_id": issue.rule_id},
            )
        )
        session.flush()
        review_from_db(session, claim, request.app.state.settings)
        session.commit()
    return {"id": issue.id, "status": issue.status}
