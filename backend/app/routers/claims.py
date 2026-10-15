"""청구 변경 API. 서버 의존성에서 배정 범위와 역할을 함께 확인한다."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile
from sqlmodel import select

from app.auth import ClaimAccess, ClaimWrite, CurrentUser, SessionDep
from app.models import AuditLog, ProcessJob
from app.services.pipeline import active_job, create_job, run_job
from app.services.silson24 import attach_silson24
from app.services.uploads import claim_lock_path, save_uploads
from app.services.upstage import UpstageClient, locked

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
