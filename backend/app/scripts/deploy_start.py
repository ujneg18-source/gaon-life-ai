"""무료 Render의 새 디스크에 검증한 시연 자산만 복원한다. API 호출/인덱스 재생성 없음."""

import hashlib
import json
import tarfile

from app.config import Settings, get_settings
from app.db import build_engine
from app.services.demo_reset import backup_database
from scripts.samples.seed_samples import seed_samples
from scripts.seed import seed_database


def prepare(config: Settings) -> dict:
    if config.DEPLOY_RUNTIME_DIR is None or not config.DEMO_MODE:
        raise ValueError("시연 배포에는 DEPLOY_RUNTIME_DIR와 DEMO_MODE=true가 필요합니다.")
    root = config.DATA_PATH
    root.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(config.DEPLOY_MANIFEST_PATH.read_text())
    # 전체 목록/해시 검증 후에만 쓰기. extractall은 사용하지 않는다.
    contents = {}
    with tarfile.open(config.DEPLOY_ASSETS_PATH, "r:gz") as archive:
        members = archive.getmembers()
        if len(members) != len(manifest):
            raise ValueError("시연 자산 목록 불일치")
        for member in members:
            target = (root / member.name).resolve()
            if (
                not member.isfile()
                or not target.is_relative_to(root.resolve())
                or member.name not in manifest
                or member.name in contents
            ):
                raise ValueError("허용되지 않은 시연 자산")
            body = archive.extractfile(member).read()
            if hashlib.sha256(body).hexdigest() != manifest[member.name]:
                raise ValueError("시연 자산 해시 불일치")
            contents[member.name] = body
    for name, body in contents.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        # 디스크가 유지된 프로세스 재시작은 기존 캐시/수정 내용을 덮어쓰지 않는다.
        if not target.exists():
            target.write_bytes(body)
    db = root / "gaon.db"
    if db.exists():
        # 테이블 마이그레이션/증분 시드도 DB를 건드리기 전에 백업한다.
        backup_database(config)
    engine = build_engine(config.DB_URL)
    try:
        result = seed_database(engine, config)
        result["documents"] = seed_samples(engine, config)
    finally:
        engine.dispose()
    return {"assets": len(contents), "seed": result}


def main():
    import uvicorn

    config = get_settings()
    print(json.dumps(prepare(config), ensure_ascii=False), flush=True)
    uvicorn.run("app.main:app", host="0.0.0.0", port=config.PORT, workers=1)


if __name__ == "__main__":
    main()
