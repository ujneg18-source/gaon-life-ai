"""실손24의 전자 문서를 모의 연결한다. 실제 외부 수신·개인정보 조회는 하지 않는다."""

import json
from pathlib import Path

from fastapi import HTTPException
from sqlmodel import Session, select

from app.config import Settings
from app.models import ActorType, AuditLog, Claim, Document, DocumentSource
from app.services.upstage import file_pages


def attach_silson24(
    session: Session, claim: Claim, settings: Settings, actor_id: int
) -> list[Document]:
    """가상 표시와 청구 ID가 맞는 데이터만 연결하며 재요청에서도 중복 생성하지 않는다."""
    payloads = []
    for path in sorted(settings.MOCK_SILSON24_PATH.glob("*.json")):
        data = json.loads(path.read_text())
        if data.get("claim_id") == claim.id and data.get("is_mock") is True:
            payloads.append((path, data))
    if not payloads:
        raise HTTPException(404, "이 청구에 연결할 실손24 모의 데이터가 없습니다.")
    existing = session.exec(select(Document).where(Document.claim_id == claim.id)).all()
    paths = {doc.file_path: doc for doc in existing}
    new = [(path, data) for path, data in payloads if str(path) not in paths]
    current_pages = sum(
        file_pages(Path(doc.file_path)) if doc.source == DocumentSource.IMAGE else 1
        for doc in existing
    )
    if (
        len(existing) + len(new) > settings.MAX_FILES_PER_CLAIM
        or current_pages + len(new) > settings.MAX_FILES_PER_CLAIM
    ):
        raise HTTPException(422, "청구의 최대 첨부 문서 수를 초과합니다.")
    for path, data in new:
        doc = Document(
            claim_id=claim.id,
            doc_type=data["doc_type"],
            source=DocumentSource.SILSON24,
            file_path=str(path),
            raw_result={"data": data},
        )
        session.add(doc)
        paths[str(path)] = doc
    if new:
        # 전자 데이터의 신뢰도는 AI confidence로 꾸미지 않는다. 후속 정규화는 method=data다.
        claim.channel = list(dict.fromkeys([*claim.channel, "silson24"]))
        session.add(claim)
        session.add(
            AuditLog(
                claim_id=claim.id,
                actor_type=ActorType.USER,
                actor_id=actor_id,
                action="silson24_receive",
                detail={"document_count": len(new), "is_mock": True},
            )
        )
    session.commit()
    return [paths[str(path)] for path, _ in payloads]
