"""10개 대표 사례를 동일 규칙으로 검증한다. 실제 HTTP/키/정답 기반 실측 위장은 금지한다."""

import json
from collections import Counter

import pytest
from sqlmodel import Session, select

from app.config import PROJECT_ROOT, Settings
from app.db import build_engine
from app.models import Claim, Customer, Document
from scripts.samples.seed_samples import seed_samples
from scripts.samples.verify_samples import evaluate_rows, image_path, prepared_rows
from scripts.seed import seed_database


def test_all_ten_expected_issues_without_api():
    config = Settings(_env_file=None)
    manifest = json.loads(config.DEMO_CUSTOMERS_PATH.read_text())
    assert len(manifest["customers"]) == 10
    for customer in manifest["customers"]:
        rows, calls = prepared_rows(customer, config)
        result = evaluate_rows(customer, rows, config)
        assert calls == 0
        assert Counter((i.rule_id, i.kind.value) for i in result.issues) == Counter(
            (i["rule"], i["kind"]) for i in customer["expected_issues"]
        ), customer["sample_id"]
        assert all(row["origin"] in ("mock", "silson24") for row in rows)


def test_demo_seed_is_complete_and_honest_without_live_cache(tmp_path):
    config = Settings(
        _env_file=None,
        DB_URL=f"sqlite:///{tmp_path / 'seed.db'}",
        CACHE_PATH=tmp_path / "cache",
        UPLOAD_PATH=tmp_path / "uploads",
        MOCK_SILSON24_PATH=tmp_path / "electronic",
    )
    engine = build_engine(config.DB_URL)
    seed_database(engine, config, reset=True)
    count = seed_samples(engine, config)
    assert count == 29
    with Session(engine) as s:
        assert len(s.exec(select(Customer)).all()) == 10
        rows = s.exec(select(Claim).order_by(Claim.received_at.desc())).all()
        assert rows[0].customer_name == "김유정"
        assert len({c.status for c in rows}) == 4
        docs = s.exec(select(Document)).all()
        assert not any(d.provenance == "upstage" for d in docs)
        assert {d.provenance for d in docs} == {"mock", "silson24"}
        from app.services.workspace import detail

        hidden = config.model_copy(update={"SHOW_DEVELOPMENT_BADGES": False})
        assert detail(s, rows[0], hidden)["development_origin"] is None
    assert seed_samples(engine, config) == 0
    engine.dispose()


def test_photo_prefers_existing_and_falls_back(tmp_path):
    config = Settings(_env_file=None)
    png = tmp_path / "png"
    photo = tmp_path / "photo"
    png.mkdir()
    photo.mkdir()
    (png / "01_diagnosis.png").write_bytes(b"original")
    assert image_path(tmp_path, "01_diagnosis", config, True) == png / "01_diagnosis.png"
    (photo / "01_diagnosis.jpg").write_bytes(b"photo")
    assert image_path(tmp_path, "01_diagnosis", config, True) == photo / "01_diagnosis.jpg"
    (photo / "01_diagnosis.png").write_bytes(b"duplicate")
    with pytest.raises(ValueError):
        image_path(tmp_path, "01_diagnosis", config, True)


def test_live_customer_allowlist():
    config = Settings(_env_file=None)
    customer = next(
        c
        for c in json.loads(config.DEMO_CUSTOMERS_PATH.read_text())["customers"]
        if c["id"] == "DEMO-C003"
    )
    with pytest.raises(ValueError):
        prepared_rows(customer, config, live=True)


def test_png_and_html_hashes_are_current():
    from scripts.samples.render import fingerprint, render_folder

    for folder in (PROJECT_ROOT / "data/samples").iterdir():
        meta = folder / "render_manifest.json"
        if not meta.exists():
            continue
        for stem, record in json.loads(meta.read_text()).items():
            assert record["html_sha256"] == fingerprint(folder / "html" / (stem + ".html"))
            assert record["png_sha256"] == fingerprint(folder / "png" / (stem + ".png"))
        assert render_folder(folder) == 0


def test_waiting_period_uses_contract_date_and_boundary():
    from copy import deepcopy
    from datetime import date, timedelta

    config = Settings(_env_file=None)
    customer = next(
        c
        for c in json.loads(config.DEMO_CUSTOMERS_PATH.read_text())["customers"]
        if c["id"] == "DEMO-C004"
    )
    rows, _ = prepared_rows(customer, config)
    for elapsed, expected in [(0, True), (89, True), (90, False)]:
        variant = deepcopy(rows)
        variant[0]["raw"]["normalized"]["diagnosis_date"] = (
            date(2026, 9, 1) + timedelta(days=elapsed)
        ).isoformat()
        report = evaluate_rows(customer, variant, config)
        assert any(i.rule_id == "CV-06-WAIT" for i in report.issues) == expected
    variant = deepcopy(rows)
    variant[0]["raw"]["normalized"]["diagnosis_code"] = "C73"
    report = evaluate_rows(customer, variant, config)
    assert not any(i.rule_id == "CV-06-WAIT" for i in report.issues)
    assert any(i.rule_id == "POLICY-C73" for i in report.issues)
