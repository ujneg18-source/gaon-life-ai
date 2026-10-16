"""화면용 근거/이슈만 조립한다. 평가용 인용·KB·엔진 결과는 수정하지 않는다."""

import re

from app.agent.kb import load_chunks
from app.schemas.chat import DisplayClaimRef
from app.services.coverage import citation


def address(text):
    """항·호 표기만 통일하고 임상 코드/숫자는 바꾸지 않는다."""
    # 숫자로 쓴 항도 같은 주소로 표시하되 단독 숫자나 질병코드는 건드리지 않는다.
    text = re.sub(
        r"(제\d+조)\s*제?(\d{1,2})항",
        lambda m: f"{m[1]} {chr(ord('①') + int(m[2]) - 1)}" if 1 <= int(m[2]) <= 20 else m[0],
        text,
    )
    text = re.sub(r"([①-⑳])\s*항\s*", r"\1 ", text)
    return re.sub(r"([①-⑳])\s*제(\d+)호", r"\1 \2호", text)


def readable_quote(text, config):
    """표는 해당 조각의 머리글과 행으로만 읽는다. HTML을 실행하지 않는다."""
    for code, name in config.CHAT_RULE_LABELS.items():
        text = re.sub(r"\b" + re.escape(code) + r"\b", name, text)
    text = re.sub(r"FIELD-([\w.-]+)", "추출 정보 확인", text)
    text = (
        text.replace("정규화", "정보 정리")
        .replace("스키마", "입력 형식")
        .replace("issue_id", "검토 항목 번호")
    )
    lines, headers = [], None
    source = text.splitlines()
    for n, line in enumerate(source):
        if line.strip().startswith("|"):
            cells = [v.strip().replace("**", "") for v in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r"[- :]+", v or "-") for v in cells):
                continue
            if n + 1 < len(source) and re.match(r"^\s*\|[\s:|-]+\|\s*$", source[n + 1]):
                headers = cells
            elif headers and len(headers) == len(cells):
                lines.append("\n".join(f"{k}: {v}" for k, v in zip(headers, cells)))
                lines.append("")
            else:
                lines.append("\n".join(cells))
        else:
            lines.append(re.sub(r"^#{1,6}\s*", "", line).replace("**", ""))
    return "\n".join(lines).strip()


