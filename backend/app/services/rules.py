"""청구 단위 검토 엔진. 규칙은 결정적이며 지급 여부를 판단하지 않는다."""

import re
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, select

from app.config import Settings
from app.models import (
    Claim,
    ClaimStatus,
    CrossCheckRule,
    Document,
    DocumentStatus,
    ExtractedField,
    Issue,
    IssueKind,
    IssueStatus,
    Policy,
    RequiredDocRule,
    ReviewSettings,
)
from app.services.normalize import canonical, element_text
from app.services.source_evidence import longer_code


@dataclass
class ReviewDocument:
    """외부 API 없는 규칙 입력. 정규화값과 셀별 검수 이유를 함께 전달한다."""

    id: int
    doc_type: str
    values: dict
    fields: list[ExtractedField]
    status: DocumentStatus = DocumentStatus.EXTRACTED
    source_text: str = ""


@dataclass
class ReviewResult:
    required: list[str]
    issues: list[Issue]
    status: ClaimStatus


def evaluate_claim(
    claim: Claim,
    docs: list[ReviewDocument],
    required_rules: list[RequiredDocRule],
    cross_rules: list[CrossCheckRule],
    review_settings: ReviewSettings,
    config: Settings,
    *,
    is_proxy: bool = False,
    policy: Policy | None = None,
) -> ReviewResult:
    """현재 청구와 제출 데이터만 사용한다. 정답·기대 이슈 파일은 실행 로직에서 읽지 않는다."""
    issues: list[Issue] = []
    by_type: dict[str, list[ReviewDocument]] = defaultdict(list)
    for doc in docs:
        for field in doc.fields:
            field.review_reasons = [r for r in field.review_reasons if r != "cross_check"]
        if doc.status == DocumentStatus.EXTRACTED:
            by_type[doc.doc_type].append(doc)
    # 자기 문서의 Parse도 짧게 오독한 경우, 다른 제출 서류의 Parse를 독립 근거로 쓴다.
    source_text = " ".join(doc.source_text for doc in docs)
    for doc in docs:
        for field in doc.fields:
            if (
                field.confirmed_by is None
                and field.key == "diagnosis_code"
                and longer_code(field.value, source_text)
            ):
                field.source_found = False
                field.review_reasons = list(
                    dict.fromkeys(
                        [*field.review_reasons, "not_in_source", "원문과 다름(세분류 누락)"]
                    )
                )
    enabled = {r.id for r in cross_rules if r.enabled}

    def issue(
        kind: IssueKind,
        rule: str,
        title: str,
        detail: str,
        related: list[ReviewDocument],
        keys: list[str],
    ):
        issues.append(
            Issue(
                claim_id=claim.id,
                kind=kind,
                rule_id=rule,
                title=title,
                detail=detail,
                doc_ids=[doc.id for doc in related][:2],
                field_keys=keys,
            )
        )
        if rule.startswith("CV-"):
            for doc in related:
                for field in doc.fields:
                    if field.key in keys:
                        field.review_reasons = list(
                            dict.fromkeys([*field.review_reasons, "cross_check"])
                        )

    required = {}
    for rule in required_rules:
        if rule.claim_type not in {"common", *claim.claim_types}:
            continue
        conditions = rule.conditions
        if set(conditions.get("waived_for_channels", [])) & set(claim.channel):
            continue
        if conditions.get("is_proxy") and not is_proxy:
            continue
        if conditions.get("has_pharmacy_claim") and not (
            by_type.get("pharmacy_receipt") or by_type.get("prescription")
        ):
            continue
        for code in rule.doc_types:
            required[code] = rule.id
    surgery_docs = [
        doc
        for doc in by_type.get("medical_detail", [])
        if any(item.get("category") == "surgery" for item in doc.values.get("items", []))
    ]
    if "CV-04" in enabled and surgery_docs:
        required["surgery_cert"] = "CV-04"
    for code, rule in sorted(required.items()):
        if code not in by_type:
            issue(
                IssueKind.MISSING,
                rule,
                "수술확인서 미제출" if code == "surgery_cert" else f"필수 서류 미제출: {code}",
                f"필수 서류 {code}의 제출·처리 여부를 확인해 주세요.",
                surgery_docs if rule == "CV-04" else [],
                ["items"] if rule == "CV-04" else [],
            )

    for doc in docs:
        if doc.status != DocumentStatus.EXTRACTED:
            issue(
                IssueKind.LOW_CONF,
                "PIPELINE",
                "문서 처리 미완료",
                "실패·미처리 문서는 자동 통과할 수 없습니다.",
                [doc],
                [],
            )
        if doc.doc_type == "medical_detail" and not doc.values.get("items"):
            issue(
                IssueKind.FORMAT,
                "FIELD-items",
                "세부내역 표 확인 필요",
                "항목 표를 확인할 수 없습니다.",
                [doc],
                ["items"],
            )
        for field in doc.fields:
            if field.confirmed_by is not None:
                continue  # 사람의 확정은 모델의 low와 분리하고 교차검증에는 확정값을 사용한다.
            reasons = [
                r
                for r in field.review_reasons
                if r == "format"
                or (r == "low_conf" and review_settings.review_on_low_conf)
                or (r == "not_in_source" and review_settings.review_on_not_in_source)
            ]
            if reasons:
                reasons += [r for r in field.review_reasons if r.startswith("원문과 다름")]
                kind = IssueKind.FORMAT if "format" in reasons else IssueKind.LOW_CONF
                issue(
                    kind,
                    f"FIELD-{field.key}",
                    f"추출 항목 확인 필요: {field.key}",
                    ", ".join(reasons),
                    [doc],
                    [field.key],
                )

    # 여러 장이 있을 때 첫 장만 검사하지 않는다. 모든 관련 문서 쌍을 대조한다.
    for diagnosis in by_type.get("diagnosis", []):
        for pathology in by_type.get("pathology", []):
            a, b = diagnosis.values, pathology.values
            if "CV-01" in enabled:
                try:
                    backwards = date.fromisoformat(a["diagnosis_date"]) < date.fromisoformat(
                        b["report_date"]
                    )
                except (ValueError, KeyError, TypeError):
                    backwards = False  # 형식 오류는 FIELD 이슈가 담당한다.
                if backwards:
                    issue(
                        IssueKind.MISMATCH,
                        "CV-01",
                        "진단일이 병리 보고일보다 빠름",
                        f"진단일 {a['diagnosis_date']} · 병리 보고일 {b['report_date']}",
                        [diagnosis, pathology],
                        ["diagnosis_date", "report_date"],
                    )
            if "CV-03" in enabled:
                hints = config.KCD_PATHOLOGY_HINTS.get(a.get("diagnosis_code", ""))
                text = str(b.get("pathology_result", "")).casefold()
                specimen = str(b.get("specimen", "")).casefold()
                compatible = (
                    hints
                    and any(word in text for word in hints["result"])
                    and any(word in specimen for word in hints["specimen"])
                    and not any(word in text for word in config.KCD_PATHOLOGY_NEGATIVE)
                )
                if not compatible:
                    # 임상적 의미 전체를 이해한다고 주장하지 않는다. 제한된 시연용 참조어 대조다.
                    issue(
                        IssueKind.MISMATCH,
                        "CV-03",
                        "질병코드와 병리 진단 부합 확인 필요",
                        "시연용 질병코드·병리 참조어 기준으로 부합을 확인하지 못했습니다.",
                        [diagnosis, pathology],
                        ["diagnosis_code", "pathology_result", "specimen"],
                    )
    if "CV-02" in enabled:
        for admission in by_type.get("admission", []):
            for detail in by_type.get("medical_detail", []):
                a, b = admission.values.get("stay_days"), detail.values.get("inpatient_days")
                if isinstance(a, int) and isinstance(b, int) and a != b:
                    issue(
                        IssueKind.MISMATCH,
                        "CV-02",
                        f"입원 일수 {a}일 vs {b}일",
                        f"입퇴원확인서 {a}일 · 세부내역서 {b}일",
                        [admission, detail],
                        ["stay_days", "inpatient_days"],
                    )
    if "CV-05" in enabled:
        for doc in docs:
            name = doc.values.get("patient_name")
            if name and canonical(name) != canonical(claim.customer_name):
                issue(
                    IssueKind.MISMATCH,
                    "CV-05",
                    "환자 이름 불일치",
                    "청구 고객과 문서의 환자 이름을 확인해 주세요.",
                    [doc],
                    ["patient_name"],
                )
    if policy is not None:
        missing_riders = set(claim.claim_types) - set(policy.riders)
        if missing_riders:
            issue(
                IssueKind.MISMATCH,
                "POLICY-RIDER",
                "미가입 특약 확인 필요",
                ", ".join(sorted(missing_riders)),
                [],
                [],
            )
        if (
            "CV-06" in enabled
            and not any(d.values.get("period_start") or d.values.get("admit_date") for d in docs)
            and claim.reported_start
            and claim.reported_end
            and (
                claim.reported_start < policy.coverage_start
                or claim.reported_end > policy.coverage_end
            )
        ):
            issue(
                IssueKind.MISMATCH,
                "CV-06",
                "보장 기간 밖 진료 확인 필요",
                f"접수 진료 {claim.reported_start}~{claim.reported_end} · 보장 {policy.coverage_start}~{policy.coverage_end}",
                [],
                [],
            )
        if "CV-06" in enabled:
            for doc in docs:
                start = doc.values.get("period_start", doc.values.get("admit_date"))
                end = doc.values.get("period_end", doc.values.get("discharge_date", start))
                if start and end:
                    try:
                        outside = (
                            date.fromisoformat(start) < policy.coverage_start
                            or date.fromisoformat(end) > policy.coverage_end
                        )
                    except (TypeError, ValueError):
                        outside = False
                    if outside:
                        issue(
                            IssueKind.MISMATCH,
                            "CV-06",
                            "보장 기간 밖 진료 확인 필요",
                            f"진료 {start}~{end} · 보장 {policy.coverage_start}~{policy.coverage_end}",
                            [doc],
                            ["period_start", "period_end", "admit_date", "discharge_date"],
                        )
    status = ClaimStatus.AUTO_PASS
    if any(i.kind == IssueKind.MISSING for i in issues):
        status = ClaimStatus.SUPPLEMENT
    elif issues:
        status = ClaimStatus.NEEDS_REVIEW
    return ReviewResult(sorted(required), issues, status)


