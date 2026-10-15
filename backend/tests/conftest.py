"""엔진 테스트는 임시 DB·설정으로 격리하고, 기본 테스트에서 실제 HTTP를 금지한다."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from scripts.seed import seed_database


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        _env_file=None,
        DB_URL=f"sqlite:///{tmp_path / 'test.db'}",
        DATA_PATH=tmp_path,
        CACHE_PATH=tmp_path / "cache",
    )
    with TestClient(create_app(settings)) as client:
        seed_database(client.app.state.engine, settings)
        yield client
