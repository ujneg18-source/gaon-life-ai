"""허용 목록의 약관만 조항으로 나누는 지식 원천. reference/나 HWP는 열지 않는다."""

import re
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml


@dataclass
class Chunk:
    """Qdrant payload와 원문 인용의 공통 계약. 공개/가상 여부를 잃지 않는다."""

    doc_name: str
    edition: str
    article: str
    title: str
    is_mock: bool
    source_path: str
    chunk_text: str
    collection: str

    def payload(self):
        return asdict(self)


def load_chunks(root: Path, max_chars: int = 1800) -> list[Chunk]:
    """제N조를 우선 분할하고 긴 조만 항으로 분리한다. 상품 개요는 절 구조를 보존한다."""
    paths = sorted((root / "policy").glob("std_*.txt"))
    paths += sorted(
        p for p in (root / "gaon").glob("*.md") if re.match(r"(?:0[0-4]|1[01])_", p.name)
    )
    chunks = []
    for path in paths:
        # 심볼릭 링크를 통한 reference/ 우회도 허용하지 않는다.
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("허용되지 않은 지식 경로")
        text = path.read_text(encoding="utf-8")
        meta = {}
        if text.startswith("---\n"):
            _, front, text = text.split("---", 2)
            meta = yaml.safe_load(front)
            if not isinstance(meta.get("is_mock"), bool):
                raise ValueError("is_mock frontmatter가 필요합니다")
        is_txt = path.suffix == ".txt"
        collection = "manual" if path.name.startswith(("10_", "11_")) else "policy"
        pattern = (
            r"(?m)^## (.+)$"
            if collection == "manual" or path.name.startswith("00_")
            else r"(?m)^(?:##\s*)?(제\s*\d+\s*조\s*\([^\n)]*\))"
        )
        matches = list(re.finditer(pattern, text))
        if not matches:
            raise ValueError(f"분할 경계 없음: {path.name}")
        name = str(meta.get("doc_name", text.splitlines()[0].lstrip("# ")))
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            body = text[
                match.start() : matches[i + 1].start() if i + 1 < len(matches) else len(text)
            ].strip()
            article_match = re.search(r"제\s*\d+\s*조", title)
            article = (
                re.sub(r"\s", "", article_match.group())
                if article_match
                else title.split(".")[0] + "장"
            )
            pieces = [body]
            if collection == "policy" and len(body) > max_chars:
                # 항 첫 줄이 아닌 본문 안의 인용 ①은 분할 경계로 오인하지 않는다.
                parts = re.split(r"(?m)^\s*(?=[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])", body)
                prefix = parts[0]
                pieces = [prefix + "\n" + part for part in parts[1:] if part.strip()] or [body]
            # 표가 긴 항은 문단/행 경계로 이어 나누고 조문·항 표제를 반복해 맥락을 유지한다.
            bounded = []
            for piece in pieces:
                if len(piece) <= max_chars:
                    bounded.append(piece)
                    continue
                prefix = (
                    title
                    + "\n"
                    + piece.splitlines()[
                        1 if piece.startswith("제") and len(piece.splitlines()) > 1 else 0
                    ][:100]
                    + "\n"
                )
                current = prefix
                for line in piece.splitlines():
                    for offset in range(0, max(1, len(line)), max_chars - len(prefix)):
                        part = line[offset : offset + max_chars - len(prefix)]
                        if len(current) + len(part) + 1 > max_chars:
                            bounded.append(current)
                            current = prefix
                        current += part + "\n"
                if current.strip() != prefix.strip():
                    bounded.append(current.strip())
            for piece in bounded:
                chunks.append(
                    Chunk(
                        name,
                        str(meta.get("edition", "2026.08.28")),
                        article,
                        title,
                        False if is_txt else meta["is_mock"],
                        "data/kb/" + path.relative_to(root).as_posix(),
                        piece,
                        collection,
                    )
                )
    return chunks
