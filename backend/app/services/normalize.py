"""추출값을 정규화하고 형식·원문·모델 신뢰도·좌표를 독립적으로 확인한다."""

import html
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from pydantic import ValidationError
from sqlmodel import Session

from app.models import ExtractedField, FieldMethod, KcdCode
from app.schemas.documents import DOCUMENT_SCHEMAS, CommonDoc
from app.services.source_evidence import longer_code, pharmacy_evidence


def additional_values(message: dict) -> dict:
    """Extract는 JSON 문자열, Classify는 객체 arguments가 실측돼 두 형식을 명시적으로 받는다."""
    extras = {}
    for call in message.get("tool_calls") or []:
        function = call.get("function", {})
        if function.get("name") == "additional_values":
            value = function.get("arguments", {})
            if isinstance(value, str):
                value = json.loads(value)
            if not isinstance(value, dict):
                raise TypeError("additional_values는 객체여야 합니다.")
            extras.update(value)
    return extras


def completion_values(response: dict) -> tuple[dict, dict]:
    """잘린 JSON·여러 건 응답은 단일 문서 값으로 오인하지 않는다."""
    if len(response["choices"]) != 1:
        raise ValueError("단일 문서 응답이 필요합니다.")
    choice = response["choices"][0]
    if choice.get("finish_reason") not in {None, "stop"}:
        raise ValueError("추출 응답이 완료되지 않았습니다.")
    message = choice["message"]
    values = json.loads(message.get("content") or "{}")
    if not isinstance(values, dict):
        raise TypeError("Extract content는 객체여야 합니다.")
    return values, additional_values(message)


def flatten(data: Any, prefix: str = "") -> dict[str, Any]:
    """객체 배열은 items[0].amount 같은 키로 저장해 각 셀의 근거와 검수 사유를 보존한다."""
    if isinstance(data, dict):
        return {
            k2: v2
            for k, v in data.items()
            for k2, v2 in flatten(v, f"{prefix}.{k}" if prefix else k).items()
        }
    if isinstance(data, list):
        return {
            k2: v2 for i, v in enumerate(data) for k2, v2 in flatten(v, f"{prefix}[{i}]").items()
        }
    return {prefix: data}


def canonical(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = re.sub(r"(?<=\d)[년월일]", "", text)
    return re.sub(r"[\W_]", "", text)


def element_text(element: dict) -> str:
    content = element.get("content", {})
    return html.unescape(
        re.sub(
            r"<[^>]+>",
            " ",
            content.get("html") or content.get("text") or content.get("markdown") or "",
        )
    )


def normal_scalar(key: str, value: Any) -> Any:
    """명시적 날짜·코드·금액만 정규화한다. 잘못된 날짜를 추정해서 고치지 않는다."""
    if value is None or value == "":
        return None
    name = re.sub(r"\[\d+\]", "", key.rsplit(".", 1)[-1])
    if isinstance(value, str):
        value = value.strip()
    if name.endswith("_date") or name in {"period_start", "period_end", "visit_dates", "date"}:
        raw = re.sub(r"[년월./]", "-", str(value)).replace("일", "").replace(" ", "").rstrip("-")
        parts = raw.split("-")
        if len(parts) != 3:
            raise ValueError("날짜 형식")
        return date(*map(int, parts)).isoformat()
    if name == "diagnosis_code":
        raw = re.sub(r"\s", "", str(value)).upper()
        if re.fullmatch(r"[A-Z]\d{3,4}", raw):
            raw = raw[:3] + "." + raw[3:]
        return raw
    if name in {
        "covered_copay",
        "covered_nhis",
        "non_covered",
        "total",
        "patient_total",
        "amount",
        "days",
        "stay_days",
        "inpatient_days",
        "per_day",
    }:
        if isinstance(value, bool):
            raise ValueError("숫자 대신 논리값")
        return int(re.sub(r"[,원₩\s]", "", str(value)))
    if name == "category" and str(value) in {"처치 및 수술료", "수술료", "수술", "surgery"}:
        return "surgery"
    if name == "covered" and isinstance(value, str):
        if value in {"급여", "true"}:
            return True
        if value in {"비급여", "false"}:
            return False
    return value


def _normalize_tree(value: Any, key: str, errors: set[str]) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_tree(v, f"{key}.{k}" if key else k, errors) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_tree(v, f"{key}[{i}]", errors) for i, v in enumerate(value)]
    try:
        return normal_scalar(key, value)
    except (ValueError, TypeError, OverflowError):
        errors.add(key)
        return value


def _extra_at(extras: dict, key: str) -> dict:
    node: Any = extras
    for part in re.findall(r"[^.\[\]]+", key):
        # 배열 자체가 _value로 감싸진 응답도 셀별 메타데이터를 따라간다.
        if isinstance(node, dict) and isinstance(node.get("_value"), (dict, list)):
            node = node["_value"]
        if isinstance(node, list) and part.isdigit():
            node = node[int(part)] if int(part) < len(node) else {}
        elif isinstance(node, dict):
            node = node.get(part, {})
        else:
            return {}
    return node if isinstance(node, dict) else {}


def valid_box(points: Any) -> list[dict[str, float]] | None:
    if not isinstance(points, list) or not points:
        return None
    if all(
        isinstance(p, dict)
        and isinstance(p.get("x"), (int, float))
        and isinstance(p.get("y"), (int, float))
        for p in points
    ):
        if not all(0 <= p["x"] <= 1 and 0 <= p["y"] <= 1 for p in points):
            return None
        if len(points) == 4:
            return points  # 단일 word의 기울어진 꼭짓점은 축 정렬 사각형으로 바꾸지 않는다.
        xs, ys = [p["x"] for p in points], [p["y"] for p in points]
        return [
            {"x": min(xs), "y": min(ys)},
            {"x": max(xs), "y": min(ys)},
            {"x": max(xs), "y": max(ys)},
            {"x": min(xs), "y": max(ys)},
        ]
    return None


