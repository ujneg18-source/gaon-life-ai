"""데모 계정·청구·규칙 시드. 기본 실행은 비어 있는 DB만 채우고 --demo만 초기화한다.

실행: cd backend && .venv/bin/python -m scripts.seed --demo
실손24의 실제 수신·문서 처리·의료 판단은 이 명령에서 수행하지 않는다.
"""

import argparse
import json
from datetime import datetime

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, delete, select

from app.config import Settings, get_settings
from app.db import build_engine, create_tables
from app.models import Claim, CrossCheckRule, RequiredDocRule, ReviewSettings, Role, User


def seed_database(engine: Engine, settings: Settings, *, reset: bool = False) -> dict[str, int]:
    """시드를 한 트랜잭션으로 적재한다. 초기화 실패 시 기존 데이터를 롤백한다."""
    fixture = json.loads(settings.DEMO_SEED_PATH.read_text())
    if fixture.get("is_mock") is not True:
        raise ValueError("가상 데이터 표시가 없는 시드는 사용할 수 없습니다.")
    create_tables(engine)
    with Session(engine) as session:
        if reset:
            # FK의 자식부터 삭제한다. DB 파일·원본 문서·사용자의 .env는 삭제하지 않는다.
            for table in reversed(SQLModel.metadata.sorted_tables):
                session.exec(delete(table))
        elif session.exec(select(User)).first() or session.exec(select(Claim)).first():
            return {"users": 0, "claims": 0}
        reviewer = User(
            email=settings.DEMO_REVIEWER_EMAIL, name=settings.DEMO_REVIEWER_NAME, role=Role.REVIEWER
        )
        admin = User(
            email=settings.DEMO_ADMIN_EMAIL, name=settings.DEMO_ADMIN_NAME, role=Role.ADMIN
        )
        session.add_all([reviewer, admin])
        session.flush()  # DB가 부여한 담당자 ID를 참조해 고정 PK를 가정하지 않는다.
        for item in fixture["claims"]:
            received_at = datetime.fromisoformat(item.pop("received_iso"))
            session.add(Claim(**item, received_at=received_at, assignee_id=reviewer.id))
        session.add(
            ReviewSettings(
                review_on_low_conf=settings.REVIEW_ON_LOW_CONF,
                review_on_not_in_source=settings.REVIEW_ON_NOT_IN_SOURCE,
                auto_pass_threshold=settings.AUTO_PASS_THRESHOLD,
            )
        )
        session.add_all(RequiredDocRule(**rule) for rule in fixture["required_rules"])
        session.add_all(CrossCheckRule(**rule) for rule in fixture["cross_rules"])
        session.commit()
    return {"users": 2, "claims": len(fixture["claims"])}


def main() -> None:
    """--demo는 명시적인 개발 초기화 옵션이며 실제 보험사 데이터에는 사용하지 않는다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="데모 DB 행을 초기화하고 다시 적재")
    args = parser.parse_args()
    settings = get_settings()
    engine = build_engine(settings.DB_URL)
    try:
        print(json.dumps(seed_database(engine, settings, reset=args.demo), ensure_ascii=False))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
