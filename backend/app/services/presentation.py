"""담당자용 항목·사유 이름. 규칙 코드와 검증 방식 설명은 내부 코드에 유지한다."""

import re


def field_label(key, config):
    name = key.rsplit(".", 1)[-1]
    text = config.FIELD_LABELS.get(name, name)
    match = re.search(r"\[(\d+)\]", key)
    return f"항목 {int(match[1]) + 1} · {text}" if match else text


def document_label(code, config):
    return config.UPSTAGE_DOC_CLASSES.get(code, "해당 서류").split(".")[0]


def review_reason(reason):
    return {
        "low_conf": "추출한 값을 원본에서 확인해 주세요.",
        "not_in_source": "추출한 값과 원문이 같은지 확인해 주세요.",
        "format": "날짜·코드·금액의 형식을 확인해 주세요.",
    }.get(reason, reason)
