"""실제 호출 검증 전용 CLI. 자동 테스트와 분리하고 답변 원문·검색 결과를 파일에 남긴다."""

import json

from sqlmodel import Session

from app.agent.graph import ChatAgent
from app.agent.rag import KnowledgeBase
from app.agent.solar import Solar
from app.agent.tools import Tools
from app.config import PROJECT_ROOT, get_settings
from app.db import build_engine
from app.models import Claim, User
from app.services.rules import review_from_db

QUESTIONS = [
    "김유정 고객 서류 왔는지 확인해보고 보완사항 있는지 검토해줘",
    "김유정 약제비 영수증에 종합비타민정 보상돼?",
    "수술확인서 보완 요청 문자 써줘",
    "이거 지급해도 돼?",
]


def main():
    config = get_settings()
    engine = build_engine(config.DB_URL)
    kb = KnowledgeBase(config)
    results = []
    try:
        with Session(engine) as session:
            claim = session.get(Claim, "GA-2610-0482")
            # 기존 추출값은 그대로 두고 새 CV-02 정의로 저장 이슈만 갱신한다.
            review_from_db(session, claim, config)
            session.commit()
            user = session.get(User, claim.assignee_id)
            agent = ChatAgent(config, Solar(config), Tools(session, user, config, kb))
            for question in QUESTIONS:
                answer = agent.run(question, claim.id)
                results.append({"question": question, **answer.model_dump()})
                print(
                    json.dumps(
                        {"question": question, "answer": answer.answer, "intent": answer.intent},
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
            session.commit()
        first, second, third, fourth = results
        checks = {
            "claim_7_8": "제출 7 / 필요 8" in first["answer"],
            "missing_cv04": "CV-04" in first["answer"] and "수술확인서" in first["answer"],
            "cv01": "CV-01" in first["answer"],
            "subcode": "C18.7" in first["answer"] and "세분류" in first["answer"],
            "cv02_info": "안내 (CV-02)" in first["answer"],
            "draft_action": any(a["label"] == "보완 요청 작성" for a in first["suggested_actions"]),
            "vitamin": "보상 제외 가능성" in second["answer"]
            and "처방전에 없음" in second["answer"],
            "vitamin_source": any(
                "rider2" in c["source_path"] and c["article"] == "제4조"
                for c in second["citations"]
            ),
            "template": "[가온생명] 김유정 고객님" in third["answer"]
            and "병원 원무과" in third["answer"],
            "refused": fourth["refused"],
        }
        output = PROJECT_ROOT / "artifacts/t16"
        output.mkdir(parents=True, exist_ok=True)
        (output / "chat_smoke.json").write_text(
            json.dumps({"answers": results, "checks": checks}, ensure_ascii=False, indent=2)
        )
        print(json.dumps(checks, ensure_ascii=False), flush=True)
        if not all(checks.values()):
            raise SystemExit("일부 실제 검증 실패: artifacts/t16/chat_smoke.json 확인")
    finally:
        kb.client.close()
        engine.dispose()


if __name__ == "__main__":
    main()