def set_nested(values: dict, key: str, value):
    """평탄화된 셀 경로를 원래 표 구조에 반영한다. 임의 속성을 만들지 않는다."""
    parts = re.findall(r"[^.\[\]]+", key)
    node = values
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    last = int(parts[-1]) if isinstance(node, list) else parts[-1]
    node[last] = value


def review_from_db(session: Session, claim: Claim, config: Settings) -> ReviewResult:
    """저장된 정규화 데이터로 재검사한다. 같은 이슈는 재생성하지 않아 확인 이력을 보존한다."""
    docs = session.exec(select(Document).where(Document.claim_id == claim.id)).all()
    inputs = [
        ReviewDocument(
            doc.id,
            doc.doc_type,
            deepcopy(doc.raw_result.get("normalized", {})),
            list(
                session.exec(
                    select(ExtractedField).where(ExtractedField.document_id == doc.id)
                ).all()
            ),
            doc.status,
            " ".join(
                element_text(el) for el in doc.raw_result.get("parse", {}).get("elements", [])
            ),
        )
        for doc in docs
    ]
    for doc in inputs:
        for field in doc.fields:
            if field.confirmed_by is not None and field.confirmed_value is not None:
                from app.services.normalize import normal_scalar

                set_nested(doc.values, field.key, normal_scalar(field.key, field.confirmed_value))
    settings = session.get(ReviewSettings, 1)
    if settings is None:
        raise ValueError("검토 설정 시드가 필요합니다.")
    report = evaluate_claim(
        claim,
        inputs,
        list(session.exec(select(RequiredDocRule)).all()),
        list(session.exec(select(CrossCheckRule)).all()),
        settings,
        config,
        policy=session.get(Policy, claim.policy_no),
    )
    existing = list(session.exec(select(Issue).where(Issue.claim_id == claim.id)).all())

    def fingerprint(item):
        return (item.rule_id, item.kind, tuple(item.doc_ids), tuple(item.field_keys))

    current = {fingerprint(item): item for item in report.issues}
    old = {fingerprint(item): item for item in existing}
    for fp, item in current.items():
        if fp not in old:
            session.add(item)
        else:
            if old[fp].detail != item.detail:
                old[fp].status = IssueStatus.OPEN
                old[fp].resolved_by = None
                old[fp].resolved_at = None
            old[fp].detail = item.detail
            old[fp].title = item.title
            session.add(old[fp])
    for fp, item in old.items():
        if fp not in current and item.rule_id.startswith(("CV-", "REQ-", "FIELD-", "PIPELINE")):
            item.status = IssueStatus.RESOLVED
            session.add(item)
    for doc in inputs:
        session.add_all(doc.fields)
    session.flush()
    open_issues = session.exec(
        select(Issue).where(Issue.claim_id == claim.id, Issue.status == IssueStatus.OPEN)
    ).all()
    claim.status = (
        ClaimStatus.SUPPLEMENT
        if any(i.kind == IssueKind.MISSING for i in open_issues)
        else ClaimStatus.NEEDS_REVIEW
        if open_issues
        else ClaimStatus.AUTO_PASS
    )
    # 문서가 하나도 없으면 수동 확인만으로 자동 통과하지 않는다.
    if not docs:
        claim.status = ClaimStatus.SUPPLEMENT
    report.status = claim.status
    session.add(claim)
    session.flush()
    return report
