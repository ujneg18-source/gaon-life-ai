"""개발 셋의 기존 답변 말투 재채점과 필수4문항 전후 비교. 홀드아웃은 읽지 않는다."""

import argparse
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

from sqlmodel import Session, select

from app.agent.graph import ChatAgent
from app.agent.solar import Solar
from app.agent.tools import Tools
from app.config import PROJECT_ROOT, get_settings
from app.db import build_engine
from app.models import User
from app.scripts.chat_smoke import QUESTIONS
from app.scripts.eval_protocol import ExperimentKB, frozen, manifest
from app.scripts.tone_grade import TONE_RUBRIC, grade_tone


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = PROJECT_ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    config = frozen(get_settings())
    baseline = PROJECT_ROOT / "artifacts/t18/runs/2026-10-16/t18c"
    old = json.loads((baseline / "new_new_v2/chat_eval.json").read_text())
    graded = []
    for row in old["results"]:
        path = out / ("before_" + row["id"] + ".json")
        if path.exists():
            result = json.loads(path.read_text())
        else:
            result = {
                "id": row["id"],
                "question": row["question"],
                "answer": row["response"]["answer"],
                "tone": grade_tone(Solar(config), row["question"], row["response"]["answer"]),
            }
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        graded.append(result)
        print(row["id"] + " 기존 말투 채점 완료", flush=True)
    (out / "before_tone.json").write_text(
        json.dumps(
            {"manifest": manifest(config), "rubric": TONE_RUBRIC, "results": graded},
            ensure_ascii=False,
            indent=2,
        )
    )
    old_demo = json.loads((baseline / "demo/demo.json").read_text())["answers"][:4]
    rows = []
    with tempfile.TemporaryDirectory(prefix="gaon-tone-demo-") as temp_name:
        tmp = Path(temp_name)
        with (
            sqlite3.connect(config.DB_URL.removeprefix("sqlite:///")) as src,
            sqlite3.connect(tmp / "demo.db") as dst,
        ):
            src.backup(dst)
        shutil.copytree(
            config.EVAL_SNAPSHOT_PATH / "index",
            tmp / "index",
            ignore=shutil.ignore_patterns(".lock"),
        )
        config = config.model_copy(
            update={"DB_URL": f"sqlite:///{tmp / 'demo.db'}", "QDRANT_PATH": tmp / "index"}
        )
        engine = build_engine(config.DB_URL)
        kb = ExperimentKB(config)
        try:
            with Session(engine) as session:
                user = session.exec(
                    select(User).where(User.email == config.DEMO_REVIEWER_EMAIL)
                ).one()
                agent = ChatAgent(config, Solar(config), Tools(session, user, config, kb))
                for i, q in enumerate(QUESTIONS):
                    path = out / f"demo_P{i + 1}.json"
                    if path.exists():
                        row = json.loads(path.read_text())
                    else:
                        answer = agent.run(q, "GA-2610-0482").model_dump(mode="json")
                        row = {
                            "question": q,
                            "before": old_demo[i],
                            "after": answer,
                            "tone_trace": agent.tone_trace,
                            "before_tone": grade_tone(Solar(config), q, old_demo[i]["answer"]),
                            "after_tone": grade_tone(Solar(config), q, answer["answer"]),
                        }
                        path.write_text(json.dumps(row, ensure_ascii=False, indent=2))
                    rows.append(row)
                    print(f"P{i + 1} 완료", flush=True)
        finally:
            kb.client.close()
            engine.dispose()
    text = [
        "# 필수 시연4문항 말투 전후",
        "",
        "T-18c 기존 실제 답변과 말투 보완 후 실제 답변입니다. 개발 질문은 프롬프트 예시에 쓰지 않았고 홀드아웃은 재실행하지 않았습니다.",
        "",
    ]
    for i, row in enumerate(rows, 1):
        text += [
            f"## P{i}. {row['question']}",
            "",
            "| 이전 답변 | 이후 답변 |",
            "|---|---|",
            "| "
            + row["before"]["answer"].replace("|", "\\|").replace("\n", "<br>")
            + " | "
            + row["after"]["answer"].replace("|", "\\|").replace("\n", "<br>")
            + " |",
            "",
            f"말투: {row['before_tone']['score']}/5 → {row['after_tone']['score']}/5. 거절 여부: {row['before']['refused']} / {row['after']['refused']}.",
            "",
        ]
    (out / "tone_before_after.md").write_text("\n".join(text))
    (PROJECT_ROOT / "artifacts/t18/tone_before_after.md").write_text("\n".join(text))


if __name__ == "__main__":
    main()
