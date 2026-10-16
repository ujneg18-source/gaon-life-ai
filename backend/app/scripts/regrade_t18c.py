"""기존 답변을 바꾸지 않고 구/신 rubric 3회 재채점·회귀 네 문항 분석을 보존한다."""

import json
from concurrent.futures import ThreadPoolExecutor

from app.agent.solar import Solar
from app.config import get_settings
from app.scripts.eval_chat import JUDGE_SCHEMA, OLD_RUBRIC, RUBRIC
from app.scripts.eval_protocol import frozen, grade, manifest


def main():
    c = frozen(get_settings())
    out = c.EVAL_OUTPUT_PATH / "runs/2026-10-16/t18c/regrade"
    out.mkdir(parents=True, exist_ok=True)
    old = json.loads((c.EVAL_OUTPUT_PATH / "revision-3/chat_eval.json").read_text())
    last = json.loads((c.EVAL_OUTPUT_PATH / "final/chat_eval.json").read_text())
    qs = {q["id"]: q for q in json.loads(c.EVAL_QUESTIONS_PATH.read_text())["questions"]}
    prior = {q["id"]: q for q in old["results"]}
    flips = [
        q["id"]
        for q in last["results"]
        if q["metrics"]["gist"]["score"] == 0 and prior[q["id"]]["metrics"]["gist"]["score"] == 1
    ]
    jobs = [
        ("final", q, rubric, name)
        for q in last["results"]
        for rubric, name in [(OLD_RUBRIC, "old"), (RUBRIC, "new")]
    ]
    jobs += [("intermediate", prior[i], OLD_RUBRIC, "old") for i in flips]

    def one(job):
        phase, row, rubric, name = job
        p = out / f"{phase}_{row['id']}_{name}.json"
        if p.exists():
            return json.loads(p.read_text())
        solar = Solar(c)
        result = grade(solar, qs[row["id"]], row["response"]["answer"], rubric, JUDGE_SCHEMA)
        r = {
            "id": row["id"],
            "phase": phase,
            "rubric": name,
            "answer": row["response"]["answer"],
            "grade": result,
            "response_meta": getattr(solar, "last_response_meta", {}),
        }
        p.write_text(json.dumps(r, ensure_ascii=False, indent=2))
        print(p.name, [v["score"] for v in result["votes"]], flush=True)
        return r

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(one, jobs))
    payload = {
        "manifest": manifest(c),
        "old_rubric": OLD_RUBRIC,
        "new_rubric": RUBRIC,
        "flipped_ids": flips,
        "results": results,
    }
    (out / "regrade.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    report = [
        "# 요지 회귀·동일 답변 3회 채점",
        "",
        "| 기존 최종30답변 | 다수결 점수 | 전원 일치 |",
        "|---|---:|---:|",
    ]
    for rubric in ["old", "new"]:
        rows = [r for r in results if r["phase"] == "final" and r["rubric"] == rubric]
        report.append(
            f"| {rubric} | {sum(r['grade']['score'] for r in rows)}/30 | {sum(r['grade']['unanimous'] for r in rows)}/30 |"
        )
    causes = {
        "Q03": "채점 흔들림: 같은 일반 약관 비율 안내를 허용/위반으로 달리 판정. 위계 순서나 인용 제한이 원인이라는 증거 없음.",
        "Q19": "채점 흔들림: 답변과 DB 집계가 완전히 같고 컨텍스트도 없음.",
        "Q24": "기타(생성 행동 누락): 두 실행 모두 대조 지침 근거가 있었으나 최종 답변이 영수증-처방전 대조 행동을 생략. 추가 영양제 조각의 주의 분산 가능성은 있으나 위계/2개 인용 제한의 인과는 확인 못함.",
        "Q27": "채점 흔들림: 답변이 동일한 범위 밖 거절. 없는 문서 설명을 요구한 rubric 적용 오판.",
    }
    for i in flips:
        b = prior[i]
        a = next(r for r in last["results"] if r["id"] == i)
        report += [
            "",
            f"## {i} · {a['question']}",
            causes.get(i, "기타"),
            "",
            "| 구분 | 중간 | 최종 |",
            "|---|---|---|",
        ]
        for label, fn in [
            ("답변 원문", lambda r: r["response"]["answer"]),
            (
                "컨텍스트 ID",
                lambda r: (
                    json.dumps(
                        [
                            h.get("node_id", h.get("chunk_id"))
                            for h in (r.get("grounding_trace") or {}).get("sources", [])
                        ],
                        ensure_ascii=False,
                    )
                    if r.get("grounding_trace")
                    else json.dumps(
                        [
                            h.get("node_id", h.get("chunk_id"))
                            for t in r.get("search_trace", [])
                            for h in t.get("hits", [])
                        ],
                        ensure_ascii=False,
                    )
                ),
            ),
            ("기존 rubric 판정", lambda r: json.dumps(r["metrics"]["gist"], ensure_ascii=False)),
        ]:
            report.append(
                "| "
                + label
                + " | "
                + fn(b).replace("|", "\\|").replace("\n", "<br>")
                + " | "
                + fn(a).replace("|", "\\|").replace("\n", "<br>")
                + " |"
            )
        for phase in ["intermediate", "final"]:
            r = next(
                r for r in results if r["phase"] == phase and r["id"] == i and r["rubric"] == "old"
            )
            report += [
                "",
                phase + " 동일 답변 구 rubric 3회: " + json.dumps(r["grade"], ensure_ascii=False),
            ]
    report += [
        "",
        "28→25점은 1→0 네 건(Q03/Q19/Q24/Q27), 0→1 한 건(Q26)의 순효과다. 과거 실행에는 seed가 없었으므로 과거 두 점수를 통제된 코드 효과로 단정하지 않는다.",
    ]
    (out / "regression.md").write_text("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
