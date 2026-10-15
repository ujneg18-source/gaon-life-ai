"""김유정 앱 서류 4장+실손24 3종의 실제 엔진 검증. 입력 폴더별 결과를 분리한다.

기본: python -m scripts.validate_engine
사진판: python -m scripts.validate_engine --input-dir ../data/samples/kim_yujeong/photo
재평가: python -m scripts.validate_engine --cached (네트워크 금지, 저장 응답만 재사용)
"""

import argparse
import hashlib
import json
import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import Settings, get_settings
from app.main import create_app
from app.models import Document, DocumentSource, ExtractedField, Issue, IssueStatus
from app.services.normalize import additional_values, canonical, flatten, normal_scalar
from app.services.upstage import UpstageClient, atomic_json
from scripts.seed import seed_database


def shape(value, depth=0):
    """메타데이터의 실제 키·타입 구조만 기록한다. 자격 증명이나 원본 전체를 출력하지 않는다."""
    if depth > 5:
        return type(value).__name__
    if isinstance(value, dict):
        return {k: shape(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [shape(value[0], depth + 1)] if value else []
    return type(value).__name__


def equal_normalized(key, expected, actual):
    try:
        expected = normal_scalar(key, expected)
        actual = normal_scalar(key, actual)
    except (ValueError, TypeError):
        return False
    if isinstance(expected, str) and isinstance(actual, str):
        return canonical(expected) == canonical(actual)
    return expected == actual


def run_validation(input_dir: Path, config: Settings, *, client_factory=None) -> dict:
    """검증 DB는 운영·시연 DB와 분리한다. 정답은 처리 후 평가할 때만 읽는다."""
    input_dir = input_dir.resolve()
    stems = ["01_diagnosis", "02_pathology", "03_admission", "07_pharmacy_receipt"]
    files = []
    for stem in stems:
        matches = [
            p for p in input_dir.glob(stem + ".*") if p.suffix.lower() in config.UPLOAD_EXTENSIONS
        ]
        if len(matches) != 1:
            raise ValueError(f"입력 파일이 없거나 중복입니다: {stem}")
        files.append(matches[0])
    fingerprint = hashlib.sha256(b"".join(p.read_bytes() for p in files)).hexdigest()[:12]
    output = config.VALIDATION_OUTPUT_PATH / input_dir.name / fingerprint
    output.mkdir(parents=True, exist_ok=True)
    db = config.CACHE_PATH / "validation" / f"{input_dir.name}-{fingerprint}.db"
    cfg = config.model_copy(update={"DB_URL": f"sqlite:///{db}"})
    with UpstageClient(cfg) as counter:
        before = counter.budget()["reserved_pages"]
    started = time.monotonic()
    with TestClient(create_app(cfg)) as api:
        seed_database(api.app.state.engine, cfg)
        if client_factory:
            api.app.state.upstage_client_factory = client_factory
        assert api.post("/api/auth/demo-login", json={"role": "reviewer"}).status_code == 200
        url = "/api/claims/GA-2610-0482"
        upload = api.post(
            url + "/documents",
            files=[("files", (p.name, p.read_bytes(), "application/octet-stream")) for p in files],
        )
        if upload.status_code != 200:
            raise RuntimeError("upload_failed")
        if api.post(url + "/silson24").status_code != 200:
            raise RuntimeError("silson24_failed")
        accepted = api.post(url + "/process")
        if accepted.status_code != 202:
            raise RuntimeError("process_not_accepted")
        job = api.get(url + "/process/status", params={"job_id": accepted.json()["job_id"]}).json()
        # TestClient는 응답 뒤 BackgroundTasks도 기다리므로 이 시점에 최종 상태를 읽을 수 있다.
        comparisons = []
        structures = {}
        actual_issues = []
        low = 0
        boxes = 0
        with Session(api.app.state.engine) as session:
            docs = session.exec(select(Document)).all()
            for doc in docs:
                if doc.source == DocumentSource.IMAGE:
                    # 파일명 대신 제출한 바이트 해시로 정답 파일을 평가 단계에서만 매칭한다.
                    data = Path(doc.file_path).read_bytes()
                    original = next(p for p in files if p.read_bytes() == data)
                    answer_path = cfg.SAMPLE_PATH / "answers" / f"{original.stem}.json"
                else:
                    answer_path = cfg.SAMPLE_PATH / "answers" / Path(doc.file_path).name
                expected = json.loads(answer_path.read_text())
                truth = {
                    k: v
                    for k, v in expected.items()
                    if not k.startswith("_") and k not in {"doc_type", "source"}
                }
                actual = flatten(doc.raw_result.get("normalized", {}))
                fields = {
                    f.key: f
                    for f in session.exec(
                        select(ExtractedField).where(ExtractedField.document_id == doc.id)
                    ).all()
                }
                low += sum(f.extract_conf == "low" for f in fields.values())
                boxes += sum(f.bbox is not None for f in fields.values())
                comparisons.append(
                    {
                        "document": answer_path.stem,
                        "key": "doc_type",
                        "expected": expected["doc_type"],
                        "actual": doc.doc_type,
                        "match": doc.doc_type == expected["doc_type"],
                        "strict_match": doc.doc_type == expected["doc_type"],
                        "source": doc.source,
                        "confidence": None,
                        "review_reasons": [],
                    }
                )
                for key, value in flatten(truth).items():
                    field = fields.get(key)
                    got = actual.get(key)
                    comparisons.append(
                        {
                            "document": answer_path.stem,
                            "key": key,
                            "expected": value,
                            "actual": got,
                            "match": equal_normalized(key, value, got),
                            "strict_match": value == got,
                            "source": doc.source,
                            "confidence": field.extract_conf if field else None,
                            "review_reasons": field.review_reasons if field else ["missing_field"],
                        }
                    )
                response = doc.raw_result.get("extract")
                if response:
                    message = response["choices"][0]["message"]
                    extras = additional_values(message)
                    structures[expected["doc_type"]] = {
                        "model": response.get("model"),
                        "message_keys": list(message),
                        "tool_names": [
                            c.get("function", {}).get("name") for c in message.get("tool_calls", [])
                        ],
                        "additional_values_shape": shape(extras) if extras else None,
                    }
            for issue in session.exec(select(Issue).where(Issue.status == IssueStatus.OPEN)).all():
                actual_issues.append(
                    {
                        "kind": issue.kind,
                        "rule": issue.rule_id,
                        "title": issue.title,
                        "detail": issue.detail,
                    }
                )
        expected_claim = json.loads((cfg.SAMPLE_PATH / "answers/_claim.json").read_text())
        expected_core = {
            (i["kind"], i["rule"])
            for i in expected_claim["expected_issues"]
            if i["kind"] in {"missing", "mismatch"}
        }
        actual_core = {
            (i["kind"], i["rule"]) for i in actual_issues if i["kind"] in {"missing", "mismatch"}
        }
        with UpstageClient(cfg) as counter:
            after = counter.budget()["reserved_pages"]
        app_comparisons = [
            c for c in comparisons if c["source"] == "image" and c["key"] != "doc_type"
        ]
        data_comparisons = [
            c for c in comparisons if c["source"] == "silson24" and c["key"] != "doc_type"
        ]
        report = {
            "input_dir": str(input_dir),
            "input_fingerprint": fingerprint,
            "state": job["state"],
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "job": job,
            "app_fields": {
                "total": len(app_comparisons),
                "matches": sum(c["match"] for c in app_comparisons),
                "strict_matches": sum(c["strict_match"] for c in app_comparisons),
                "mismatches": sum(not c["match"] for c in app_comparisons),
            },
            "silson24_fields": {
                "total": len(data_comparisons),
                "matches": sum(c["match"] for c in data_comparisons),
            },
            "low_confidence_fields": low,
            "fields_with_coordinates": boxes,
            "issues": actual_issues,
            "expected_core_issues_found": sorted(expected_core & actual_core),
            "expected_core_issues_missing": sorted(expected_core - actual_core),
            "unexpected_core_issues": sorted(actual_core - expected_core),
            "stamp_low_conf_observed": any(
                i["kind"] == "low_conf" and i["rule"] == "FIELD-diagnosis_code"
                for i in actual_issues
            ),
            "coverage_excluded": "T-16 범위로 평가 제외",
            "reserved_pages_this_run": after - before,
            "reserved_pages_total": after,
            "comparison_policy": "날짜·KCD·금액·수술 분류 정규화 후 텍스트 공백·문장부호·대소문자 정리 비교. strict_match도 별도 기록.",
            "response_structures": structures,
            "output_dir": str(output),
        }
        atomic_json(output / "runs" / job["job_id"] / "report.json", report)
        atomic_json(output / "runs" / job["job_id"] / "comparisons.json", comparisons)
        atomic_json(output / "report.json", report)
        atomic_json(output / "comparisons.json", comparisons)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--cached", action="store_true", help="저장 응답만 사용. 외부 호출 금지")
    args = parser.parse_args()
    config = get_settings()
    if args.cached:
        config = config.model_copy(update={"USE_CACHED_RESULTS": True})
    report = run_validation(args.input_dir or config.SAMPLE_PATH / "png", config)
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in {"response_structures", "job"}},
            ensure_ascii=False,
            indent=2,
        )
    )
    if report["state"] != "done":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
