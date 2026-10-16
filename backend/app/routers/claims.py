"""청구 변경 API. 서버 의존성에서 배정 범위와 역할을 함께 확인한다."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import select

from app.auth import ClaimAccess, ClaimWrite, CurrentUser, SessionDep
from app.models import (
    ActorType,
    AuditLog,
    Claim,
    ClaimStatus,
    Customer,
    Document,
    DocumentStatus,
    Issue,
    IssueKind,
    IssueStatus,
    ProcessJob,
    Role,
)
from app.services.pipeline import active_job, create_job, run_job
from app.services.silson24 import attach_silson24
from app.services.uploads import claim_lock_path, save_uploads
from app.services.upstage import UpstageClient, locked
from app.services.workspace import detail

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("/{claim_id}/silson24")
def receive_silson24(claim: ClaimWrite, user: CurrentUser, session: SessionDep, request: Request):
    """허용된 가상 청구에 정형 데이터 3종을 붙인다. 파일 경로는 응답에 노출하지 않는다."""
    config = request.app.state.settings
    with locked(claim_lock_path(config, claim.id)):
        if active_job(session, claim.id):
            raise HTTPException(409, "처리 중에는 문서를 추가할 수 없습니다.")
        docs = attach_silson24(session, claim, config, user.id)
    return {
        "is_mock": True,
        "documents": [
            {"id": doc.id, "doc_type": doc.doc_type, "source": doc.source, "status": doc.status}
            for doc in docs
        ],
    }


@router.post("/{claim_id}/documents")
def upload_documents(
    claim: ClaimWrite,
    user: CurrentUser,
    session: SessionDep,
    request: Request,
    files: list[UploadFile],
):
    """한 청구의 업로드·전자 연결·처리 시작을 잠금으로 직렬화한다."""
    config = request.app.state.settings
    with locked(claim_lock_path(config, claim.id)):
        docs = save_uploads(session, claim, files, config, user.id)
    return {
        "documents": [
            {"id": d.id, "doc_type": d.doc_type, "source": d.source, "status": d.status}
            for d in docs
        ]
    }


@router.post("/{claim_id}/process", status_code=202)
def process_documents(
    claim: ClaimWrite,
    user: CurrentUser,
    session: SessionDep,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """빠르게 작업 ID를 반환하고 응답 이후 작업 스레드에서 외부 API를 호출한다."""
    config = request.app.state.settings
    with locked(claim_lock_path(config, claim.id)):
        job = create_job(session, claim, user.id)
    factory = getattr(request.app.state, "upstage_client_factory", UpstageClient)
    background_tasks.add_task(run_job, request.app.state.engine, config, job.id, factory)
    return {"job_id": job.id}


@router.get("/{claim_id}/process/status")
def process_status(claim: ClaimAccess, session: SessionDep, job_id: str | None = None):
    query = select(ProcessJob).where(ProcessJob.claim_id == claim.id)
    if job_id:
        query = query.where(ProcessJob.id == job_id)
    job = session.exec(query.order_by(ProcessJob.created_at.desc())).first()
    if job is None:
        if job_id:
            raise HTTPException(404, "작업을 찾을 수 없습니다.")
        return {"stage": "idle", "state": "idle", "progress": 0}
    return {
        "job_id": job.id,
        "stage": job.stage,
        "state": job.state,
        "progress": job.progress,
        "errors": job.errors,
        "result": job.result,
    }


@router.get("/{claim_id}/logs")
def claim_logs(claim: ClaimAccess, session: SessionDep):
    """이력 조회도 담당자 배정 범위를 적용한다. 원본 파일 경로나 API 응답을 포함하지 않는다."""
    return session.exec(
        select(AuditLog).where(AuditLog.claim_id == claim.id).order_by(AuditLog.created_at)
    ).all()


@router.get("")
def list_claims(
    user: CurrentUser,
    session: SessionDep,
    request: Request,
    q: str = Query(default="", max_length=120),
    status: ClaimStatus | None = None,
):
    query = select(Claim).order_by(Claim.received_at.desc(), Claim.id.desc())
    if user.role == Role.REVIEWER:
        query = query.where(Claim.assignee_id == user.id)
    rows = list(session.exec(query).all())
    if q:
        rows = [
            c
            for c in rows
            if q.casefold()
            in f"{c.id} {c.customer_name} {c.policy_no} {session.get(Customer, c.customer_id).birth_date if c.customer_id else ''}".casefold()
        ]
    counts = {s.value: sum(c.status == s for c in rows) for s in ClaimStatus}
    counts["total"] = len(rows)
    selected = [c for c in rows if status is None or c.status == status]
    return {
        "items": [detail(session, c, request.app.state.settings) for c in selected],
        "counts": counts,
    }


@router.get("/{claim_id}")
def claim_detail(claim: ClaimAccess, user: CurrentUser, session: SessionDep, request: Request):
    response = detail(session, claim, request.app.state.settings)
    session.add(
        AuditLog(
            claim_id=claim.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="view",
            detail={"screen": "claim_detail"},
        )
    )
    session.commit()
    return response


class ClaimPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step: int | None = Field(default=None, ge=0, le=3)
    review_note: str | None = Field(default=None, max_length=2000)


@router.patch("/{claim_id}")
def patch_claim(payload: ClaimPatch, claim: ClaimWrite, user: CurrentUser, session: SessionDep):
    changes = payload.model_dump(exclude_unset=True)
    if any(v is None for v in changes.values()):
        raise HTTPException(422, "null로 지울 수 없습니다.")
    before = {k: getattr(claim, k) for k in changes}
    for key, value in changes.items():
        setattr(claim, key, value)
    session.add(claim)
    session.add(
        AuditLog(
            claim_id=claim.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="claim_edit",
            detail={"before": before, "after": changes},
        )
    )
    session.commit()
    return {k: getattr(claim, k) for k in changes}


@router.get("/{claim_id}/normalized")
def normalized_claim(claim: ClaimAccess, session: SessionDep, request: Request):
    return detail(session, claim, request.app.state.settings)["fields"]


@router.get("/{claim_id}/issues")
def claim_issues(claim: ClaimAccess, session: SessionDep):
    return session.exec(select(Issue).where(Issue.claim_id == claim.id).order_by(Issue.id)).all()


@router.post("/{claim_id}/submit")
def submit_claim(claim: ClaimWrite, user: CurrentUser, session: SessionDep):
    if session.exec(
        select(Issue).where(
            Issue.claim_id == claim.id,
            Issue.status == IssueStatus.OPEN,
            Issue.kind != IssueKind.INFO,
        )
    ).first():
        raise HTTPException(409, "열린 이슈를 먼저 확인해 주세요.")
    docs = session.exec(select(Document).where(Document.claim_id == claim.id)).all()
    if not docs or any(d.status != DocumentStatus.EXTRACTED for d in docs):
        raise HTTPException(409, "서류 처리가 완료되지 않았습니다.")
    claim.status = ClaimStatus.TO_PAYMENT_REVIEW
    session.add(claim)
    session.add(
        AuditLog(
            claim_id=claim.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="submit",
            detail={"destination": "payment_review"},
        )
    )
    session.commit()
    return {"status": claim.status}