def extra_location(extra: dict) -> tuple[int, list | None]:
    loc = extra.get("location", extra)
    if isinstance(loc, list):
        loc = loc[0] if loc else {}
    if not isinstance(loc, dict):
        return 1, None
    words = loc.get("word_coordinates") or extra.get("word_coordinates")
    page = loc.get("page", extra.get("page", 1))
    box = valid_box(words)
    if box:
        return max(int(page or 1), 1), box
    if isinstance(words, list):

        def word_points(node):
            if isinstance(node, list):
                return [p for item in node for p in word_points(item)]
            if isinstance(node, dict):
                if "x" in node and "y" in node:
                    return [node]
                return word_points(node.get("coordinates", []))
            return []

        # 실측 word_coordinates는 [[꼭짓점 4개], ...]이다. 여러 word는 합친 영역을 쓴다.
        box = valid_box(word_points(words))
    return max(int(page or 1), 1), box or valid_box(loc.get("coordinates"))


@dataclass
class NormalizationResult:
    """values는 규칙용, fields는 저장·뷰어용이다. 검증 실패 항목도 버리지 않는다."""

    values: dict
    fields: list[ExtractedField]
    kcd_names: dict[str, str]
    evidence: dict = field(default_factory=dict)


def normalize_document(
    doc_type: str,
    values: dict,
    extras: dict,
    parsed: dict,
    document_id: int,
    *,
    is_data: bool = False,
    session: Session | None = None,
) -> NormalizationResult:
    model = DOCUMENT_SCHEMAS.get(doc_type, CommonDoc)
    values = {k: v for k, v in values.items() if k in model.model_fields}
    errors: set[str] = set()
    candidate = _normalize_tree(values, "", errors)
    evidence = (
        pharmacy_evidence(candidate, parsed, canonical)
        if doc_type == "pharmacy_receipt" and not is_data
        else {}
    )
    for key, proof in evidence.items():
        index = int(re.search(r"\[(\d+)\]", key).group(1))
        candidate["items"][index]["covered"] = proof["value"]
    try:
        normalized = model.model_validate(candidate).model_dump(mode="json", exclude_none=True)
    except ValidationError as error:
        for item in error.errors():
            key = ""
            for part in item["loc"]:
                key += f"[{part}]" if isinstance(part, int) else ("." if key else "") + str(part)
            errors.add(key)
        normalized = candidate
    raw = flatten(values)
    flat = flatten(normalized)
    # 필수 항목 자체가 빠졌을 때도 빈 필드로 남겨 자동 통과하지 않게 한다.
    for key in errors:
        flat.setdefault(key, None)
    elements = [(el, canonical(element_text(el))) for el in parsed.get("elements", [])]
    fields = []
    names = {}
    for key, value in flat.items():
        if value is None and key not in errors:
            continue
        extra = _extra_at(extras, key)
        confidence = extra.get("confidence")
        confidence = confidence if confidence in {"high", "low"} and not is_data else None
        raw_value = raw.get(key)
        queries = {canonical(v) for v in (raw_value, value) if v is not None and str(v) != ""}
        if isinstance(value, bool):
            queries = {"급여" if value else "비급여"}
        if key.endswith("diagnosis_code"):
            # C18이 C18.7의 부분 문자열이라는 이유만으로 원문에 있다고 판단하지 않는다.
            matches = [
                (el, text)
                for el, text in elements
                if canonical(value)
                in {
                    canonical(code)
                    for code in re.findall(r"[A-Z]\d{2}(?:\.\d{1,2})?", element_text(el).upper())
                }
            ]
        else:
            matches = [(el, text) for el, text in elements if any(q and q in text for q in queries)]
        found = is_data or bool(matches)
        page, box = extra_location(extra)
        if box is None and matches:
            page = matches[0][0].get("page", 1)
            box = valid_box(matches[0][0].get("coordinates"))
        reasons = []
        if key in evidence:
            # 모델의 low를 high로 위조하지 않는다. 별도 Parse 표 근거로 판정하고 원 응답은 보존한다.
            proof = evidence[key]
            confidence = None
            found = True
            page = proof["page"]
            box = valid_box(proof.get("coordinates"))
        if key.endswith("diagnosis_code") and longer_code(
            str(value), " ".join(element_text(el) for el, _ in elements)
        ):
            found = False
            reasons.append("원문과 다름(세분류 누락)")
        if confidence == "low":
            reasons.append("low_conf")
        if not found:
            reasons.append("not_in_source")
        if key in errors:
            reasons.append("format")
        fields.append(
            ExtractedField(
                document_id=document_id,
                key=key,
                value=json.dumps(value, ensure_ascii=False)
                if not isinstance(value, str)
                else value,
                raw_value="" if raw_value is None else str(raw_value),
                extract_conf=confidence,
                source_found=found,
                review_reasons=reasons,
                method=FieldMethod.DATA if is_data else FieldMethod.PARSE,
                page=page,
                bbox=box,
            )
        )
        if key.endswith("diagnosis_code") and session is not None:
            ref = session.get(KcdCode, value)
            if ref:
                names[key] = ref.name
    return NormalizationResult(normalized, fields, names, evidence)
