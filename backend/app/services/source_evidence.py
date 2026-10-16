"""원문 표와 코드의 직접 근거를 읽는다. 정답이나 파일명으로 값을 추정하지 않는다."""

import re
from html.parser import HTMLParser


def codes(text: str) -> set[str]:
    return set(re.findall(r"(?<![A-Z0-9])[A-Z]\d{2}(?:\.\d{1,2})?(?!\d)", text.upper()))


def longer_code(value: str, text: str) -> bool:
    """C18과 C18.7은 다른 코드다. 더 긴 동일 계열 코드가 있으면 확정을 요구한다."""
    return any(code.startswith(value + ".") for code in codes(text))


class TableRows(HTMLParser):
    """Parse가 보존한 표의 셀 경계를 사용한다. 전체 텍스트의 급여 단어로 행을 추측하지 않는다."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        if tag in {"td", "th"}:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        if tag == "tr" and self.row:
            self.rows.append(self.row)


def pharmacy_evidence(values: dict, parsed: dict, canonical) -> dict:
    evidence = {}
    for el in parsed.get("elements", []):
        parser = TableRows()
        parser.feed(el.get("content", {}).get("html", ""))
        headers = None
        for row in parser.rows:
            if "구분" in row and any(x in row for x in ("품명", "약품명")):
                headers = row
                continue
            if not headers or len(row) != len(headers):
                continue
            record = dict(zip(headers, row))
            name = record.get("품명", record.get("약품명", ""))
            if record.get("구분") not in {"급여", "비급여"}:
                continue
            matches = [
                i
                for i, item in enumerate(values.get("items", []))
                if canonical(item.get("drug_name", "")) == canonical(name)
            ]
            if len(matches) != 1:
                continue  # 동명 행이 여럿이면 임의 연결하지 않는다.
            i = matches[0]
            key = f"items[{i}].covered"
            evidence[key] = {
                "value": record["구분"] == "급여",
                "text": record["구분"],
                "element_id": el.get("id"),
                "page": el.get("page", 1),
                "coordinates": el.get("coordinates"),
                "basis": "Parse 표의 품명·구분 칸",
            }
    return evidence


def added_diagnosis_words(value: str, source: str) -> bool:
    """공백·괄호 차이는 허용하되 새 번역/수식어는 원문 존재를 요구한다."""
    import unicodedata

    normalize = lambda text: re.sub(
        r"[\s()（）]+", "", unicodedata.normalize("NFKC", text).casefold()
    )
    if not value or normalize(value) in normalize(source):
        return False
    words = re.findall(r"[a-zA-Z]+|[가-힣]+", value)
    # 문서 전체에 같은 낱말이 있더라도 연속된 진단명을 찾지 못하면 확인을 요구한다.
    return bool(words)
