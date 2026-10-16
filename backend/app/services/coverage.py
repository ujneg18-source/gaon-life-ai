"""처방 대조와 매뉴얼 근거만 제시한다. 보상 확정·지급액 계산은 하지 않는다."""

import re

from app.schemas.chat import Citation


def citation(hit):
    return Citation(
        doc_name=hit["doc_name"],
        article=hit["article"],
        source_path=hit["source_path"],
        is_mock=hit["is_mock"],
        quote=hit["chunk_text"],
    )


def check_coverage(documents, item_name, kb):
    receipts = [d for d in documents if d.doc_type == "pharmacy_receipt"]
    prescriptions = [d for d in documents if d.doc_type == "prescription"]
    norm = lambda s: re.sub(r"\s", "", re.sub(r"\([^)]*\)", "", str(s))).casefold()
    matches = [
        item
        for d in receipts
        for item in d.values.get("items", [])
        if norm(item_name) == norm(item.get("drug_name", ""))
    ]
    prescribed = [
        item.get("drug_name", "") for d in prescriptions for item in d.values.get("items", [])
    ]
    in_prescription = any(norm(item_name) == norm(name) for name in prescribed)
    hits = kb.search("영양제 비타민제 보상하지 않는 사항 특별약관2 제4조", "policy", limit=12)
    rules = [
        h
        for h in hits
        if h["source_path"].endswith("std_silson_rider2_nonsevere_noncovered.txt")
        and h["article"] == "제4조"
        and "영양제" in h["chunk_text"]
    ]
    manual = kb.search("실손 비급여 처방전에 없는 일반의약품", "manual", limit=6)
    rules += [
        h
        for h in manual
        if h["source_path"].endswith("10_claims_manual.md") and h["article"] == "6장"
    ][:1]
    # 명칭만으로 약을 분류하지 않고 저장된 영수증 분류와 문서의 영양제 기준을 함께 본다.
    vitamin = any(word in norm(item_name) for word in ("비타민", "영양제"))
    excluded = bool(
        matches
        and bool(prescriptions)
        and any(item.get("covered") is False for item in matches)
        and not in_prescription
        and vitamin
        and rules
    )
    status = "보상 제외 가능성" if excluded else "확인 필요"
    # 처방 일치만으로 급여·보상 가능을 단정하지 않는다. 치료목적 자료가 없으면 확인 필요다.
    return {
        "item_name": item_name,
        "found": bool(matches),
        "prescribed": in_prescription,
        "prescription_available": bool(prescriptions),
        "status": status,
        "citations": [citation(h).model_dump() for h in rules[:2]],
        "reason": "처방전에 없음"
        if prescriptions and not in_prescription
        else "처방전과 치료 목적 확인 필요",
    }


def coverage_issues(claim, documents, config):
    """영수증 비급여·일반의약품 표기와 처방전을 결정적으로 대조해 저장할 과제를 만든다."""
    from app.agent.kb import load_chunks
    from app.models import Issue, IssueKind

    rx = [d for d in documents if d.doc_type == "prescription"]
    if not rx:
        return []  # 처방전 자체가 없으면 약 부재를 단정하지 않고 필수서류 규칙으로 보낸다.
    normalize = lambda value: re.sub(r"\s", "", re.sub(r"\([^)]*\)", "", str(value))).casefold()
    prescribed = {
        normalize(item.get("drug_name", "")) for d in rx for item in d.values.get("items", [])
    }
    candidates = [
        (d, i, item)
        for d in documents
        if d.doc_type == "pharmacy_receipt"
        for i, item in enumerate(d.values.get("items", []))
        if item.get("covered") is False
        and any(word in item.get("drug_name", "") for word in config.OTC_MARKERS)
        and normalize(item.get("drug_name", "")) not in prescribed
    ]
    if not candidates:
        return []
    # 배치 규칙은 네트워크를 쓰지 않는다. RAG와 동일 허용 목록의 원문에서 근거를 보존한다.
    chunks = load_chunks(config.KB_PATH, config.KB_CHUNK_MAX_CHARS)
    texts = [
        c
        for c in chunks
        if c.source_path.endswith("std_silson_rider2_nonsevere_noncovered.txt")
        and c.article == "제4조"
        and "영양제" in c.chunk_text
    ]
    manual = [
        c for c in chunks if c.source_path.endswith("10_claims_manual.md") and c.article == "6장"
    ]
    evidence = [
        {
            "source": c.doc_name,
            "article": c.article,
            "text": c.chunk_text,
            "source_path": c.source_path,
            "is_mock": c.is_mock,
        }
        for c in texts[:1] + manual[:1]
    ]
    if not evidence:
        return []  # 근거 없는 보상 제외 가능성을 지어내지 않는다.
    return [
        Issue(
            claim_id=claim.id,
            kind=IssueKind.EXCLUDED_ITEM,
            rule_id="coverage",
            title=f"{item['drug_name']} 보상 제외 가능성",
            detail="처방전에 없는 일반의약품·비급여 항목이에요. 치료 목적 등 예외 여부를 담당자가 확인해 주세요.",
            doc_ids=[d.id, rx[0].id],
            field_keys=[f"items[{i}].drug_name"],
            evidence=evidence,
        )
        for d, i, item in candidates
    ]
