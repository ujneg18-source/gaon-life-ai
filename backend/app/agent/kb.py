"""허용된 공개·가상 문서를 주소가 있는 트리로 읽는다. reference/HWP는 열지 않는다."""

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

CIRCLES = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
ARTICLE = r"(?m)^(?:##\s*)?((?:제\s*\d+\s*조\s*\([^\n)]*\))|(?:<\s*부\s*표\s*[\d-]+\s*>))"


@dataclass
class Chunk:
    """검색 단위는 호, 인용 주소는 항·호까지 보존한다. article은 기존 조 단위 계약이다."""

    doc_name: str
    edition: str
    article: str
    title: str
    is_mock: bool
    source_path: str
    chunk_text: str
    collection: str
    coverage_section: str = ""
    paragraph: str = ""
    item: str = ""
    node_id: str = ""
    parent_id: str = ""
    is_definition: bool = False
    refs: list = field(default_factory=list)
    defined_terms: list = field(default_factory=list)
    paragraph_head: str = ""
    address: str = ""
    authority_level: int = 1
    governs: list = field(default_factory=list)
    falls_back_to: list = field(default_factory=list)

    def payload(self):
        return asdict(self)


@dataclass
class Structure:
    """검색 벡터와 별도로 부모/목/정의 원문을 보관해 길이 제한으로 원문을 훼손하지 않는다."""

    chunks: list = field(default_factory=list)
    nodes: dict = field(default_factory=dict)
    definitions: dict = field(default_factory=dict)

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"nodes": self.nodes, "definitions": self.definitions}, ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )


def _spans(pattern, text):
    matches = list(re.finditer(pattern, text))
    return [
        (m, text[m.start() : matches[i + 1].start() if i + 1 < len(matches) else len(text)].strip())
        for i, m in enumerate(matches)
    ]


def _coverage(body):
    # TXT 표의 줄바꿈을 읽되 일반 (1) 예시는 보장종목으로 오인하지 않는다.
    pattern = r"(?m)^\s*\(\d+\)[ \t]*(?:\n[ \t]*)?((?:상해|질병)(?:[ \t]*\n[ \t]*|[ \t]*)비급여|비급여[ \t]+자기공명영상진단|상해급여|질병급여|공통)(?:주\))?"
    matches = list(re.finditer(pattern, body))
    if not matches:
        return [("", body)]
    sections = []
    for i, m in enumerate(matches):
        name = re.sub(r"\s", "", m.group(1))
        sections.append(
            (
                name,
                body[
                    m.end() : matches[i + 1].start() if i + 1 < len(matches) else len(body)
                ].strip(),
            )
        )
    return sections


def _refs(text):
    # 법령도 원문 주소로 남기되 실제 연결은 동일 문서에 존재하는 노드만 한다.
    return list(
        dict.fromkeys(
            re.sub(r"\s+", " ", m.group()).strip()
            for m in re.finditer(r"제\s*\d+\s*조(?:\s*제\s*\d+\s*항)?", text)
        )
    )


