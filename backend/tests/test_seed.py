"""시드는 반복 실행과 명시적 초기화에서 중복·부분 데이터가 없어야 한다."""

from sqlmodel import Session, select

from app.config import Settings
from app.db import build_engine
from app.models import Claim, CrossCheckRule, RequiredDocRule, ReviewSettings, User
from scripts.seed import seed_database


def test_seed_idempotent_and_reset(tmp_path):
    settings = Settings(_env_file=None, DB_URL=f"sqlite:///{tmp_path / 'seed.db'}")
    engine = build_engine(settings.DB_URL)
    assert seed_database(engine, settings) == {"users": 2, "claims": 13}
    assert seed_database(engine, settings) == {"users": 0, "claims": 0}
    with Session(engine) as session:
        claim = session.get(Claim, "GA-2610-0482")
        assert claim.customer_name == "김유정"
        claim.step = 2
        session.add(claim)
        session.commit()
    assert seed_database(engine, settings, reset=True) == {"users": 2, "claims": 13}
    with Session(engine) as session:
        assert len(session.exec(select(User)).all()) == 2
        assert len(session.exec(select(Claim)).all()) == 13
        assert session.get(Claim, "GA-2610-0482").step == 0
        assert len(session.exec(select(CrossCheckRule)).all()) == 6
        assert len(session.exec(select(RequiredDocRule)).all()) == 10
        assert session.get(ReviewSettings, 1).review_on_low_conf is True
    engine.dispose()