def present(agent, state):
    result = state["result"]
    text = address(result.answer)
    # 고객에게 보내는 문자 원문은 그대로 편집하고, 화면에만 출처 설명을 붙인다.
    display_text = text
    if result.intent == "draft" and result.citations:
        display_text = text + "\n\n(업무 기준: 보완 요청 표준 문구 2장)"
    if result.refused and result.citations:
        source = result.citations[0]
        if "매뉴얼" in source.doc_name:
            intro, *rest = text.split("\n\n")
            display_text = (
                intro
                + f" (업무 기준: 보상 업무 매뉴얼 {source.article})"
                + ("\n\n" + "\n\n".join(rest) if rest else "")
            )
    chunks = [c.payload() for c in load_chunks(agent.config.KB_PATH)]
    compact = lambda s: re.sub(r"\s|항", "", address(s))
    references = list(re.finditer(r"\(([^()\n]*(?:제\d+조|\d+장)[^()\n]*)\)", display_text))
    shown, seen = [], set()
    aliases_by_path = dict(agent.config.CHAT_CITATION_ALIASES)
    for original in result.citations:
        path = original.source_path.rsplit("/", 1)[-1]
        aliases_by_path[path] = (*aliases_by_path.get(path, ()), original.doc_name)
    for reference in references:
        ref = reference.group(1)
        for path, aliases in aliases_by_path.items():
            if not any(compact(alias) in compact(ref) for alias in aliases):
                continue
            match = re.search(r"제\d+조(?:\s*[①-⑳])?(?:\s*\d+호)?|\d+장", ref)
            if not match:
                continue
            requested = address(match.group()).strip()
            base = re.search(r"제\d+조|\d+장", requested).group()
            options = [
                c for c in chunks if c["source_path"].endswith(path) and c["article"] == base
            ]
            # 같은 제4조라도 상해/질병이 다르면 다른 근거다. 본문의 종목이나 원래
            # 인용의 유일한 종목으로만 좁히고, 애매하면 임의로 질병을 고르지 않는다.
            sections = {c.get("coverage_section") for c in options if c.get("coverage_section")}
            if len(sections) > 1:
                explicit = [section for section in sections if compact(section) in compact(ref)]
                original_sections = {
                    c.coverage_section
                    for c in result.citations
                    if c.source_path.endswith(path) and c.coverage_section
                }
                if not original_sections:
                    # 청구 답변은 평가용 인용 수와 별개로 저장된 이슈의 원문 근거도 쓴다.
                    evidence_texts = {
                        evidence.get("text")
                        for issue in state.get("evidence", {}).get("issues", [])
                        for evidence in issue.get("evidence", [])
                        if evidence.get("source_path", "").endswith(path)
                    }
                    original_sections = {
                        c.get("coverage_section")
                        for c in options
                        if c["chunk_text"] in evidence_texts
                    }
                selected_section = (
                    explicit[0]
                    if len(explicit) == 1
                    else next(iter(original_sections))
                    if len(original_sections) == 1
                    else None
                )
                options = [c for c in options if c.get("coverage_section") == selected_section]
            exact = [
                c for c in options if compact(c.get("address", c["article"])) == compact(requested)
            ]
            candidates = exact or [
                c for c in options if compact(c.get("address", "")).startswith(compact(requested))
            ]
            if candidates:
                key = (path, requested)
                if key not in seen:
                    shown.append(
                        citation(candidates[0]).model_copy(
                            update={
                                "article": requested,
                                "display_quote": readable_quote(
                                    "\n\n".join(dict.fromkeys(c["chunk_text"] for c in candidates)),
                                    agent.config,
                                ),
                            }
                        )
                    )
                    seen.add(key)
    # 전체 문서명이 포함된 기존 인용도 처리한다. 괄호 밖 조항은 원문 위치 순서로 읽는다.
    if not shown:
        for original in sorted(result.citations, key=lambda c: display_text.find(c.doc_name)):
            article = address(original.article)
            if original.doc_name in display_text and article in display_text:
                shown.append(
                    original.model_copy(
                        update={"display_quote": readable_quote(original.quote, agent.config)}
                    )
                )
    issues = state.get("evidence", {}).get("issues", [])
    cid = state.get("claim_id") or next((c.claim_id for c in result.claim_refs), None)
    refs, used = [], set()
    rules = {i["rule_id"] for i in issues}
    for issue in issues:
        rule = issue["rule_id"]
        if rule == "CV-03" and "FIELD-diagnosis_code" in rules:
            continue  # 같은 코드 원인의 병합 항목은 대표 링크 하나로 표시한다.
        title = re.sub(r"\s*\([^)]*\)", "", issue["title"])
        if issue["kind"] == "missing":
            term = title.replace(" 미제출", "").replace(" 누락", "")
            label = term + " 누락"
        elif rule == "coverage":
            term = title.replace(" 보상 제외 가능성", "")
            label = term + " 보상 여부"
        else:
            term = agent.config.CLAIM_REVIEW_LABELS.get(rule, title)
            label = {
                "FIELD-diagnosis_code": "질병분류기호 세분류 확인",
                "CV-01": "진단일과 병리 보고일 확인",
                "CV-02": "입원일수 차이 확인",
            }.get(rule, title)
            if rule == "CV-02":
                term = "입원일수"
        if cid and term in text and label not in used:
            refs.append(DisplayClaimRef(claim_id=cid, issue_id=issue["id"], label=label))
            used.add(label)
    return {
        "result": result.model_copy(
            update={
                "answer": text,
                "display_answer": display_text,
                "display_citations": shown,
                "display_claim_refs": refs,
            }
        )
    }
