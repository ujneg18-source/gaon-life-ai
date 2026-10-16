"""기존 3고객 실제 캐시만 재생해 추출 정확도와 오류 검수 분류행렬을 계산한다."""

import json

from app.config import get_settings
from app.services.normalize import flatten, normal_scalar
from scripts.samples.verify_samples import evaluate_rows, prepared_rows


def confusion(rows):
    """오류값=양성. 예측 양성은 엔진이 필드 확인 필요로 표시한 경우다. 0분모는 N/A."""
    tp = sum(r["wrong"] and r["flagged"] for r in rows)
    fp = sum(not r["wrong"] and r["flagged"] for r in rows)
    fn = sum(r["wrong"] and not r["flagged"] for r in rows)
    tn = sum(not r["wrong"] and not r["flagged"] for r in rows)
    return {
        "fields": len(rows),
        "correct": tn + fp,
        "accuracy": (tn + fp) / len(rows) if rows else None,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "flagged": tp + fp,
    }


def main():
    config = get_settings()
    manifest = json.loads(config.DEMO_CUSTOMERS_PATH.read_text())
    all_fields = []
    customers = []
    for slug in ["kim_yujeong", "lee_gaon", "han_nuri"]:
        profile = next(c for c in manifest["customers"] if c["sample_id"] == slug)
        rows, calls = prepared_rows(profile, config, cached=True)
        assert calls == 0
        review = evaluate_rows(profile, rows, config)
        fields = []
        for number, row in enumerate(rows, 1):
            truth = json.loads(
                (config.SAMPLES_ROOT / slug / "answers" / (row["stem"] + ".json")).read_text()
            )
            expected = {
                k: v
                for k, v in flatten(truth).items()
                if not k.startswith("_") and k not in ("doc_type", "source")
            }
            found = flatten(row["raw"]["normalized"])
            details = {f["key"]: f for f in row["fields"]}
            for key, value in expected.items():
                f = details.get(key, {})
                issues = [
                    i
                    for i in review.issues
                    if i.rule_id.startswith("FIELD-")
                    and number in i.doc_ids
                    and key in i.field_keys
                ]
                reasons = list(
                    dict.fromkeys(f.get("review_reasons", []) + [i.detail for i in issues])
                )
                fields.append(
                    {
                        "customer": slug,
                        "document": row["stem"],
                        "origin": row["origin"],
                        "field": key,
                        "expected": normal_scalar(key, value),
                        "actual": found.get(key),
                        "wrong": found.get(key) != normal_scalar(key, value),
                        "flagged": bool(reasons),
                        "reasons": reasons,
                    }
                )
        customers.append(
            {
                "customer": slug,
                "api_only": confusion([f for f in fields if f["origin"] == "upstage"]),
                "all_with_electronic_mock": confusion(fields),
            }
        )
        all_fields.extend(fields)
    api = [f for f in all_fields if f["origin"] == "upstage"]
    result = {
        "mode": "cached_only",
        "new_api_calls": 0,
        "definition": "정답 스칼라별 정규화 후 엄격 일치. 확인 필요=해당 필드 review_reasons 또는 FIELD-* 이슈. 업무상 날짜 불일치/CV 이슈는 추출 오류 검수로 세지 않음. 정답에 없는 선택 필드는 분모 제외.",
        "api_only": confusion(api),
        "all_with_electronic_mock": confusion(all_fields),
        "customers": customers,
        "fields": all_fields,
    }
    out = config.EVAL_OUTPUT_PATH
    out.mkdir(parents=True, exist_ok=True)
    (out / "extract_eval.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    lines = [
        "# 문서 추출 평가",
        "",
        result["definition"],
        "",
        "추출 API를 호출한 실제 PNG 7장, 고객3명. 원본 캐시 재생이며 신규 API0. 실손24 mock을 OCR 성능 분모에 넣지 않는다.",
        "",
        "| 범위 | 일치/항목 | 정확도 | TP/FP/FN/TN | 정밀도 | 재현율 |",
        "|---|---|---|---|---|---|",
    ]

    def fmt(v):
        return "N/A" if v is None else f"{v:.2%}"

    for name, m in [
        ("실제 API만", result["api_only"]),
        ("전자 모의 포함", result["all_with_electronic_mock"]),
    ] + [(c["customer"], c["api_only"]) for c in customers]:
        lines.append(
            f"| {name} | {m['correct']}/{m['fields']} | {fmt(m['accuracy'])} | {m['tp']}/{m['fp']}/{m['fn']}/{m['tn']} | {fmt(m['precision'])} | {fmt(m['recall'])} |"
        )
    lines += ["", "## 불일치와 미검출 전부", ""]
    for f in api:
        if f["wrong"] or f["flagged"]:
            lines += [
                f"- {f['customer']} / {f['document']} / {f['field']}: 정답 `{f['expected']}`, 추출 `{f['actual']}`. 확인 필요={f['flagged']}, 사유={f['reasons']}"
            ]
    lines += [
        "",
        "C18.7→C18은 다른 서류의 Parse 원문과 교차 대조한 FIELD-diagnosis_code의 세분류 누락으로 검출된다. 개별 진단서 Parse도 C18로 읽어서 단일 문서 원문 대조만으로는 검출하지 못했다. 병리 결과의 괄호 번역 추가는 엄격 문자열 평가에서는 오류이나 의미상 동일할 수 있다. 이를 사후에 정답으로 바꾸지 않고 FN으로 남긴다. 따라서 적은 오류2건으로 계산한 정밀도/재현율은 일반화할 수 없다.",
        "",
    ]
    (out / "extract_eval.md").write_text("\n".join(lines))
    print(
        json.dumps(
            {k: result[k] for k in ["api_only", "all_with_electronic_mock"]}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
