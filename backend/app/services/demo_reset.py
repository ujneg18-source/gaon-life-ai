"""시연 DB만 백업 후 재시드한다. 벡터 인덱스와 응답 캐시는 읽기 검사만 한다."""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.engine import make_url

from app.db import build_engine
from app.services.upstage import atomic_json, locked
from scripts.samples.seed_samples import seed_samples
from scripts.seed import seed_database


def state_path(config):
    return config.DATA_PATH / "demo-state.json"


def read_revision(config):
    path = state_path(config)
    return json.loads(path.read_text())["revision"] if path.exists() else "initial"


def backup_database(config):
    url = make_url(config.DB_URL)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        raise ValueError("시연 초기화에는 파일 SQLite DB가 필요합니다.")
    source = Path(url.database).resolve()
    if not source.is_file():
        raise ValueError("백업할 시연 DB가 없습니다.")
    folder = config.DATA_PATH / "backup"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(ZoneInfo(config.DEMO_RESET_TIMEZONE)).strftime("%Y%m%d_%H%M")
    target = folder / f"gaon_{stamp}.db"
    suffix = 0
    while target.exists():
        suffix += 1
        target = folder / f"gaon_{stamp}_{suffix:02}.db"
    # WAL을 포함한 일관된 복사본. 같은 분에 반복 실행해도 이전 백업을 덮어쓰지 않는다.
    with (
        sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as src,
        sqlite3.connect(target) as dst,
    ):
        src.backup(dst)
    return source, target


def reset_demo(config):
    if not config.DEMO_MODE:
        raise ValueError("시연 모드에서만 초기화할 수 있습니다.")
    started = time.monotonic()
    with locked(config.DATA_PATH / "locks/demo-reset.lock"):
        checks = {
            "index": bool(config.QDRANT_URL)
            or (
                config.QDRANT_PATH.is_dir()
                and all(
                    (config.QDRANT_PATH / "collection" / name).is_dir()
                    for name in config.KB_COLLECTIONS
                )
            ),
            "structure": config.KB_STRUCTURE_PATH.is_file(),
            "cache": config.CACHE_PATH.is_dir() and any(config.CACHE_PATH.rglob("*.json")),
        }
        if not all(checks.values()):
            raise ValueError(f"시연 자산이 없습니다 (재생성하지 않음): {checks}")
        source, backup = backup_database(config)
        engine = build_engine(config.DB_URL)
        try:
            result = seed_database(engine, config, reset=True)
            result["documents"] = seed_samples(engine, config)
        except Exception:
            engine.dispose()
            with sqlite3.connect(backup) as src, sqlite3.connect(source) as dst:
                src.backup(dst)
            raise
        finally:
            engine.dispose()
        revision = uuid4().hex
        atomic_json(state_path(config), {"revision": revision})
        elapsed = time.monotonic() - started
        return {
            "backup": str(backup),
            "elapsed_seconds": round(elapsed, 3),
            "within_limit": elapsed < config.DEMO_RESET_LIMIT_SEC,
            "checks": checks,
            "seed": result,
            "revision": revision,
        }
