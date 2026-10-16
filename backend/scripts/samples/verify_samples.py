"""폴더별 실제/모의 엔진 검증. --live는 명시된 2고객만 허용하며 기본은 정답 기반 mock이다."""

import argparse
import json
from collections import Counter
from pathlib import Path

from app.config import PROJECT_ROOT, get_settings
from app.models import Claim, CrossCheckRule, Policy, RequiredDocRule, ReviewSettings
from app.schemas.documents import DOCUMENT_SCHEMAS
from app.schemas.to_upstage import to_extract_schema
from app.services.normalize import completion_values, flatten, normal_scalar, normalize_document
from app.services.pipeline import classified_type
from app.services.rules import ReviewDocument, evaluate_claim
from app.services.upstage import UpstageClient


def profile(folder, config):
    manifest = json.loads(config.DEMO_CUSTOMERS_PATH.read_text())
    customer = next(
        c for c in manifest["customers"] if c["sample_id"] == folder.name or c["id"] == folder.name
    )
    return manifest, customer


def image_path(folder, stem, config, use_photo=False):
    if not use_photo:
        return folder / "png" / (stem + ".png")
    files = [
        p
        for p in (folder / "photo").glob(stem + ".*")
        if p.suffix.lower() in config.UPLOAD_EXTENSIONS
    ]
    if not files:
        return folder / "png" / (stem + ".png")
    if len(files) != 1:
        raise ValueError(f"사진 파일이 없거나 중복입니다: {folder.name}/{stem}")
    return files[0]


def prepared_rows(customer, config, *, live=False, cached=False, use_photo=False):
    """실제 경로는 정답을 추출 입력으로 쓰지 않는다. 모의 경로만 정답을 의도적으로 주입한다."""
    folder = config.SAMPLES_ROOT / customer["sample_id"]
    if live and customer["id"] not in ("DEMO-C001", "DEMO-C002", "DEMO-C006"):
        raise ValueError("이번 신규 실제 호출은 완결 건과 6번만 허용합니다")
    rows = []
    calls = 0
    client_config = config.model_copy(update={"USE_CACHED_RESULTS": cached})
    with UpstageClient(client_config) as api:
        for number, doc in enumerate(customer["documents"], 1):
            truth = json.loads((folder / "answers" / (doc["stem"] + ".json")).read_text())
            parsed, extras = {}, {}
            origin = "silson24" if doc["source"] == "silson24" else "mock"
            path = (
                image_path(folder, doc["stem"], config, use_photo)
                if doc["source"] == "image"
                else folder / "png" / (doc["stem"] + ".png")
            )
            raw = {"sample_id": customer["sample_id"]}
            if doc["source"] == "silson24" or not (live or cached):
                values = truth
                kind = truth["doc_type"]
            else:
                classification = api.classify(path)
                kind, _ = classified_type(classification)
                parsed = api.parse(path)
                extracted = api.extract(path, to_extract_schema(DOCUMENT_SCHEMAS[kind]), kind)
                values, extras = completion_values(extracted)
                origin = "upstage"
                raw.update(
                    classify=classification, parse=parsed, extract=extracted, cache_replay=cached
                )
            result = normalize_document(
                kind, values, extras, parsed, number, is_data=origin != "upstage"
            )
            raw.update(
                normalized=result.values,
                kcd_names=result.kcd_names,
                parse_evidence=result.evidence,
                provenance=origin,
            )
            rows.append(
                {
                    "stem": doc["stem"],
                    "source": doc["source"],
                    "path": str(path),
                    "doc_type": kind,
                    "origin": origin,
                    "raw": raw,
                    "fields": [f.model_dump(mode="json") for f in result.fields],
                }
            )
        calls = api.requests_made
    return rows, calls


def evaluate_rows(customer, rows, config):
    """시드와 같은 규칙·고객·증권으로 계산한다. 상태/이슈를 기대값으로 덮어쓰지 않는다."""
    from app.models import ExtractedField

    manifest = json.loads(config.DEMO_CUSTOMERS_PATH.read_text())
    fixture = json.loads(config.DEMO_SEED_PATH.read_text())
    raw_claim = next(c for c in manifest["claims"] if c["id"] == customer["primary_claim_id"])
    claim = Claim(**raw_claim, received_at=raw_claim["received_iso"], assignee_id=1)
    policy = Policy(**next(p for p in manifest["policies"] if p["policy_no"] == claim.policy_no))
    # SQLModel table 객체 직접 생성은 날짜를 검증하지 않으므로 명시적으로 변환한다.
    from datetime import date

    policy.contract_date = (
        date.fromisoformat(policy.contract_date) if policy.contract_date else None
    )
    policy.coverage_start = date.fromisoformat(policy.coverage_start)
    policy.coverage_end = date.fromisoformat(policy.coverage_end)
    docs = []
    for i, row in enumerate(rows, 1):
        fields = [ExtractedField(**f) for f in row["fields"]]
        for f in fields:
            f.document_id = i
        from app.services.normalize import element_text

        docs.append(
            ReviewDocument(
                i,
                row["doc_type"],
                row["raw"]["normalized"],
                fields,
                source_text=" ".join(
                    element_text(e) for e in row["raw"].get("parse", {}).get("elements", [])
                ),
                source=row["source"],
            )
        )
    return evaluate_claim(
        claim,
        docs,
        [RequiredDocRule(**r) for r in fixture["required_rules"]],
        [CrossCheckRule(**r) for r in fixture["cross_rules"]],
        ReviewSettings(
            review_on_low_conf=True,
            review_on_not_in_source=True,
            review_on_format=True,
            auto_pass_threshold=0.9,
        ),
        config,
        policy=policy,
    )


