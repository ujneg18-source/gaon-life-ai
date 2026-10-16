"""챗봇 API 계약. 선택적 값도 필수 키+nullable로 구조화 출력과 동일하게 검증한다."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Intent = Literal["policy_qa", "claim_check", "item_coverage", "draft", "refusal"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Citation(StrictModel):
    source_kind: str = "약관"
    coverage_section: str = ""
    authority_level: int = 1
    chunk_id: str = ""
    doc_name: str
    article: str
    source_path: str
    is_mock: bool
    quote: str


class ClaimRef(StrictModel):
    claim_id: str
    issue_id: int | None


class Action(StrictModel):
    label: str
    action: str


class ChatAnswer(StrictModel):
    used_chunk_ids: list[str] = Field(default_factory=list)
    answer: str
    intent: Intent
    citations: list[Citation]
    claim_refs: list[ClaimRef]
    suggested_actions: list[Action]
    refused: bool


class Route(StrictModel):
    intent: Intent
    customer_name: str | None
    claim_id: str | None
    item_name: str | None
    doc_types: list[str]
    query: str


class History(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    claim_id: str | None = None
    history: list[History] = Field(default_factory=list, max_length=24)


class UsedQuote(StrictModel):
    chunk_id: str
    quote: str


class GroundedAnswer(StrictModel):
    """모델은 사용한 주소·인용문만 제안한다. 출처 메타데이터는 서버가 만든다."""

    used_chunk_ids: list[str]
    answer: str
    quotes: list[UsedQuote]
