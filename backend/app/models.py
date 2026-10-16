"""청구 검토 도메인의 저장 객체. JSON 배열은 행별 factory로 만들어 공유를 방지한다.

Claim은 처리 단위, Document는 원본, ExtractedField는 AI 값과 사람의 확정값,
Issue는 담당자 확인 과제다. 규칙 테이블은 정의를 저장하며 services/rules.py가 실행한다.
"""

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, Index, text
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """로그·접수 시간은 UTC로 저장하고 화면에서 한국 시간으로 표시한다."""
    return datetime.now(UTC)


class Role(StrEnum):
    REVIEWER = "reviewer"
    ADMIN = "admin"


class ClaimStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    AUTO_PASS = "auto_pass"
    NEEDS_REVIEW = "needs_review"
    SUPPLEMENT = "supplement"
    TO_PAYMENT_REVIEW = "to_payment_review"


class DocumentType(StrEnum):
    DIAGNOSIS = "diagnosis"
    PATHOLOGY = "pathology"
    ADMISSION = "admission"
    SURGERY_CERT = "surgery_cert"
    MEDICAL_RECEIPT = "medical_receipt"
    MEDICAL_DETAIL = "medical_detail"
    PRESCRIPTION = "prescription"
    OUTPATIENT = "outpatient"
    PHARMACY_RECEIPT = "pharmacy_receipt"
    IMAGING_REPORT = "imaging_report"
    DISABILITY = "disability"
    DEATH_CERT = "death_cert"
    CLAIM_FORM = "claim_form"
    ID_COPY = "id_copy"
    BANKBOOK = "bankbook"
    FAMILY_CERT = "family_cert"
    BASIC_CERT = "basic_cert"
    POA = "poa"
    SEAL_CERT = "seal_cert"
    CONSENT = "consent"
    ACCIDENT_REPORT = "accident_report"
    ACCIDENT_STATEMENT = "accident_statement"
    MEDICAL_RECORD = "medical_record"
    OTHER = "other"


class DocumentSource(StrEnum):
    IMAGE = "image"
    SILSON24 = "silson24"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    EXTRACTED = "extracted"
    FAILED = "failed"


class Confidence(StrEnum):
    HIGH = "high"
    LOW = "low"


class FieldMethod(StrEnum):
    PARSE = "parse"
    OCR = "ocr"
    DATA = "data"


class IssueKind(StrEnum):
    INFO = "info"
    MISSING = "missing"
    MISMATCH = "mismatch"
    LOW_CONF = "low_conf"
    EXCLUDED_ITEM = "excluded_item"
    FORMAT = "format"


class IssueStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"


class SupplementChannel(StrEnum):
    KAKAO = "kakao"
    SMS = "sms"


class SupplementStatus(StrEnum):
    DRAFT = "draft"
    SENT_MOCK = "sent_mock"
    RECEIVED = "received"


class ActorType(StrEnum):
    CUSTOMER = "customer"
    AI = "ai"
    USER = "user"


class User(SQLModel, table=True):
    """데모 로그인 사용자. 비밀번호는 없고 역할은 서버 DB를 기준으로 판단한다."""

    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    role: Role


class Customer(SQLModel, table=True):
    """동명이인은 별도 고객 ID로 구분한다. 시드는 명시적으로 가상 정보만 저장한다."""

    __tablename__ = "customers"
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    birth_date: date
    contact: str
    is_mock: bool = True


class Policy(SQLModel, table=True):
    """고객과 보장 기간·가입 특약을 연결한다. 코드의 적합성 검사는 지급 결정이 아니다."""

    __tablename__ = "policies"
    policy_no: str = Field(primary_key=True)
    customer_id: str = Field(foreign_key="customers.id", index=True)
    product_name: str
    riders: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    coverage_start: date
    coverage_end: date
    is_mock: bool = True


class Claim(SQLModel, table=True):
    """여러 문서와 보장 종류를 묶는 청구 단위. auto_pass는 지급 승인이 아니다."""

    __tablename__ = "claims"
    id: str = Field(primary_key=True)
    customer_name: str
    review_note: str = ""
    reported_start: date | None = None
    reported_end: date | None = None
    policy_no: str = Field(foreign_key="policies.policy_no")
    customer_id: str | None = Field(default=None, foreign_key="customers.id", index=True)
    claim_types: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    received_at: datetime = Field(default_factory=utc_now)
    channel: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    status: ClaimStatus = ClaimStatus.PENDING
    assignee_id: int = Field(foreign_key="users.id", index=True)
    step: int = Field(default=0, ge=0, le=3)


