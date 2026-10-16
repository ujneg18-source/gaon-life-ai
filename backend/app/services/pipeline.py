"""청구 처리 작업. 파일은 캐시로 재사용하고 DB 상태·실패·이력을 단계별로 보존한다."""

import json
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, delete, select

from app.config import Settings
from app.models import (
    ActorType,
    AuditLog,
    Claim,
    ClaimStatus,
    Document,
    DocumentSource,
    DocumentStatus,
    DocumentType,
    ExtractedField,
    ProcessJob,
    SupplementRequest,
    SupplementStatus,
    utc_now,
)
from app.schemas.documents import DOCUMENT_SCHEMAS
from app.schemas.to_upstage import to_extract_schema
from app.services.normalize import additional_values, completion_values, normalize_document
from app.services.rules import review_from_db
from app.services.upstage import UpstageClient, UpstageError


def active_job(session: Session, claim_id: str) -> ProcessJob | None:
    return session.exec(
        select(ProcessJob).where(
            ProcessJob.claim_id == claim_id, ProcessJob.state.in_(["queued", "running"])
        )
    ).first()


def create_job(session: Session, claim: Claim, actor_id: int) -> ProcessJob:
    """실제 DB의 부분 유일 인덱스로 이중 실행도 방지한다."""
    if active_job(session, claim.id):
        raise HTTPException(409, "이미 처리 중인 청구입니다.")
    docs = session.exec(select(Document).where(Document.claim_id == claim.id)).all()
    if not docs:
        raise HTTPException(422, "먼저 서류를 첨부해 주세요.")
    for doc in docs:
        confirmed = session.exec(
            select(ExtractedField).where(
                ExtractedField.document_id == doc.id, ExtractedField.confirmed_by.is_not(None)
            )
        ).first()
        if confirmed and doc.status != DocumentStatus.EXTRACTED:
            raise HTTPException(409, "담당자 확정값이 있는 문서는 재분석할 수 없습니다.")
    job = ProcessJob(id=uuid4().hex, claim_id=claim.id, actor_id=actor_id)
    session.add(job)
    claim.status = ClaimStatus.PROCESSING
    session.add(claim)
    session.add(
        AuditLog(
            claim_id=claim.id,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="process_start",
            detail={"job_id": job.id, "document_count": len(docs)},
        )
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "이미 처리 중인 청구입니다.") from None
    return job


def recover_interrupted(engine: Engine) -> None:
    """메모리 작업을 자동 재실행하지 않는다. 재시작 당시 미완료 작업은 중단으로 기록한다."""
    with Session(engine) as session:
        jobs = session.exec(
            select(ProcessJob).where(ProcessJob.state.in_(["queued", "running"]))
        ).all()
        for job in jobs:
            job.state = "failed"
            job.stage = "failed"
            job.errors = [*job.errors, {"code": "process_interrupted"}]
            job.updated_at = utc_now()
            session.add(job)
            claim = session.get(Claim, job.claim_id)
            claim.status = ClaimStatus.NEEDS_REVIEW
            session.add(claim)
            session.add(
                AuditLog(
                    claim_id=claim.id,
                    actor_type=ActorType.AI,
                    action="process_failed",
                    detail={"job_id": job.id, "code": "process_interrupted"},
                )
            )
        session.commit()


def classified_type(response: dict) -> tuple[DocumentType, float | None]:
    """문서 유형은 모델 응답에서만 읽는다. 파일명·정답 파일로 분류를 덮어쓰지 않는다."""
    content = response["choices"][0]["message"]["content"]
    try:
        value = json.loads(content)
    except (ValueError, TypeError):
        value = content
    metadata = additional_values(response["choices"][0]["message"])
    conf = metadata.get("document_type", {}).get("confidence_score")
    if isinstance(value, dict):
        conf = value.get("confidence", conf)
        value = value.get("doc_type", value.get("category", value.get("class")))
    if value == "others":
        value = "other"  # 가이드의 예전 예시 별칭만 호환한다.
    if not isinstance(conf, (int, float)) or isinstance(conf, bool) or not 0 <= conf <= 1:
        conf = None
    return DocumentType(value), conf


