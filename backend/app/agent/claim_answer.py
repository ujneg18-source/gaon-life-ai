"""저장된 검토 결과를 담당자용 문단으로 표시한다. 새 심사나 질문 문장 분기는 하지 않는다."""

import re

from app.agent.kb import load_chunks
from app.services.presentation import document_label


def clean(text):
    """내부 식별자는 본문에서만 숨긴다. 원본 이슈와 근거 인용은 수정하지 않는다."""
    text = re.sub(r"\bCV-0\d\b|FIELD-[\w.-]+|\b[a-z]+(?:_[a-z]+)+\b", "", str(text))
    return text.replace("·", " 및 ").replace("→", ", ").strip(" :.,")


def render_claim(claim, issues, documents, config, *, as_rows=False):
    """규칙 결과별 표시 템플릿. 같은 진단서의 코드 원인만 합치고 서로 다른 이슈는 보존한다."""
    if not claim["submitted_count"]:
        if as_rows:
            return []
        return f"{claim['customer_name']}({claim['claim_id']}) 고객님은 아직 서류를 제출하지 않았습니다.\n\n서류가 접수되면 필요한 서류와 검토 사항을 확인하겠습니다.\n\n필요하시다면 접수 안내를 진행해 주세요."
    by_type = {}
    for doc in documents:
        by_type.setdefault(doc.doc_type, []).append(doc)
    value = lambda kind, key: next(
        (d.values.get(key) for d in by_type.get(kind, []) if d.values.get(key) is not None), None
    )
    missing = [i for i in issues if i["kind"] == "missing"]
    labels = list(
        dict.fromkeys(
            clean(i["title"]).replace(" 미제출", "").replace(" 누락", "") for i in missing
        )
    )
    conclusion = f"{claim['customer_name']}({claim['claim_id']}) 고객님은 서류 {claim['submitted_count']}건을 제출했고, "
    conclusion += (
        f"추가로 받아야 할 서류가 {len(labels)}건 있습니다."
        if labels
        else "추가로 받을 서류는 없습니다."
    )
    blocks = [conclusion]
    for label in labels:
        if "수술확인서" in label:
            operations = [
                str(i.get("name", ""))
                for d in by_type.get("medical_detail", [])
                for i in d.values.get("items", [])
                if i.get("category") == "surgery"
            ]
            reason = (
                "세부내역서에 수술 기록"
                + ("(" + ", ".join(operations) + ")" if operations else "")
                + "이 있지만 수술확인서가 제출되지 않았습니다."
            )
        else:
            reason = f"필수 서류인 {label}가 제출되지 않았습니다."
        blocks.append(f"추가 서류: {label}\n{reason} 보완 요청이 필요합니다.")
    chunks = load_chunks(config.KB_PATH)

    def law(rule):
        # 조문이 실제 KB에 있고 해당 항을 포함할 때만 괄호 근거를 표시한다.
        entry = config.CLAIM_DISPLAY_SOURCES.get(rule)
        if not entry:
            return ""
        path, article, marker, address = entry
        return (
            " (" + address + ")"
            if any(
                c.source_path.endswith(path) and c.article == article and marker in c.chunk_text
                for c in chunks
            )
            else ""
        )

    rows = []
    display_rows = [
        {
            "id": i["id"],
            "kind": i["kind"],
            "title": clean(i["title"])
            .replace(" 미제출", " 누락")
            .replace("필수 서류 미제출: ", ""),
            "detail": "보완 요청이 필요합니다.",
            "doc_ids": i["doc_ids"],
        }
        for i in missing
    ]
    code_issue = next((i for i in issues if i["rule_id"] == "FIELD-diagnosis_code"), None)
    merged = set()
    if code_issue:
        # 같은 진단서의 세분류 누락과 병리 부합 확인은 한 항목에 담되 확인 과제는 남긴다.
        related = [
            i
            for i in issues
            if i["rule_id"] == "CV-03" and set(i["doc_ids"]) & set(code_issue["doc_ids"])
        ]
        merged = {i["id"] for i in related}
    for issue in issues:
        rule, kind = issue["rule_id"], issue["kind"]
        if kind == "missing" or issue["id"] in merged:
            continue
        title, body = "", ""
        if rule == "FIELD-diagnosis_code":
            code = value("diagnosis", "diagnosis_code")
            longer = sorted(
                {
                    m
                    for d in documents
                    for m in re.findall(r"\b[A-Z]\d{2}\.\d+\b", d.source_text)
                    if code and m.startswith(str(code) + ".")
                }
            )
            title = "진단서: 질병분류기호 확인"
            body = (
                f"추출된 값({code})이 {next((document_label(d.doc_type, config) for d in documents if any(m in d.source_text for m in longer)), '제출 서류')} 원문({', '.join(longer)})과 다릅니다. "
                if code and longer
                else clean(issue["detail"]) + ". "
            )
            body += "세분류가 빠졌을 수 있으니 원문과 같은지 확인해 주세요."
            if merged:
                body = (
                    body.removesuffix(" 확인해 주세요.")
                    + " 확인하고, 병리 진단명과도 함께 대조해 주세요."
                )
        elif rule == "CV-01":
            title = "진단서 · 조직검사 결과지: 진단일과 병리 보고일 확인"
            body = (
                f"진단일({value('diagnosis', 'diagnosis_date')})이 병리 보고일({value('pathology', 'report_date')})보다 빠릅니다. 진단확정일은 병리 보고일 기준이므로 진료 기록으로 경위를 확인해 주세요."
                + law(rule)
            )
        elif rule == "CV-02":
            title = "입퇴원확인서 · 세부내역서: 입원일수 차이"
            a, b = value("admission", "stay_days"), value("medical_detail", "inpatient_days")
            body = f"입퇴원확인서는 {a}일, 세부내역서는 {b}일로 "
            body += (
                f"{abs(a - b)}일 차이가 있습니다. "
                if isinstance(a, int) and isinstance(b, int)
                else "기록이 서로 다릅니다. "
            )
            body += (
                "산정 방식 차이일 수 있어 불일치로 보지 않았습니다."
                if kind == "info"
                else "입원일수와 입원일 및 퇴원일을 원본에서 확인해 주세요."
            ) + law(rule)
        elif rule == "coverage":
            title = "영수증 · 처방전: " + re.sub(
                r"\s*\([^)]*\)", "", clean(issue["title"])
            ).replace(" 보상 제외 가능성", " 보상 여부")
            item = re.sub(
                r"\s*\([^)]*\)", "", clean(issue["title"]).replace(" 보상 제외 가능성", "")
            )
            reason = clean(issue["detail"].split(". ")[0])
            reason = re.sub(r"(?:이에요|입니다|예요)$", "", reason)
            body = (
                f"{item}은 {reason}으로 분류되어 보상 제외 가능성이 있습니다. 치료 목적 등 예외 여부를 확인하고, 필요하시다면 지급 심사로 이관할 때 메모를 함께 남겨 주세요."
                + law(rule)
            )
        else:
            names = list(
                dict.fromkeys(
                    document_label(d.doc_type, config)
                    for d in documents
                    if d.id in issue["doc_ids"]
                )
            )
            title = (" · ".join(names) or "제출 서류") + ": " + clean(issue["title"])
            body = clean(issue["detail"]).replace("이에요", "입니다").replace("해요", "합니다")
            if not body.endswith(("다", "요", ".")):
                body += " 내용을 확인해 주세요"
            body = body.rstrip(".") + "."
        priority = 2 if kind == "info" else 1 if kind == "excluded_item" else 0
        rows.append((priority, title, body))
        display_rows.append(
            {
                "id": issue["id"],
                "kind": kind,
                "title": title,
                "detail": body,
                "doc_ids": issue["doc_ids"],
            }
        )
    if as_rows:
        return sorted(
            display_rows,
            key=lambda i: {"missing": 0, "excluded_item": 2, "info": 3}.get(i["kind"], 1),
        )
    if rows:
        blocks.append("그 외 검토 사항은 다음과 같습니다.")
        for n, (_, title, body) in enumerate(sorted(rows, key=lambda row: row[0]), 1):
            number = chr(0x2460 + n - 1) if n <= 20 else str(n) + "."
            blocks.append(f"{number} {title}\n{body}")
    if labels:
        blocks.append(", ".join(labels) + " 보완 요청 문구를 작성해 드릴까요?")
    else:
        blocks.append("필요하시다면 청구 상세에서 검토 기록을 남겨 주세요.")
    return "\n\n".join(blocks)
