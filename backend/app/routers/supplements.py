"""보완 요청은 내부 모의 상태 전이만 수행한다. 외부 발송 클라이언트는 존재하지 않는다."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import select

from app.auth import ClaimWrite, CurrentUser, SessionDep
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
from app.services.supplement import draft_message

router = APIRouter(tags=["supplements"])


def dto(row, session):
    claim = session.get(Claim, row.claim_id)
    return {**row.model_dump(mode="json"), "customer_name": claim.customer_name}


@router.get("/supplements")
def list_supplements(user: CurrentUser, session: SessionDep):
    query = select(SupplementRequest).join(Claim, SupplementRequest.claim_id == Claim.id)
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
    if not missing or not codes:
        raise HTTPException(409, "요청할 미제출 필수 서류가 없습니다.")
    active = session.exec(
        select(SupplementRequest).where(
            SupplementRequest.claim_id == claim.id,
            SupplementRequest.status.in_([SupplementStatus.DRAFT, SupplementStatus.SENT_MOCK]),
        )
    ).first()
    if active:
        return dto(active, session)
    labels = [config.UPSTAGE_DOC_CLASSES[c].split(".")[0] for c in codes]
    # 캐시 전용 서버에서는 Solar 호출 없이 표준 문구를 사용하며 이를 이력·응답에 명시한다.
    message, source = draft_message(config, claim.customer_name, claim.id, labels)
    row = SupplementRequest(claim_id=claim.id, doc_types=codes, message=message)
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
