"""미리 작성한 안내 양식에 실제 청구 정보만 채운다. 외부 AI/문자 발송은 하지 않는다."""

import json
from datetime import UTC
from zoneinfo import ZoneInfo

from app.auth import require_claim_access
from app.models import Policy
from app.services.presentation import document_label


def claim_supplement_draft(session, user, config, claim_id, doc_types):
    """서버가 검증한 누락 서류에만 발급 안내를 붙이고 금액·기한은 만들어 넣지 않는다."""
    claim = require_claim_access(claim_id, user, session)
    policy = session.get(Policy, claim.policy_no)
    templates = json.loads(config.SUPPLEMENT_MESSAGE_TEMPLATES.read_text())
    documents = []
    for index, code in enumerate(doc_types, 1):
        entry = templates["documents"].get(code)
        if not entry:
            return {"message": "이 서류의 안내 양식이 준비되지 않았어요.", "draft_text": None}
        documents.append(
            f"{index}. {document_label(code, config)}\n"
            f"발급·준비처: {entry['issuer']}\n확인 사항: {entry['description']}"
        )
    received = claim.received_at
    if received.tzinfo is None:
        received = received.replace(tzinfo=UTC)
    message = templates["message"].format(
        customer_name=claim.customer_name,
        claim_id=claim.id,
        product_name=policy.product_name if policy else "가입 상품 확인 필요",
        claim_types=", ".join(config.CLAIM_TYPE_LABELS.get(t, t) for t in claim.claim_types),
        received_date=received.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y.%m.%d"),
        document_count=len(doc_types),
        document_details="\n\n".join(documents),
    )
    if not doc_types or len(message) > config.SUPPLEMENT_MAX_CHARS:
        return {"message": "요청할 서류와 안내 문구 길이를 확인해 주세요.", "draft_text": None}
    return {"message": message, "draft_text": message, "customer_name": claim.customer_name}
