"""실제 호출 검증 전용 CLI. 자동 테스트와 분리하고 답변 원문·검색 결과를 파일에 남긴다."""

import argparse
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "artifacts/t16")
    args = parser.parse_args()
    config = get_settings()
    # 검증이 사용자의 검토/감사 이력을 바꾸지 않도록 DB와 인덱스를 복제한다.
    snapshot = tempfile.TemporaryDirectory(prefix="gaon-chat-smoke-")
    tmp = Path(snapshot.name)
    with (
        sqlite3.connect(config.DB_URL.removeprefix("sqlite:///")) as src,
        sqlite3.connect(tmp / "smoke.db") as dst,
    ):
        src.backup(dst)
    updates = {"DB_URL": f"sqlite:///{tmp / 'smoke.db'}"}
    if not config.QDRANT_URL:
        shutil.copytree(config.QDRANT_PATH, tmp / "qdrant", ignore=shutil.ignore_patterns(".lock"))
        updates["QDRANT_PATH"] = tmp / "qdrant"
    config = config.model_copy(update=updates)
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
            tools = Tools(session, user, config, kb)
            tools.tool_errors = []
            agent = ChatAgent(config, Solar(config), tools)
            for question in QUESTIONS:
                answer = agent.run(question, claim.id)
                results.append(
                    {
                        "question": question,
                        **answer.model_dump(),
                        "tool_errors": list(tools.tool_errors),
                    }
                )
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
                "rider2" in c["source_path"] and c["article"].startswith("제4조")
                for c in second["citations"]
            ),
            "template": "[가온생명] 김유정 고객님" in third["answer"]
            and "병원 원무과" in third["answer"],
            "refused": fourth["refused"],
        }
        output = args.out if args.out.is_absolute() else PROJECT_ROOT / args.out
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
        snapshot.cleanup()


if __name__ == "__main__":
    main()
