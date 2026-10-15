"""화면용 읽기 모델. 숫자는 저장 데이터와 현재 규칙에서 계산하며 경로·원본 응답은 숨긴다."""

from copy import deepcopy

from sqlmodel import Session, select

from app.models import (
    Claim,
    CrossCheckRule,
    Customer,
    Document,
    ExtractedField,
    Issue,
    IssueStatus,
    KcdCode,
    Policy,
    RequiredDocRule,
    ReviewSettings,
)
from app.services.normalize import element_text, normal_scalar
from app.services.rules import ReviewDocument, evaluate_claim, set_nested


def review_input(session, doc):
    result = ReviewDocument(
        doc.id,
        doc.doc_type,
        deepcopy(doc.raw_result.get("normalized", {})),
        [
            ExtractedField(**f.model_dump())
            for f in session.exec(
                select(ExtractedField).where(ExtractedField.document_id == doc.id)
            ).all()
        ],
        doc.status,
        " ".join(element_text(el) for el in doc.raw_result.get("parse", {}).get("elements", [])),
    )

    # 확정값을 읽기 전용 입력에도 반영해 필수 서류 집계와 재검사 결과가 같게 한다.
    for field in result.fields:
        if field.confirmed_by is not None and field.confirmed_value is not None:
            set_nested(result.values, field.key, normal_scalar(field.key, field.confirmed_value))
    return result


def detail(session: Session, claim: Claim, config):
    docs = list(
        session.exec(
            select(Document).where(Document.claim_id == claim.id).order_by(Document.id)
        ).all()
    )
    policy = session.get(Policy, claim.policy_no)
    customer = session.get(Customer, claim.customer_id)
    report = evaluate_claim(
        claim,
        [review_input(session, d) for d in docs],
        list(session.exec(select(RequiredDocRule)).all()),
        list(session.exec(select(CrossCheckRule)).all()),
        session.get(ReviewSettings, 1),
        config,
        policy=policy,
    )
    issues = list(
        session.exec(select(Issue).where(Issue.claim_id == claim.id).order_by(Issue.id)).all()
    )
    fields = []
    for doc in docs:
        for f in session.exec(
            select(ExtractedField).where(ExtractedField.document_id == doc.id)
        ).all():
            fields.append(
                {
                    **f.model_dump(mode="json"),
                    "doc_type": doc.doc_type,
                    "source": doc.source,
                    "display_value": f.confirmed_value
                    if f.confirmed_value is not None
                    else f.value,
                    "kcd_name": (
                        session.get(KcdCode, f.confirmed_value or f.value).name
                        if f.key == "diagnosis_code"
                        and session.get(KcdCode, f.confirmed_value or f.value)
                        else doc.raw_result.get("kcd_names", {}).get(f.key)
                    ),
                    "parse_evidence": doc.raw_result.get("parse_evidence", {}).get(f.key),
                }
            )
    return {
        **claim.model_dump(mode="json"),
        "customer": customer.model_dump(mode="json") if customer else None,
        "policy": policy.model_dump(mode="json") if policy else None,
        "submitted_count": len(docs),
        "required_count": len(report.required),
        "required": report.required,
        "documents": [
            {
                "id": d.id,
                "doc_type": d.doc_type,
                "source": d.source,
                "status": d.status,
                "page_size": d.page_size,
            }
            for d in docs
        ],
        "issues": [i.model_dump(mode="json") for i in issues],
        "fields": fields,
        "open_issue_count": sum(i.status == IssueStatus.OPEN for i in issues),
    }
