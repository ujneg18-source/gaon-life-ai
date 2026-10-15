"""원본 업로드 저장. 파일명 대신 내용 해시로 경로를 만들고 입력을 모두 검증한 뒤 저장한다."""

import hashlib
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlmodel import Session, select

from app.config import Settings
from app.models import ActorType, AuditLog, Claim, Document
from app.services.pipeline import active_job
from app.services.upstage import file_pages


def claim_lock_path(settings: Settings, claim_id: str) -> Path:
    return settings.DATA_PATH / "locks" / (hashlib.sha256(claim_id.encode()).hexdigest() + ".lock")


def save_uploads(
    session: Session, claim: Claim, files: list[UploadFile], settings: Settings, actor_id: int
) -> list[Document]:
    """확장자·실제 형식·용량·페이지 수를 검사하고 같은 청구의 동일 파일은 재사용한다."""
    if active_job(session, claim.id):
        raise HTTPException(409, "처리 중에는 문서를 추가할 수 없습니다.")
    if not files or len(files) > settings.MAX_FILES_PER_CLAIM:
        raise HTTPException(422, "첨부 파일 수를 확인해 주세요.")
    validated = []
    for upload in files:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in settings.UPLOAD_EXTENSIONS:
            raise HTTPException(415, "PNG·JPEG·PDF만 첨부할 수 있습니다.")
        blob = upload.file.read(settings.UPLOAD_MAX_BYTES + 1)
        if len(blob) > settings.UPLOAD_MAX_BYTES:
            raise HTTPException(413, "파일 용량 제한을 초과했습니다.")
        try:
            size = {}
            if suffix == ".pdf":
                pdf = PdfReader(BytesIO(blob))
                if pdf.is_encrypted:
                    raise ValueError("encrypted")
                pages = len(pdf.pages)
            else:
                with Image.open(BytesIO(blob)) as image:
                    if image.format not in {"PNG", "JPEG"}:
                        raise ValueError("unsupported image")
                    if (suffix == ".png") != (image.format == "PNG"):
                        raise ValueError("extension mismatch")
                    size = {"width": image.width, "height": image.height}
                    image.verify()
                pages = 1
            if pages < 1 or pages > settings.MAX_FILES_PER_CLAIM:
                raise ValueError("pages")
        except (ValueError, OSError, SyntaxError, PdfReadError, Image.DecompressionBombError):
            raise HTTPException(
                422, "읽을 수 없는 문서이거나 페이지 제한을 초과했습니다."
            ) from None
        file_hash = hashlib.sha256(blob).hexdigest()
        # 고객이 보낸 경로 요소는 저장 경로에 사용하지 않아 ../ 조작을 차단한다.
        target = (
            settings.UPLOAD_PATH
            / hashlib.sha256(claim.id.encode()).hexdigest()
            / (file_hash + suffix)
        )
        validated.append((target, blob, pages, size))
    existing = list(session.exec(select(Document).where(Document.claim_id == claim.id)).all())
    paths = {d.file_path: d for d in existing}
    unique = {
        str(path): (path, blob, pages, size)
        for path, blob, pages, size in validated
        if str(path) not in paths
    }
    current_pages = sum(
        file_pages(Path(doc.file_path)) if doc.source == "image" else 1 for doc in existing
    )
    if (
        len(existing) + len(unique) > settings.MAX_FILES_PER_CLAIM
        or current_pages + sum(v[2] for v in unique.values()) > settings.MAX_FILES_PER_CLAIM
    ):
        raise HTTPException(422, "청구의 최대 첨부 문서·페이지 수를 초과했습니다.")
    created_paths = []
    try:
        for path, blob, _pages, size in unique.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(blob)
                created_paths.append(path)
            doc = Document(claim_id=claim.id, file_path=str(path), page_size=size)
            session.add(doc)
            paths[str(path)] = doc
        if unique:
            session.add(
                AuditLog(
                    claim_id=claim.id,
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    action="upload",
                    detail={"document_count": len(unique)},
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        for path in created_paths:
            path.unlink(missing_ok=True)
        raise
    return [paths[str(path)] for path, _, _, _ in validated]
