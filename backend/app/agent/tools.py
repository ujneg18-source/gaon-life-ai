"""모델이 호출하는 읽기 도구. 모든 청구 ID마다 배정 권한을 검사하고 개인정보는 최소화한다."""

import logging
import re

from fastapi import HTTPException
from pydantic import Field
from sqlmodel import select

from app.auth import require_claim_access
from app.models import (
    ActorType,
    AuditLog,
    Claim,
    Customer,
    Document,
    Issue,
    IssueStatus,
    Policy,
    Role,
)
from app.schemas.chat import StrictModel
from app.services.coverage import check_coverage, citation
from app.services.presentation import document_label
from app.services.workspace import detail, review_input


class SearchArgs(StrictModel):
    query: str = Field(min_length=1, max_length=2000)
    collection: str | None


class ClaimArgs(StrictModel):
    customer_name: str | None
    claim_id: str | None


class IdArgs(StrictModel):
    claim_id: str


class FieldsArgs(IdArgs):
    doc_type: str


class ItemArgs(IdArgs):
    item_name: str = Field(min_length=1, max_length=120)


class DraftArgs(IdArgs):
    doc_types: list[str] = Field(max_length=10)


ARG_MODELS = {
    "search_kb": SearchArgs,
    "get_claim": ClaimArgs,
    "get_claim_issues": IdArgs,
    "get_document_fields": FieldsArgs,
    "check_item_coverage": ItemArgs,
    "draft_supplement": DraftArgs,
}
DESCRIPTIONS = {
    "search_kb": "약관·매뉴얼 근거 검색. 지급 여부나 금액 판단은 하지 않는다.",
    "get_claim": "고객 이름 또는 청구번호로 배정 범위 내 청구를 찾는다. 동명이인은 모두 반환한다.",
    "get_claim_issues": "청구의 저장된 누락·불일치·안내·확인 필요 결과 조회.",
    "get_document_fields": "저장된 문서의 정규화/담당자 확정값 조회.",
    "check_item_coverage": "약제비 항목을 처방전·비급여 기준과 대조해 가능성만 제시.",
    "draft_supplement": "표준 템플릿에 고객명과 누락 서류를 채운다. 실제 발송 없음.",
}


