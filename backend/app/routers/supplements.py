"""보완 요청은 내부 모의 상태 전이만 수행한다. 외부 발송 클라이언트는 존재하지 않는다."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import select

from app.auth import ClaimWrite, CurrentUser, SessionDep, require_claim_access
from app.models import (
    ActorType,
    AuditLog,
    Claim,
    Issue,
    IssueKind,
    IssueStatus,
    Role,
    SupplementChannel,
    SupplementRequest,
    SupplementStatus,
)
from app.routers.review import access
from app.services.rules import review_from_db
from app.services.supplement import claim_supplement_draft

router = APIRouter(tags=["supplements"])


def dto(row, session):
    claim = session.get(Claim, row.claim_id)
    logs = session.exec(
        select(AuditLog).where(AuditLog.claim_id == row.claim_id).order_by(AuditLog.created_at)
    ).all()
    related = [log for log in logs if log.detail.get("request_id") == row.id]

    def event_time(action):
        return next((log.created_at.isoformat() for log in related if log.action == action), None)

    return {
        **row.model_dump(mode="json"),
        "customer_name": claim.customer_name,
        "created_at": event_time("supplement_draft"),
        "sent_at": event_time("supplement_send_mock"),
        "received_at": event_time("supplement_received"),
    }


@router.get("/supplements")
def list_supplements(user: CurrentUser, session: SessionDep, claim_id: str | None = None):
    query = select(SupplementRequest).join(Claim, SupplementRequest.claim_id == Claim.id)
    if claim_id:
        require_claim_access(claim_id, user, session)
        query = query.where(SupplementRequest.claim_id == claim_id)
    if user.role != Role.ADMIN:
        query = query.where(Claim.assignee_id == user.id)
    return [
        dto(row, session) for row in session.exec(query.order_by(SupplementRequest.id.desc())).all()
    ]


@router.post("/claims/{claim_id}/supplements")
def create_supplement(claim: ClaimWrite, user: CurrentUser, session: SessionDep, request: Request):
    config = request.app.state.settings
    review_from_db(session, claim, config)
    missing = session.exec(
        select(Issue).where(
            Issue.claim_id == claim.id,
            Issue.kind == IssueKind.MISSING,
            Issue.status == IssueStatus.OPEN,
        )
    ).all()
    # 필수 코드 집합과 실제 제출 유형의 차를 사용해 문구에서 서류를 추측하지 않는다.
    from app.services.workspace import detail

    data = detail(session, claim, config)
    submitted = {d["doc_type"] for d in data["documents"] if d["status"] == "extracted"}
    codes = sorted(set(data["required"]) - submitted)
    if any(i.rule_id == "REQ-diagnosis-code" for i in missing):
        codes = sorted(set(codes) | {"diagnosis"})
    if not missing or not codes:
        raise HTTPException(409, "요청할 미제출 필수 서류가 없습니다.")
    active = session.exec(
        select(SupplementRequest).where(
            SupplementRequest.claim_id == claim.id,
            SupplementRequest.status.in_([SupplementStatus.DRAFT, SupplementStatus.SENT_MOCK]),
        )
    ).first()
    if active and active.status == SupplementStatus.SENT_MOCK:
        raise HTTPException(409, "이미 발송한 보완 요청의 회신을 기다리고 있어요.")
    # 서버가 판단한 누락 서류에 고정 안내 양식의 고객/계약/접수 정보를 채운다.
    generated = claim_supplement_draft(session, user, config, claim.id, codes)
    message = generated.get("draft_text")
    if not message:
        raise HTTPException(409, generated.get("message", "안내 문구를 만들지 못했어요."))
    source = "fixed_template"
    # 명시적인 생성 요청은 기존 미발송 초안도 재생성한다. 오래된 Solar 캐시를 재사용하지 않는다.
    row = active or SupplementRequest(claim_id=claim.id, doc_types=codes, message=message)
    row.doc_types = codes
    row.message = message
    session.add(row)
    session.flush()
    session.add(
        AuditLog(
            claim_id=claim.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="supplement_draft",
            detail={"request_id": row.id, "doc_types": codes, "message_source": source},
        )
    )
    session.commit()
    return {**dto(row, session), "message_source": source}


class SupplementPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str | None = Field(default=None, min_length=1, max_length=2000)
    channel: SupplementChannel | None = None


@router.patch("/supplements/{request_id}")
def edit_supplement(
    request_id: int, payload: SupplementPatch, user: CurrentUser, session: SessionDep
):
    row = session.get(SupplementRequest, request_id)
    claim = access(row, user, session, write=True)
    if row.status != SupplementStatus.DRAFT:
        raise HTTPException(409, "발송한 요청은 수정할 수 없습니다.")
    changes = payload.model_dump(exclude_unset=True)
    if any(v is None for v in changes.values()):
        raise HTTPException(422, "값을 비울 수 없습니다.")
    before = {k: getattr(row, k) for k in changes}
    for key, value in changes.items():
        setattr(row, key, value)
    session.add(row)
    session.add(
        AuditLog(
            claim_id=claim.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="supplement_edit",
            detail={"request_id": row.id, "before": before, "after": changes},
        )
    )
    session.commit()
    return dto(row, session)


@router.post("/supplements/{request_id}/send")
def send_mock(request_id: int, user: CurrentUser, session: SessionDep):
    row = session.get(SupplementRequest, request_id)
    claim = access(row, user, session, write=True)
    if row.status == SupplementStatus.SENT_MOCK:
        return dto(row, session)
    if row.status != SupplementStatus.DRAFT:
        raise HTTPException(409, "초안만 모의 발송할 수 있습니다.")
    row.status = SupplementStatus.SENT_MOCK
    session.add(row)
    session.add(
        AuditLog(
            claim_id=claim.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="supplement_send_mock",
            detail={"request_id": row.id, "channel": row.channel, "is_mock": True},
        )
    )
    session.commit()
    return dto(row, session)
