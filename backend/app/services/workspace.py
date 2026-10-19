"""화면용 읽기 모델. 숫자는 저장 데이터와 현재 규칙에서 계산하며 경로·원본 응답은 숨긴다."""

import json
import math
from copy import deepcopy

from sqlmodel import Session, select

from app.models import (
    Claim,
    ClaimStatus,
    CrossCheckRule,
    Customer,
    Document,
    ExtractedField,
    Issue,
    IssueKind,
    IssueStatus,
    KcdCode,
    Policy,
    RequiredDocRule,
    ReviewSettings,
)
from app.services.claim_status import claim_status
from app.services.normalize import element_text, normal_scalar
from app.services.rules import (
    ReviewDocument,
    ReviewResult,
    evaluate_claim,
    required_documents,
    set_nested,
)


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
        doc.source,
    )

    # 확정값을 읽기 전용 입력에도 반영해 필수 서류 집계와 재검사 결과가 같게 한다.
    for field in result.fields:
        if field.confirmed_by is not None and field.confirmed_value is not None:
            set_nested(result.values, field.key, normal_scalar(field.key, field.confirmed_value))
    return result


def field_confidences(raw):
    """Extract choice의 JSON 문자열 점수를 펼친다. 분류 점수/_ctx와 혼동하지 않는다."""
    from app.services.normalize import flatten

    try:
        score = raw.get("extract", {}).get("choices", [{}])[0].get("confidence_score", {})
        if isinstance(score, str):
            score = json.loads(score)
        if not isinstance(score, dict):
            return {}
        return {
            key.removesuffix("._value"): value
            for key, value in flatten(score).items()
            if key.endswith("._value")
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and 0 <= value <= 1
        }
    except (ValueError, TypeError, IndexError, AttributeError):
        return {}


