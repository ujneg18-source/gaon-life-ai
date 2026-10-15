"""실제 검증 스크립트 자체도 외부 HTTP 모킹으로 먼저 확인한다."""

from pathlib import Path
from types import SimpleNamespace

from engine_fakes import SAMPLE, install_fake

from scripts.validate_engine import run_validation


def test_report_and_cache_replay_by_input_folder(client, tmp_path):
    fake = SimpleNamespace(state=SimpleNamespace())
    calls = install_fake(fake)
    cfg = client.app.state.settings.model_copy(
        update={"VALIDATION_OUTPUT_PATH": tmp_path / "evaluations"}
    )
    report = run_validation(SAMPLE / "png", cfg, client_factory=fake.state.upstage_client_factory)
    assert report["state"] == "done" and len(calls) == 12
    assert report["app_fields"]["total"] == report["app_fields"]["matches"]
    assert report["silson24_fields"]["total"] == report["silson24_fields"]["matches"]
    assert not report["expected_core_issues_missing"] and not report["unexpected_core_issues"]
    assert Path(report["output_dir"]).parent.name == "png"
    replay = run_validation(
        SAMPLE / "png",
        cfg.model_copy(update={"USE_CACHED_RESULTS": True}),
        client_factory=fake.state.upstage_client_factory,
    )
    assert len(calls) == 12 and replay["reserved_pages_this_run"] == 0
    assert replay["state"] == "done"