def run_job(engine: Engine, settings: Settings, job_id: str, client_factory=UpstageClient) -> None:
    """요청 세션을 재사용하지 않고 작업 스레드 전용 세션을 연다. 오류는 안전한 코드만 남긴다."""
    with Session(engine) as session:
        job = session.get(ProcessJob, job_id)
        if job is None or job.state != "queued":
            return
        job.state = "running"
        session.add(job)
        session.commit()
        docs = session.exec(
            select(Document).where(Document.claim_id == job.claim_id).order_by(Document.id)
        ).all()
        total = sum(1 if d.source == DocumentSource.SILSON24 else 3 for d in docs) + 1
        completed = 0

        def stage(name: str):
            job.stage = name
            job.progress = min(int(completed / total * 100), 99)
            job.updated_at = utc_now()
            session.add(job)
            session.commit()

        try:
            with client_factory(settings) as client:
                for doc in docs:
                    # 이미 처리한 원본과 담당자 확정값은 보존하고 새로 회신한 서류만 읽는다.
                    if doc.status == DocumentStatus.EXTRACTED:
                        completed += 1 if doc.source == DocumentSource.SILSON24 else 3
                        continue
                    try:
                        from pathlib import Path

                        from app.services.demo_samples import supplement_input

                        claim = session.get(Claim, job.claim_id)
                        mock = (
                            supplement_input(settings, claim, Path(doc.file_path))
                            if doc.source == DocumentSource.IMAGE
                            else None
                        )
                        if mock:
                            doc.doc_type = mock["doc_type"]
                            doc.raw_result = {
                                **doc.raw_result,
                                "provenance": "mock",
                                "mock_input": mock,
                            }

                        if doc.source == DocumentSource.SILSON24 or mock:
                            values = mock or doc.raw_result["data"]
                            extras = {}
                            parsed = {}
                            stage("extract")
                        else:
                            from pathlib import Path

                            path = Path(doc.file_path)
                            stage("classify")
                            classified = client.classify(path)
                            doc.doc_type, doc.classify_conf = classified_type(classified)
                            doc.raw_result = {**doc.raw_result, "classify": classified}
                            session.add(doc)
                            session.commit()
                            completed += 1
                            stage("parse")
                            parsed = client.parse(path)
                            doc.raw_result = {**doc.raw_result, "parse": parsed}
                            doc.status = DocumentStatus.PARSED
                            session.add(doc)
                            session.commit()
                            completed += 1
                            stage("extract")
                            model = DOCUMENT_SCHEMAS.get(doc.doc_type)
                            if model is None:
                                # Tier 3는 유형·원문만 처리한다. 미지원 세부 항목을 추출한 척하지 않는다.
                                values, extras = {}, {}
                            else:
                                extracted = client.extract(
                                    path, to_extract_schema(model), doc.doc_type
                                )
                                doc.raw_result = {**doc.raw_result, "extract": extracted}
                                values, extras = completion_values(extracted)
                        if doc.doc_type in DOCUMENT_SCHEMAS:
                            normalized = normalize_document(
                                doc.doc_type,
                                values,
                                extras,
                                parsed,
                                doc.id,
                                is_data=doc.source == DocumentSource.SILSON24 or bool(mock),
                                session=session,
                            )
                            session.exec(
                                delete(ExtractedField).where(ExtractedField.document_id == doc.id)
                            )
                            session.add_all(normalized.fields)
                            doc.raw_result = {
                                **doc.raw_result,
                                "normalized": normalized.values,
                                "kcd_names": normalized.kcd_names,
                                "parse_evidence": normalized.evidence,
                            }
                        else:
                            doc.raw_result = {**doc.raw_result, "normalized": {}}
                        doc.status = DocumentStatus.EXTRACTED
                        # 재시도에서 성공했다면 이전 오류 메타데이터만 제거한다.
                        doc.raw_result = {k: v for k, v in doc.raw_result.items() if k != "error"}
                        session.add(doc)
                        session.commit()
                        completed += 1
                    except Exception as error:  # noqa: BLE001 — 문서별 실패를 기록하고 나머지 문서를 보존하는 작업 경계
                        session.rollback()
                        job = session.get(ProcessJob, job_id)
                        doc = session.get(Document, doc.id)
                        code = (
                            str(error)
                            if isinstance(error, UpstageError)
                            else "invalid_document_result"
                        )
                        job.errors = [*job.errors, {"document_id": doc.id, "code": code}]
                        doc.status = DocumentStatus.FAILED
                        doc.raw_result = {**doc.raw_result, "error": code}
                        session.add_all([doc, job])
                        session.commit()
                stage("review")
                claim = session.get(Claim, job.claim_id)
                report = review_from_db(session, claim, settings)
                # 수신만으로 완료 처리하지 않는다. 요청 유형이 모두 정상 추출된 뒤 회신 완료로 기록한다.
                submitted = {d.doc_type for d in docs if d.status == DocumentStatus.EXTRACTED}
                for request in session.exec(
                    select(SupplementRequest).where(
                        SupplementRequest.claim_id == claim.id,
                        SupplementRequest.status == SupplementStatus.SENT_MOCK,
                    )
                ).all():
                    if set(request.doc_types) <= submitted:
                        request.status = SupplementStatus.RECEIVED
                        session.add(request)
                        session.add(
                            AuditLog(
                                claim_id=claim.id,
                                actor_type=ActorType.USER,
                                actor_id=job.actor_id,
                                action="supplement_received",
                                detail={"request_id": request.id, "doc_types": request.doc_types},
                            )
                        )
                job.result = {
                    "required": report.required,
                    "document_count": len(docs),
                    "issue_count": len(report.issues),
                    "claim_status": report.status,
                    "cache_hits": client.cache_hits,
                    "requests_made": client.requests_made,
                }
                job.state = "failed" if job.errors else "done"
                job.stage = job.state
                job.progress = 100
                job.updated_at = utc_now()
                session.add(job)
                session.add(
                    AuditLog(
                        claim_id=claim.id,
                        actor_type=ActorType.AI,
                        action="process_failed" if job.errors else "process_done",
                        detail={"job_id": job.id, **job.result},
                    )
                )
                session.commit()
        except Exception:  # noqa: BLE001 — 미예상 작업 오류도 완료로 오인하지 않게 DB에 기록
            session.rollback()
            job = session.get(ProcessJob, job_id)
            job.state = "failed"
            job.stage = "failed"
            job.updated_at = utc_now()
            job.errors = [*job.errors, {"code": "processing_failed"}]
            claim = session.get(Claim, job.claim_id)
            claim.status = ClaimStatus.NEEDS_REVIEW
            session.add_all(
                [
                    job,
                    claim,
                    AuditLog(
                        claim_id=claim.id,
                        actor_type=ActorType.AI,
                        action="process_failed",
                        detail={"job_id": job.id, "code": "processing_failed"},
                    ),
                ]
            )
            session.commit()
