"""공개·가상 허용 목록의 구조별 조각 수/길이를 네트워크 없이 재현한다."""

import statistics

from app.agent.kb import load_structure
from app.config import get_settings


def main():
    c = get_settings()
    tree = load_structure(c.KB_PATH)
    lines = [
        "# 구조 기반 청킹 보고서",
        "",
        "호/항을 검색하고 별도 JSON 부모 항을 확장한다. 길이로 단서 문장을 자르지 않는다.",
        "",
        "| 문서 | 수 | 최소 | 중앙 | p95 | 최대 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for path in sorted({p.source_path for p in tree.chunks}):
        sizes = sorted(len(p.chunk_text) for p in tree.chunks if p.source_path == path)
        lines.append(
            f"| {path} | {len(sizes)} | {sizes[0]} | {statistics.median(sizes)} | {sizes[min(len(sizes) - 1, int(len(sizes) * 0.95))]} | {sizes[-1]} |"
        )
    lines += [
        "",
        f"전체 {len(tree.chunks)}개 / 노드 {len(tree.nodes)}개 / 정의 용어 {len(tree.definitions)}개.",
        "",
        "영양제 원문은 상해③2·질병③2·MRI④2 세 곳에 있다. 각각 별도 주소로 보존한다.",
        "",
        "부표를 마지막 제43조에 붙이지 않고 별도 경계로 분리한다. 원문 개정 이력의 동일 번호는 revision/occurrence 주소로 보존한다.",
        "",
        "부모·목 원문: KB_STRUCTURE_PATH (기본 data/cache/kb_nodes.json). API 키·reference 원문은 포함하지 않는다.",
    ]
    out = c.EVAL_OUTPUT_PATH / "chunk_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(
        f"chunks={len(tree.chunks)}, nodes={len(tree.nodes)}, definitions={len(tree.definitions)}"
    )


if __name__ == "__main__":
    main()
