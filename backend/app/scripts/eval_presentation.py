"""관련 문항만 같은 실제 응답에 표시 규칙을 적용한다. 검색/분류 평가는 재측정하지 않는다."""

import json

from sqlmodel import Session, select

from app.agent.graph import ChatAgent
from app.agent.kb import load_chunks
from app.agent.solar import Solar
from app.agent.tools import Tools
from app.config import PROJECT_ROOT, get_settings
from app.db import build_engine
from app.models import User
from app.schemas.chat import ChatAnswer, Route
from app.scripts.eval_chat import JUDGE_SCHEMA, RUBRIC, aggregate, measure
from app.scripts.eval_protocol import frozen, grade


def main():
    config = frozen(get_settings())
    folder = PROJECT_ROOT / "artifacts/t18/presentation/final"
    folder.mkdir(parents=True, exist_ok=True)
    source = json.loads(
        (PROJECT_ROOT / "artifacts/t18/runs/2026-10-16/tone/v2/chat_eval.json").read_text()
    )
    assert source["rubric"] == RUBRIC
    chunks = [c.payload() for c in load_chunks(config.KB_PATH)]
    names = {h["source_path"].removeprefix("data/kb/"): h["doc_name"] for h in chunks}

    class ReadKB:
        def lookup(self, path, article, term=""):
            return [
                h
                for h in chunks
                if h["source_path"].endswith(path)
                and h["article"] == article
                and term in h["chunk_text"]
            ]

        def search(self, query, collection=None, limit=3):
            # 표시 단계 실험에서는 기존 실제 검색 결과를 그대로 사용한다.
            return active_hits[:limit]

    engine = build_engine(config.DB_URL)
    before, after, details = [], [], []
    for row in source["results"]:
        old = row["response"]
        active_hits = row["retrieval_top3"]
        if (
            old["intent"] not in {"claim_check", "refusal", "item_coverage"}
            and not row["metrics"]["tone_violations"]
        ):
            continue
        path = folder / (row["id"] + ".json")
        if path.exists():
            saved = json.loads(path.read_text())
        else:
            with Session(engine) as session:
                user = session.exec(
                    select(User).where(User.email == config.DEMO_REVIEWER_EMAIL)
                ).one()
                tools = Tools(session, user, config, ReadKB())
                agent = ChatAgent(config, Solar(config), tools)
                cid = next((r["claim_id"] for r in old["claim_refs"]), None)
                state = {
                    "message": row["question"],
                    "claim_id": cid,
                    "history": [],
                    "route": Route(
                        intent=old["intent"],
                        customer_name=None,
                        claim_id=cid,
                        item_name=None,
                        doc_types=[],
                        query=row["question"],
                    ),
                }
                if old["intent"] == "claim_check":
                    claims = (
                        [
                            claim
                            for identifier in dict.fromkeys(
                                ref["claim_id"] for ref in old["claim_refs"]
                            )
                            for claim in tools.get_claim(claim_id=identifier)
                        ]
                        if cid
                        else []
                    )
                    issues = tools.get_claim_issues(cid) if cid else []
                    state["evidence"] = (
                        {
                            "claims": claims,
                            "issues": issues,
                            "hits": tools.claim_evidence(row["question"], issues),
                        }
                        if cid
                        else {"workload": tools.get_workload()}
                    )
                    if len(claims) == 1:
                        state.update(agent.gather(state))
                    state.update(agent.answer(state))
                elif old["intent"] == "item_coverage" and cid:
                    names_in_docs = [
                        item.get("drug_name", "")
                        for doc in tools.documents(cid)
                        for item in doc.values.get("items", [])
                        if item.get("drug_name")
                    ]
                    state["route"].item_name = next(
                        (name for name in names_in_docs if name.split(" (")[0] in row["question"]),
                        None,
                    )
                    state.update(agent.gather(state))
                    state.update(agent.answer(state))
                elif old["intent"] == "refusal":
                    state.update(agent.gather(state))
                    state.update(agent.answer(state))
                else:
                    state["result"] = ChatAnswer.model_validate(old)
                new = agent.tone(state)["result"].model_dump(mode="json")
                # 비용 절약을 위해 양쪽 답변을 동일 rubric으로 각1회 채점한다. 반복 캐시를 독립 투표로 세지 않는다.
                metrics = []
                for answer in (old, new):
                    judged = grade(Solar(config), row, answer["answer"], RUBRIC, JUDGE_SCHEMA, 1)
                    metrics.append(measure(row, answer, row["retrieval_top3"], names, judged))
                saved = {
                    "id": row["id"],
                    "question": row["question"],
                    "before": old,
                    "after": new,
                    "before_metrics": metrics[0],
                    "after_metrics": metrics[1],
                    "patterns": agent.tone_trace["remaining_violations"],
                }
                path.write_text(json.dumps(saved, ensure_ascii=False, indent=2))
                session.rollback()
        before.append({"metrics": saved["before_metrics"]})
        after.append({"metrics": saved["after_metrics"]})
        details.append(saved)
        print(row["id"] + " 표시 전후 완료", flush=True)
    payload = {
        "method": "기존 실제 응답을 재사용한 표시 단계 비교. 의도/검색은 이전 결과를 상속하며 신규 측정이 아님. 동일 rubric 각각1회, 캐시 적용. 홀드아웃 미사용.",
        "rubric": RUBRIC,
        "before": aggregate(before),
        "after": aggregate(after),
        "results": details,
    }
    (folder / "comparison.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    engine.dispose()


if __name__ == "__main__":
    main()