class Document(SQLModel, table=True):
    """청구에 첨부된 원본과 처리 결과. 경로·JSON은 후속 파이프라인이 채운다."""

    __tablename__ = "documents"
    id: int | None = Field(default=None, primary_key=True)
    claim_id: str = Field(foreign_key="claims.id", index=True)
    doc_type: DocumentType = DocumentType.OTHER
    source: DocumentSource = DocumentSource.IMAGE
    file_path: str
    classify_conf: float | None = Field(default=None, ge=0, le=1)
    page_size: dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON))
    status: DocumentStatus = DocumentStatus.UPLOADED
    raw_result: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class ExtractedField(SQLModel, table=True):
    """AI 추출 원문·정규화값·담당자 확정값을 분리해 수정 근거를 보존한다."""

    __tablename__ = "fields"
    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id", index=True)
    key: str
    value: str
    raw_value: str
    extract_conf: Confidence | None = None
    source_found: bool = False
    review_reasons: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    method: FieldMethod
    page: int = Field(default=1, ge=1)
    bbox: list[dict[str, float]] | None = Field(default=None, sa_column=Column(JSON))
    confirmed_value: str | None = None
    confirmed_by: int | None = Field(default=None, foreign_key="users.id")


class Issue(SQLModel, table=True):
    """규칙에서 발생한 확인 과제. evidence는 표시용 근거이며 지급 결정을 의미하지 않는다."""

    __tablename__ = "issues"
    id: int | None = Field(default=None, primary_key=True)
    claim_id: str = Field(foreign_key="claims.id", index=True)
    kind: IssueKind
    rule_id: str
    title: str
    detail: str
    doc_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    field_keys: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    evidence: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    status: IssueStatus = IssueStatus.OPEN
    resolved_by: int | None = Field(default=None, foreign_key="users.id")
    resolved_at: datetime | None = None


class SupplementRequest(SQLModel, table=True):
    """고객 보완 요청 초안과 모의 전송 상태. 외부 메시지를 보내는 객체가 아니다."""

    __tablename__ = "supplement_requests"
    id: int | None = Field(default=None, primary_key=True)
    claim_id: str = Field(foreign_key="claims.id", index=True)
    doc_types: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    channel: SupplementChannel = SupplementChannel.KAKAO
    message: str
    status: SupplementStatus = SupplementStatus.DRAFT


class AuditLog(SQLModel, table=True):
    """작업 주체·시각·변경 전후를 저장하는 이력. 민감 원문·비밀값은 넣지 않는다."""

    __tablename__ = "audit_logs"
    id: int | None = Field(default=None, primary_key=True)
    claim_id: str | None = Field(default=None, foreign_key="claims.id", index=True)
    actor_type: ActorType
    actor_id: int | None = Field(default=None, foreign_key="users.id")
    action: str
    detail: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class ReviewSettings(SQLModel, table=True):
    """설정 1행. 숫자 임계값은 설계 호환용으로 보존하고 high/low와 혼동하지 않는다."""

    __tablename__ = "settings"
    id: int = Field(default=1, primary_key=True)
    review_on_low_conf: bool
    review_on_not_in_source: bool
    review_on_format: bool = True
    auto_pass_threshold: float = Field(ge=0, le=1)


class RequiredDocRule(SQLModel, table=True):
    """청구 유형의 필수·조건부 서류 정의. 조건은 규칙 엔진에서 해석한다."""

    __tablename__ = "required_doc_rules"
    id: str = Field(primary_key=True)
    claim_type: str = Field(index=True)
    doc_types: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    conditions: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class CrossCheckRule(SQLModel, table=True):
    """교차검증 규칙 메타데이터. services/rules.py가 활성 규칙만 실행한다."""

    __tablename__ = "cross_check_rules"
    id: str = Field(primary_key=True)
    description: str
    doc_types: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    field_keys: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    issue_kind: IssueKind
    enabled: bool = True


class KcdCode(SQLModel, table=True):
    """질병코드 표시용 참조 데이터. 적용 차수 검증은 후속 티켓에서 수행한다."""

    __tablename__ = "kcd_codes"
    code: str = Field(primary_key=True)
    name: str


class DrugCatalog(SQLModel, table=True):
    """데모용 약품 분류 참조. 실제 보험 보상 여부를 확정하는 근거가 아니다."""

    __tablename__ = "drug_catalog"
    name: str = Field(primary_key=True)
    category: str
    is_mock: bool = True


class ProcessJob(SQLModel, table=True):
    """백그라운드 처리 상태를 DB에 보존한다. 프로세스 재시작도 완료로 오인하지 않는다."""

    __tablename__ = "process_jobs"
    __table_args__ = (
        Index(
            "uq_active_claim_job",
            "claim_id",
            unique=True,
            sqlite_where=text("state IN ('queued', 'running')"),
        ),
    )
    id: str = Field(primary_key=True)
    claim_id: str = Field(foreign_key="claims.id", index=True)
    actor_id: int = Field(foreign_key="users.id")
    state: str = "queued"
    stage: str = "classify"
    progress: int = Field(default=0, ge=0, le=100)
    errors: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    result: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
