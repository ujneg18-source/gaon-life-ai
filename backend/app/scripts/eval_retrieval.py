"""같은 구조 인덱스로 dense-only와 hybrid를 독립 측정한다. 정답은 검색 함수에 전달하지 않는다."""

import json
from concurrent.futures import ThreadPoolExecutor

from app.agent.kb import load_structure
from app.agent.rag import KnowledgeBase
from app.config import get_settings
from app.scripts.eval_chat import source_pair
from app.scripts.legacy_search import LegacySearch


def main():
    c = get_settings()
    out = c.EVAL_OUTPUT_PATH / "ablation"
    out.mkdir(parents=True, exist_ok=True)
    questions = json.loads(c.EVAL_QUESTIONS_PATH.read_text())["questions"]
    names = {
        p.source_path.removeprefix("data/kb/"): p.doc_name for p in load_structure(c.KB_PATH).chunks
    }
    all_results = {}
    for mode in ["legacy", "dense", "hybrid"]:
        kb = KnowledgeBase(c.model_copy(update={"RAG_MODE": mode}))
        kb.corpus()

        def one(q, mode=mode, kb=kb):
            path = out / (mode + "_" + q["id"] + ".json")
            if path.exists():
                return json.loads(path.read_text())
            hits = (
                LegacySearch.search(kb, q["question"])
                if mode == "legacy"
                else kb.search(q["question"])
            )
            expected = {source_pair(s, names) for s in q["expected_sources"]}
            found = {source_pair(h, names) for h in hits}
            r = {
                "id": q["id"],
                "question": q["question"],
                "recall": len(found & expected) / len(expected) if expected else None,
                "hits": hits,
                "trace": kb.traces.get((q["question"], None, 3), {}),
            }
            path.write_text(json.dumps(r, ensure_ascii=False, indent=2))
            print(mode, q["id"], r["recall"], flush=True)
            return r

        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                rows = list(pool.map(one, questions))
        finally:
            kb.client.close()
        recalls = [r["recall"] for r in rows if r["recall"] is not None]
        all_results[mode] = {
            "recall_at_3": sum(recalls) / len(recalls),
            "questions": len(recalls),
            "results": rows,
        }
    (out / "retrieval_ablation.json").write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2)
    )
    lines = [
        "# 청킹·검색 ablation",
        "",
        "동일 새 구조 인덱스/머리말 임베딩/질문/정답. legacy는 이전 점수·BM25 정규화·가중치를 그대로 두고 주소 묶음만 새 구조로 바꾼 청킹-only 실험이다. dense는 추가 참고이며 재작성·BM25·재정렬이 없다. hybrid는 RRF·재작성·재정렬까지 적용한다. 운영 코드에는 legacy를 쓰지 않는다.",
        "",
        "| 변경 | recall@3 |",
        "|---|---:|",
        "| 이전 인덱스 + 이전 검색 (정답 수정 후) | 70.83% |",
    ]
    for mode, r in all_results.items():
        lines.append(f"| 구조 청킹 + {mode} | {r['recall_at_3']:.2%} |")
    (out / "retrieval_ablation.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