class Tools:
    def __init__(self, session, user, config, kb):
        self.session, self.user, self.config, self.kb = session, user, config, kb
        self.reads = set()

    def claim(self, claim_id):
        claim = require_claim_access(claim_id, self.user, self.session)
        if claim_id not in self.reads:
            self.session.add(
                AuditLog(
                    claim_id=claim_id,
                    actor_type=ActorType.USER,
                    actor_id=self.user.id,
                    action="chat_read",
                    detail={"scope": "claim_review"},
                )
            )
            self.reads.add(claim_id)
        return claim

    def search_kb(self, query, collection=None):
        return self.kb.search(query, collection)

    def get_claim(self, customer_name=None, claim_id=None):
        query = select(Claim)
        if claim_id:
            rows = [self.claim(claim_id)]
        else:
            if not customer_name:
                return []
            query = query.where(Claim.customer_name == customer_name)
            if self.user.role != Role.ADMIN:
                query = query.where(Claim.assignee_id == self.user.id)
            rows = list(self.session.exec(query).all())
        result = []
        for row in rows:
            self.claim(row.id)
            customer = self.session.get(Customer, row.customer_id)
            policy = self.session.get(Policy, row.policy_no)
            view = detail(self.session, row, self.config)
            result.append(
                {
                    "claim_id": row.id,
                    "customer_name": row.customer_name,
                    "birth_date": str(customer.birth_date) if customer else None,
                    "policy": {
                        "product_name": policy.product_name,
                        "contract_date": str(policy.contract_date)
                        if policy.contract_date
                        else None,
                        "riders": policy.riders,
                        "coverage_start": str(policy.coverage_start),
                        "coverage_end": str(policy.coverage_end),
                    }
                    if policy
                    else None,
                    "submitted_count": view["submitted_count"],
                    "required_count": view["required_count"],
                    "status": view["status"],
                }
            )
        return result

    def get_workload(self):
        """담당 범위의 상태 집계만 반환해 전체 고객 명단을 모델에 제공하지 않는다."""
        from collections import Counter

        from app.models import ClaimStatus

        query = select(Claim)
        if self.user.role != Role.ADMIN:
            query = query.where(Claim.assignee_id == self.user.id)
        counts = Counter(
            detail(self.session, row, self.config)["status"]
            for row in self.session.exec(query).all()
        )
        needs = counts[ClaimStatus.NEEDS_REVIEW]
        supplement = counts[ClaimStatus.SUPPLEMENT]
        return {"needs_review": needs, "supplement": supplement, "total": needs + supplement}

    def get_claim_issues(self, claim_id):
        self.claim(claim_id)
        return [
            i.model_dump(mode="json")
            for i in self.session.exec(
                select(Issue).where(Issue.claim_id == claim_id, Issue.status == IssueStatus.OPEN)
            ).all()
        ]

    def documents(self, claim_id):
        self.claim(claim_id)
        return [
            review_input(self.session, d)
            for d in self.session.exec(select(Document).where(Document.claim_id == claim_id)).all()
        ]

    def get_document_fields(self, claim_id, doc_type):
        return [
            {"doc_type": d.doc_type, "values": d.values}
            for d in self.documents(claim_id)
            if d.doc_type == doc_type
        ]

    def check_item_coverage(self, claim_id, item_name):
        return check_coverage(self.documents(claim_id), item_name, self.kb)

    def draft_supplement(self, claim_id, doc_types):
        claim = self.claim(claim_id)
        if hasattr(self.kb, "lookup"):
            hits = self.kb.lookup("11_supplement_templates.md", "2장")
        else:
            hits = self.kb.search("보완 요청 표준 문구 서류별 문구", "manual", limit=12)
        templates = [
            h
            for h in hits
            if h["source_path"].endswith("11_supplement_templates.md") and h["article"] == "2장"
        ]
        if not templates:
            return {"message": "관련 규정을 찾지 못했어요", "citations": []}
        text = templates[0]["chunk_text"]
        missing = self.get_claim_issues(claim_id)
        allowed = set()
        for issue in missing:
            if issue["kind"] == "missing":
                if issue["rule_id"] == "CV-04":
                    allowed.add("surgery_cert")
                else:
                    allowed.update(
                        code
                        for code in self.config.UPSTAGE_DOC_CLASSES
                        if document_label(code, self.config) in issue["title"]
                    )
        chosen = doc_types or sorted(allowed)
        if not chosen:
            return {
                "message": "추가로 요청할 누락 서류가 없어요. 요청할 서류명을 말씀해 주세요.",
                "citations": [],
                "draft_text": None,
            }
        messages = []
        for code in chosen:
            title = document_label(code, self.config)
            match = re.search(
                r"### " + re.escape(title) + r"[^\n]*\n(.*?)(?=\n### |\Z)", text, re.DOTALL
            )
            if not match:
                return {
                    "message": "이 서류의 보완 요청 템플릿은 없어요. 사용할 수 있는 서류는 "
                    + ", ".join(re.findall(r"^### (.+)$", text, re.MULTILINE))
                    + "예요.",
                    "citations": [],
                    "draft_text": None,
                }
            messages.append(
                match.group(1).strip().replace("{고객명}", claim.customer_name).replace("**", "")
            )
        return {
            "message": "\n\n".join(messages),
            "draft_text": "\n\n".join(messages),
            "submitted": [
                document_label(code, self.config)
                for code in chosen
                if any(d.doc_type == code for d in self.documents(claim_id))
            ],
            "customer_name": claim.customer_name,
            "citations": [citation(templates[0]).model_dump()],
        }

    def call(self, name, args):
        if name not in ARG_MODELS:
            raise ValueError("허용되지 않은 도구")
        values = ARG_MODELS[name].model_validate(args).model_dump()
        return getattr(self, name)(**values)

    def call_with_retry(self, name, args):
        """Pydantic/일시 오류는 한 번만 재시도한다. 로그에는 입력·의료정보를 남기지 않는다."""
        for attempt in range(2):
            try:
                return self.call(name, args)
            except HTTPException as exc:
                if exc.status_code == 403:
                    raise  # 권한 거절을 일반 조회 실패로 감추지 않는다.
                error = f"HTTP{exc.status_code}"
            except (ValueError, TypeError, RuntimeError) as exc:
                error = type(exc).__name__
            logging.getLogger(__name__).warning(
                "tool_failure tool=%s attempt=%s error=%s", name, attempt + 1, error
            )
            if hasattr(self, "tool_errors"):
                self.tool_errors.append({"tool": name, "attempt": attempt + 1, "error": error})
        raise RuntimeError("확인하지 못했어요")

    def claim_evidence(self, message, issues):
        """청구 사실은 DB에서, 판단 근거는 실행된 규칙 주소에서만 읽는다. 일반 RAG는 금지다."""
        from app.agent.kb import load_chunks

        chunks = [c.payload() for c in load_chunks(self.config.KB_PATH)]

        def lookup(path, article, term=""):
            matches = [
                h
                for h in chunks
                if h["source_path"].endswith(path)
                and h["article"] == article
                and term in h["chunk_text"]
            ]
            return matches[:1]

        focus = None
        for name, pattern in self.config.CLAIM_FOCUS_PATTERNS.items():
            if re.search(pattern, message):
                focus = name
                break
        active = {i["rule_id"] for i in issues}
        focus_rules = self.config.CLAIM_FOCUS_RULES.get(focus, [])
        if focus_rules:
            active &= set(focus_rules)
        hits = []
        if focus:
            for rule in focus_rules:
                if rule in active:
                    for path, article, term in self.config.CLAIM_RULE_SOURCES.get(rule, []):
                        hits += lookup(path, article, term)
        else:
            # 전체 검토는 필수서류/교차검증을 먼저 제시한다. 청구 지급 심사를 새로 하지 않는다.
            if any(i["kind"] == "missing" for i in issues):
                hits += lookup("10_claims_manual.md", "2장", "수술비" if "CV-04" in active else "")
            hits += lookup("10_claims_manual.md", "4장", "CV-01" if "CV-01" in active else "")
            for rule in sorted(active):
                for path, article, term in self.config.CLAIM_RULE_SOURCES.get(rule, []):
                    hits += lookup(path, article, term)
        return list({h["node_id"]: h for h in hits}.values())
