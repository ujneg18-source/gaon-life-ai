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