def detail(session: Session, claim: Claim, config, *, summary: bool = False):
    docs = list(
        session.exec(
            select(Document).where(Document.claim_id == claim.id).order_by(Document.id)
        ).all()
    )
    policy = session.get(Policy, claim.policy_no)
    customer = session.get(Customer, claim.customer_id)
    required_rules = list(session.exec(select(RequiredDocRule)).all())
    cross_rules = list(session.exec(select(CrossCheckRule)).all())
    # 조회도 빈 청구의 엔진 실행을 피한다. 필수서류 목록만 계산한다.
    report = (
        evaluate_claim(
            claim,
            [review_input(session, d) for d in docs],
            required_rules,
            cross_rules,
            session.get(ReviewSettings, 1),
            config,
            policy=policy,
        )
        if docs
        else ReviewResult(
            sorted(required_documents(claim, required_rules, {})), [], ClaimStatus.PENDING
        )
    )
    issues = list(
        session.exec(select(Issue).where(Issue.claim_id == claim.id).order_by(Issue.id)).all()
    )
    result = {
        **claim.model_dump(mode="json"),
        "status": claim_status(
            claim, docs, issues, [i for i in report.issues if i.kind == IssueKind.MISSING]
        ),
        "customer": customer.model_dump(mode="json") if customer else None,
        "policy": policy.model_dump(mode="json") if policy else None,
        "development_origin": (
            "실제 API + mock"
            if any(d.provenance == "upstage" for d in docs)
            and any(d.provenance == "mock" for d in docs)
            else "실제 API"
            if any(d.provenance == "upstage" for d in docs)
            else "mock"
            if any(d.provenance == "mock" for d in docs)
            else "실손24 모의"
            if docs and all(d.provenance == "silson24" for d in docs)
            else "미처리"
        )
        if config.SHOW_DEV_BADGE and not config.DEMO_MODE
        else None,
        "submitted_count": len(docs),
        "required_count": len(report.required),
        "required": report.required,
        "documents": [
            {
                "id": d.id,
                "doc_type": d.doc_type,
                "source": d.source,
                "provenance": d.provenance,
                "status": d.status,
                "page_size": d.page_size,
            }
            for d in docs
        ],
        "issues": [i.model_dump(mode="json") for i in issues],
        "open_issue_count": sum(
            i.status == IssueStatus.OPEN and i.kind != IssueKind.INFO for i in issues
        ),
    }
    if summary:
        return result

    fields = []
    for doc in docs:
        scores = field_confidences(doc.raw_result)
        for f in session.exec(
            select(ExtractedField).where(ExtractedField.document_id == doc.id)
        ).all():
            fields.append(
                {
                    **f.model_dump(mode="json"),
                    "confidence_score": scores.get(f.key) if f.method.value != "data" else None,
                    "doc_type": doc.doc_type,
                    "provenance": doc.provenance,
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
    from app.agent.claim_answer import render_claim

    display_issues = render_claim(
        {"customer_name": claim.customer_name, "claim_id": claim.id, "submitted_count": len(docs)},
        [i.model_dump(mode="json") for i in issues if i.status == IssueStatus.OPEN],
        [review_input(session, d) for d in docs],
        config,
        as_rows=True,
    )
    return {
        **result,
        "display_issues": display_issues,
        "comparisons": comparisons(
            claim,
            [review_input(session, d) for d in docs],
            policy,
            report.issues,
            config,
            {rule.id for rule in cross_rules if rule.enabled},
        ),
        "fields": fields,
    }


def comparisons(claim, docs, policy, issues, config, enabled):
    """실제 대조 가능한 값과 서류 쌍만 표시하고 없는 값을 일치로 꾸미지 않는다."""
    from itertools import combinations

    from app.services.presentation import document_label

    rows = []
    if not docs:
        return rows

    def cell(doc, key):
        return {
            "document_id": doc.id,
            "doc_name": document_label(doc.doc_type, config),
            "key": key,
            "value": str(doc.values.get(key, "미기재")),
        }

    def add(title, a, b, result=None):
        if not result:
            result = "match" if a["value"] == b["value"] else "mismatch"
        rows.append({"title": title, "a": a, "b": b, "result": result})

    # 환자명은 제출 서류의 실제 값끼리 대조한다.
    named = [d for d in docs if d.values.get("patient_name")]
    for doc in named if "CV-05" in enabled else []:
        add(
            "환자명",
            {
                "document_id": None,
                "doc_name": "청구 접수정보",
                "key": "patient_name",
                "value": claim.customer_name,
            },
            cell(doc, "patient_name"),
        )
    for key, title in [
        ("diagnosis_code", "질병분류기호"),
        ("surgery_date", "수술일"),
        ("admit_date", "입원일"),
        ("discharge_date", "퇴원일"),
    ]:
        rule = "CV-03" if key == "diagnosis_code" else "CV-04" if key == "surgery_date" else "CV-02"
        present = [d for d in docs if d.values.get(key)] if rule in enabled else []
        for a, b in combinations(present, 2):
            add(title, cell(a, key), cell(b, key))
    for a in [d for d in docs if d.doc_type == "admission" and "CV-02" in enabled]:
        for b in [d for d in docs if d.doc_type == "medical_detail"]:
            x, y = a.values.get("stay_days"), b.values.get("inpatient_days")
            if isinstance(x, int) and isinstance(y, int):
                result = "match" if x == y else "info" if abs(x - y) == 1 else "mismatch"
                if any(i.rule_id == "CV-02" and i.kind == IssueKind.MISMATCH for i in issues):
                    result = "mismatch"
                add("입원일수", cell(a, "stay_days"), cell(b, "inpatient_days"), result)
    for a in [d for d in docs if d.doc_type == "diagnosis" and "CV-01" in enabled]:
        for b in [d for d in docs if d.doc_type == "pathology"]:
            if a.values.get("diagnosis_date") and b.values.get("report_date"):
                add(
                    "진단일과 병리 보고일",
                    cell(a, "diagnosis_date"),
                    cell(b, "report_date"),
                    "mismatch" if any(i.rule_id == "CV-01" for i in issues) else "match",
                )
    if "CV-03" in enabled:
        for diagnosis in [
            d for d in docs if d.doc_type == "diagnosis" and d.values.get("diagnosis_code")
        ]:
            for pathology in [d for d in docs if d.doc_type == "pathology"]:
                relevant = any(
                    i.rule_id == "CV-03" and diagnosis.id in i.doc_ids and pathology.id in i.doc_ids
                    for i in issues
                )
                add(
                    "질병분류기호와 병리 진단명",
                    cell(diagnosis, "diagnosis_code"),
                    cell(pathology, "pathology_result"),
                    "mismatch"
                    if relevant
                    else "match"
                    if pathology.values.get("pathology_result")
                    else "na",
                )
    if policy and "CV-06" in enabled:
        # 엔진과 같이 진료/입퇴원 기간의 양 끝을 검사한다. 진단일 하나로
        # 기간 전체의 일치를 주장하거나 퇴원일의 보장 초과를 놓치지 않는다.
        if claim.reported_start and claim.reported_end:
            add(
                "접수 진료 기간",
                {
                    "document_id": None,
                    "doc_name": "청구 접수정보",
                    "key": "reported_period",
                    "value": f"{claim.reported_start} ~ {claim.reported_end}",
                },
                {
                    "document_id": None,
                    "doc_name": "보험 계약",
                    "key": "coverage",
                    "value": f"{policy.coverage_start} ~ {policy.coverage_end}",
                },
                "match"
                if claim.reported_start >= policy.coverage_start
                and claim.reported_end <= policy.coverage_end
                else "mismatch",
            )
        for d in docs:
            start_key = "period_start" if d.values.get("period_start") else "admit_date"
            end_key = "period_end" if d.values.get("period_end") else "discharge_date"
            start, end = d.values.get(start_key), d.values.get(end_key, d.values.get(start_key))
            if start and end:
                from datetime import date

                try:
                    result = (
                        "match"
                        if date.fromisoformat(start) >= policy.coverage_start
                        and date.fromisoformat(end) <= policy.coverage_end
                        else "mismatch"
                    )
                except (TypeError, ValueError):
                    result = "na"
                a = cell(d, start_key)
                a["value"] = f"{start} ~ {end}"
                add(
                    "보장 기간",
                    a,
                    {
                        "document_id": None,
                        "doc_name": "보험 계약",
                        "key": "coverage",
                        "value": f"{policy.coverage_start} ~ {policy.coverage_end}",
                    },
                    result,
                )
    return sorted(rows, key=lambda r: {"mismatch": 0, "info": 1, "match": 2, "na": 3}[r["result"]])
