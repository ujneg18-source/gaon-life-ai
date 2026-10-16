"""쿠키 인증 챗봇. 대화 본문은 DB/감사 로그에 저장하지 않고 클라이언트 세션 메모리로만 받는다."""

from threading import Lock

from fastapi import APIRouter, HTTPException, Request

from app.agent.graph import ChatAgent
from app.agent.rag import KnowledgeBase
from app.agent.solar import Solar
from app.agent.tools import Tools
from app.auth import CurrentUser, SessionDep, require_claim_access
from app.schemas.chat import ChatAnswer, ChatRequest

router = APIRouter(tags=["chat"])
_kb_lock = Lock()


@router.post("/chat", response_model=ChatAnswer)
def chat(payload: ChatRequest, user: CurrentUser, session: SessionDep, request: Request):
    config = request.app.state.settings
    if payload.claim_id:
        require_claim_access(payload.claim_id, user, session)
    kb = None
    try:
        # 테스트는 factory를 주입해 실제 HTTP와 로컬 DB 잠금을 피한다.
        factory = getattr(request.app.state, "chat_factory", None)
        if factory:
            agent = factory(session, user, config)
        else:
            # Qdrant 로컬은 파일 잠금이 있으므로 프로세스에서 클라이언트 하나를 공유한다.
            with _kb_lock:
                if not hasattr(request.app.state, "chat_kb"):
                    request.app.state.chat_kb = KnowledgeBase(config)
                kb = request.app.state.chat_kb
            agent = ChatAgent(config, Solar(config), Tools(session, user, config, kb))
        result = agent.run(
            payload.message, payload.claim_id, [h.model_dump() for h in payload.history]
        )
        session.commit()
        return result
    except (RuntimeError, ValueError, KeyError, TypeError):
        # HTTP 응답/키/모델 원문 오류는 숨기고 사용자용 오류만 전달한다.
        raise HTTPException(
            503, "업무 어시스턴트 연결을 확인해 주세요. 캐시 또는 AI 연결이 준비되지 않았어요."
        ) from None