def verify(folder, config, *, live=False, cached=False, use_photo=False):
    _, customer = profile(folder, config)
    rows, calls = prepared_rows(customer, config, live=live, cached=cached, use_photo=use_photo)
    result = evaluate_rows(customer, rows, config)
    actual = Counter((i.rule_id, i.kind.value) for i in result.issues)
    expected = Counter((i["rule"], i["kind"]) for i in customer["expected_issues"])
    # 김유정 실측의 세분류 오독/CV-03은 원본 모델 결과이므로 추가 이슈를 감추지 않고 기록한다.
    missing = expected - actual
    extra = actual - expected
    matches = 0
    total = 0
    mismatches = []
    for row in rows:
        truth = json.loads((folder / "answers" / (row["stem"] + ".json")).read_text())
        wanted = {
            k: v
            for k, v in flatten(truth).items()
            if not k.startswith("_") and k not in ("doc_type", "source")
        }
        found = flatten(row["raw"]["normalized"])
        for key, value in wanted.items():
            total += 1
            if found.get(key) == normal_scalar(key, value):
                matches += 1
            else:
                mismatches.append(
                    {
                        "document": row["stem"],
                        "field": key,
                        "expected": value,
                        "actual": found.get(key),
                    }
                )
    optional = Counter((i["rule"], i["kind"]) for i in customer.get("optional_model_issues", []))
    unexpected = extra - optional
    passed = not missing and not unexpected
    report = {
        "customer": customer["name"],
        "sample_id": customer["sample_id"],
        "claim_id": customer["primary_claim_id"],
        "mode": "live" if live else "cached" if cached else "mock",
        "variant": "photo" if use_photo else "png",
        "photo_count": sum(Path(r["path"]).parent.name == "photo" for r in rows),
        "status": result.status.value,
        "expected": [{"rule": r, "kind": k, "count": n} for (r, k), n in expected.items()],
        "actual": [{"rule": r, "kind": k, "count": n} for (r, k), n in actual.items()],
        "passed": passed,
        "optional_model_issues": sum((extra & optional).values()),
        "missing_issues": [{"rule": r, "kind": k, "count": n} for (r, k), n in missing.items()],
        "unexpected_issues": [
            {"rule": r, "kind": k, "count": n} for (r, k), n in unexpected.items()
        ],
        "calls": calls,
        "field_matches": matches,
        "field_total": total,
        "field_mismatches": mismatches,
    }
    output = PROJECT_ROOT / "artifacts/t06" / customer["sample_id"] / report["variant"]
    output.mkdir(parents=True, exist_ok=True)
    (output / ("live.json" if live else "cached.json" if cached else "mock.json")).write_text(
        json.dumps(report, ensure_ascii=False, indent=2)
    )
    if live or cached:
        target = config.DEMO_RESULTS_PATH / customer["sample_id"] / report["variant"]
        target.mkdir(parents=True, exist_ok=True)
        (target / "rows.json").write_text(json.dumps(rows, ensure_ascii=False))
    print("| 고객 | 모드 | 상태 | 기대/실제 이슈 | 결과 |")
    print("|---|---|---|---|---|")
    print(
        f"| {customer['name']} | {report['mode']} | {report['status']} | {sum(expected.values())}/{sum(actual.values())} | {'PASS' if passed else 'FAIL'} |",
        flush=True,
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", required=True, type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--cached", action="store_true")
    parser.add_argument("--use-photo", action="store_true")
    args = parser.parse_args()
    if args.live and args.cached:
        parser.error("--live와 --cached는 함께 쓸 수 없습니다")
    folder = args.folder
    if not folder.exists():
        folder = PROJECT_ROOT / folder
    config = get_settings()
    if not verify(folder, config, live=args.live, cached=args.cached, use_photo=args.use_photo)[
        "passed"
    ]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