def load_structure(root: Path) -> Structure:
    result = Structure()
    paths = sorted((root / "policy").glob("std_*.txt")) + sorted(
        p for p in (root / "gaon").glob("*.md") if re.match(r"(?:0[0-4]|1[01])_", p.name)
    )
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("허용되지 않은 지식 경로")
        text = path.read_text(encoding="utf-8")
        meta = {}
        if text.startswith("---\n"):
            _, front, text = text.split("---", 2)
            meta = yaml.safe_load(front)
            if not isinstance(meta.get("is_mock"), bool):
                raise ValueError("is_mock frontmatter가 필요합니다")
        source = "data/kb/" + path.relative_to(root).as_posix()
        prefix = "rider2" if path.name.startswith("std_silson_rider2_") else path.stem
        collection = "manual" if path.name.startswith(("10_", "11_")) else "policy"
        sections = _spans(
            r"(?m)^## (.+)$" if collection == "manual" or path.name.startswith("00_") else ARTICLE,
            text,
        )
        if not sections:
            raise ValueError(f"분할 경계 없음: {path.name}")
        for match, raw in sections:
            title = match.group(1).strip()
            number = re.search(r"제\s*\d+\s*조", title)
            article = re.sub(r"\s", "", number.group()) if number else title.split(".")[0] + "장"
            body = raw[len(match.group().strip()) :].strip()
            article_id = f"{prefix}/{article}"
            authority = (
                1
                if path.suffix == ".txt"
                else 2
                if path.name.startswith("00_")
                else 4
                if collection == "manual"
                else 3
            )
            common = {
                "authority_level": authority,
                "doc_name": str(meta.get("doc_name", text.splitlines()[0].lstrip("# "))),
                "edition": str(meta.get("edition", "2026.08.28")),
                "article": article,
                "title": title,
                "is_mock": False if path.suffix == ".txt" else meta["is_mock"],
                "source_path": source,
                "collection": collection,
                "is_definition": "정의" in title,
            }
            result.nodes[article_id] = {
                **common,
                "node_id": article_id,
                "chunk_text": raw,
                "parent_id": prefix,
            }
            result.nodes.setdefault(
                prefix,
                {
                    "node_id": prefix,
                    "parent_id": "",
                    "chunk_text": "",
                    "source_path": source,
                    "doc_name": common["doc_name"],
                },
            )

            def add(
                content,
                node_id,
                parent_id,
                coverage="",
                paragraph="",
                item="",
                head="",
                common=common,
                article=article,
            ):
                address = " ".join(
                    x for x in [article, paragraph, f"{item}호" if item else ""] if x
                )
                chunk = Chunk(
                    **common,
                    chunk_text=content,
                    coverage_section=coverage,
                    paragraph=paragraph,
                    item=item,
                    node_id=node_id,
                    parent_id=parent_id,
                    paragraph_head=head,
                    address=address,
                    refs=_refs(content),
                )
                if node_id in result.nodes:
                    raise ValueError(f"중복 주소: {node_id}")
                result.nodes[node_id] = chunk.payload()
                result.chunks.append(chunk)
                return chunk

            if collection == "manual" or path.name.startswith("00_"):
                # 표 머리글과 각 행을 함께 검색한다. 표 전후 설명은 독립 문단으로 보존한다.
                lines = body.splitlines()
                prose = []
                header = None
                ordinal = 0

                def flush(prose=prose, title=title, article_id=article_id, add=add):
                    nonlocal ordinal
                    if "\n".join(prose).strip():
                        ordinal += 1
                        add(
                            title + "\n" + "\n".join(prose).strip(),
                            f"{article_id}/text{ordinal}",
                            article_id,
                        )
                    prose.clear()

                for line in lines:
                    if line.strip().startswith("|"):
                        flush()
                        if re.match(r"^\s*\|[\s:|\-]+\|\s*$", line):
                            continue
                        if header is None:
                            header = line
                            continue
                        ordinal += 1
                        add(
                            title + "\n" + header + "\n" + line,
                            f"{article_id}/row{ordinal}",
                            article_id,
                        )
                    else:
                        header = None
                        prose.append(line)
                flush()
                continue
            for coverage, section in _coverage(body):
                base = f"{prefix}/{coverage or '공통'}/{article}"
                coverage_id = f"{prefix}/{coverage or '공통'}"
                result.nodes.setdefault(
                    coverage_id,
                    {
                        **common,
                        "node_id": coverage_id,
                        "parent_id": prefix,
                        "coverage_section": coverage,
                        "chunk_text": "",
                    },
                )
                result.nodes[base] = {
                    **common,
                    "node_id": base,
                    "parent_id": coverage_id,
                    "coverage_section": coverage,
                    "chunk_text": section,
                }
                paragraphs = _spans(r"(?m)^[ \t]*([" + CIRCLES + r"])", section)
                # 조에 항이 없더라도 호 목록은 읽는다. 첫 항 앞 도입부도 잃지 않는다.
                preface = section[: paragraphs[0][0].start()].strip() if paragraphs else ""
                if preface:
                    add(title + "\n" + preface, base + "/intro", base, coverage)
                for pm, paragraph_body in paragraphs or [(None, section)]:
                    marker = pm.group(1) if pm else ""
                    index = str(CIRCLES.index(marker) + 1) if marker else "0"
                    parent = f"{base}/{index}"
                    if parent in result.nodes:
                        # 원문 개정 이력에 같은 항 번호와 삭제 표기가 함께 있다. 덮어쓰지 않는다.
                        parent += "/revision" + str(sum(n.startswith(parent) for n in result.nodes))
                    items = _spans(r"(?m)^[ \t]*(\d+)\.[ \t]+", paragraph_body)
                    head = (
                        paragraph_body[: items[0][0].start()].strip() if items else paragraph_body
                    )
                    if not items:
                        add(title + "\n" + paragraph_body, parent, base, coverage, marker)
                        continue
                    result.nodes[parent] = {
                        **common,
                        "node_id": parent,
                        "parent_id": base,
                        "coverage_section": coverage,
                        "paragraph": marker,
                        "chunk_text": title + "\n" + paragraph_body,
                    }
                    for im, item_body in items:
                        item_id = parent + "/" + im.group(1)
                        if item_id in result.nodes:
                            # 부록/개정 예시의 번호 재시작도 별도 주소로 보존한다.
                            item_id += "/occurrence" + str(
                                sum(n.startswith(item_id) for n in result.nodes)
                            )
                        # 목·다만·단서는 검색 호와 같이 둔다. 목은 별도 주소로도 추적할 수 있다.
                        add(
                            title + "\n" + head + "\n" + item_body,
                            item_id,
                            parent,
                            coverage,
                            marker,
                            im.group(1),
                            head,
                        )
                        for mm, mok in _spans(r"(?m)^[ \t]*([가-하])\.[ \t]+", item_body):
                            mid = item_id + "/" + mm.group(1)
                            result.nodes[mid] = {
                                **common,
                                "node_id": mid,
                                "parent_id": item_id,
                                "chunk_text": mok,
                                "coverage_section": coverage,
                                "paragraph": marker,
                                "item": im.group(1),
                            }
    # 정의는 원문에 명시된 표제/강조 용어만 수집한다. LLM이 정의를 만들어 넣지 않는다.
    for chunk in result.chunks:
        if not chunk.is_definition:
            continue
        terms = re.findall(r"\*\*([^*]+)\*\*\s*[:：]", chunk.chunk_text)
        # 펼쳐진 TXT 표의 짧은 단독 셀 다음에는 정의 설명이 온다.
        if chunk.source_path.endswith(".txt"):
            lines = chunk.chunk_text.splitlines()
            terms += [
                line.strip()
                for i, line in enumerate(lines[:-1])
                if re.fullmatch(r"[가-힣· ]{2,20}", line.strip())
                and len(lines[i + 1].strip()) > 25
                and line.strip() not in {"용 어", "정  의"}
            ]
        terms += re.findall(
            r"[“「]([^”」]{1,30})[”」](?:이?라\s*함은|이?란|는|은)", chunk.chunk_text
        )
        if not terms and chunk.item:
            term = re.search(r"(?m)^\s*\d+\.\s*([^\n:：]{1,30})[:：]", chunk.chunk_text)
            if term:
                terms.append(term.group(1))
        for term in terms:
            result.definitions.setdefault(term.strip(), []).append(chunk.node_id)
    # 준용은 명시된 문서명으로만 연결한다. 표준약관과 상품 요약을 동일 문서로 취급하지 않는다.
    documents = {c.source_path: c for c in result.chunks}
    fallback = {}
    for c in result.chunks:
        if "준용" not in c.title and not (c.authority_level == 2 and "표준약관" in c.chunk_text):
            continue
        targets = []
        if "생명보험 표준약관" in c.chunk_text:
            targets += [p for p in documents if p.endswith("std_life_insurance.txt")]
        if "주계약" in c.chunk_text:
            targets += [p for p in documents if "/gaon/00_" in p]
        fallback.setdefault(c.source_path, []).extend(targets)
    for chunk in result.chunks:
        chunk.governs = [chunk.coverage_section] if chunk.coverage_section else [chunk.doc_name]
        chunk.falls_back_to = sorted(set(fallback.get(chunk.source_path, [])))
        chunk.defined_terms = [term for term in result.definitions if term in chunk.chunk_text]
        result.nodes[chunk.node_id] = chunk.payload()
    return result


def load_chunks(root: Path, max_chars: int = 1800) -> list[Chunk]:
    # 이전 호출부 호환 인자다. 길이로 문장을 자르면 단서/항 맥락을 잃으므로 사용하지 않는다.
    return load_structure(root).chunks


def chunk_id(hit):
    """조각의 위치와 원문이 같을 때만 동일 ID다. 출처 이름 변경도 지문에 반영한다."""
    return (
        hit.get("chunk_id")
        or hit.get("node_id")
        or hashlib.sha256(
            (hit["source_path"] + "\0" + hit["article"] + "\0" + hit["chunk_text"]).encode()
        ).hexdigest()[:24]
    )
