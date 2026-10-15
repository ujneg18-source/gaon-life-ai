"""명시적으로 -m live를 선택할 때만 실행되는 실제 API 검증 진입점."""

import pytest

from app.config import get_settings
from scripts.validate_engine import run_validation


@pytest.mark.live
def test_real_kim_yujeong():
    config = get_settings()
    report = run_validation(config.SAMPLE_PATH / "png", config)
    assert report["state"] == "done"
    assert not report["expected_core_issues_missing"]
    assert report["reserved_pages_total"] <= 30
