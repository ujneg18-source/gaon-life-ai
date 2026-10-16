"""같은 실행의 사실 초안/말투 답변을 비교해 별도 실행의 생성 변동과 분리한다."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.agent.kb import load_chunks
from app.agent.solar import Solar
from app.agent.tone import violations
from app.config import PROJECT_ROOT, get_settings
from app.scripts.eval_chat import JUDGE_SCHEMA, RUBRIC, aggregate, measure
from app.scripts.eval_protocol import frozen, grade
from app.scripts.tone_grade import grade_tone


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    root = PROJECT_ROOT / args.run
    payload = json.loads((root / "chat_eval.json").read_text())
    config = frozen(get_settings())
    names = {
        c.source_path.removeprefix("data/kb/"): c.doc_name
        for c in load_chunks(config.KB_PATH, config.KB_CHUNK_MAX_CHARS)
    }
    out = root / "paired_before"
    out.mkdir(exist_ok=True)

    def evaluate(row):
        path = out / (row["id"] + ".json")
        if path.exists():
            return json.loads(path.read_text())
        # 말투 노드는 model_copy(answer=...)만 수행한다. 메타데이터는 같은 객체 계약으로 보존된다.
        before = {**row["response"], "answer": row["tone_trace"]["before"]}
        judge = grade(Solar(config), row, before["answer"], RUBRIC, JUDGE_SCHEMA, 3)
        metrics = measure(row, before, row["retrieval_top3"], names, judge)
        metrics.update(
            {
                "tone": grade_tone(Solar(config), row["question"], before["answer"]),
                "tone_violations": violations(before["answer"]),
            }
        )
        result = {
            "id": row["id"],
            "question": row["question"],
            "response": before,
            "metrics": metrics,
        }
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(row["id"] + " 같은 초안 채점 완료", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(evaluate, payload["results"]))
    (root / "paired_comparison.json").write_text(
        json.dumps(
            {
                "method": "같은 실행에서 사실/인용 확정 후, 말투 처리 전후의 대응 비교. 인용 메타데이터는 같은 값을 사용한다.",
                "before": aggregate(rows),
                "after": payload["summary"],
                "before_rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
