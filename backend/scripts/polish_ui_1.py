"""기존 가상 DB의 생일·접수 시각·빈 청구 상태를 무손실 보정한다. 외부 API 호출은 없다."""

import json
from datetime import date, datetime

from sqlmodel import Session, select

from app.config import get_settings
from app.db import build_engine, create_tables
from app.models import Claim, Customer
from app.services.rules import review_from_db


def apply_polish(engine, config):
    fixture = {
        **json.loads(config.DEMO_SEED_PATH.read_text()),
        **json.loads(config.DEMO_CUSTOMERS_PATH.read_text()),
    }
    if not fixture.get("is_mock"):
        raise ValueError("가상 시드만 보정할 수 있습니다.")
    with Session(engine) as session:
        for item in fixture["customers"]:
            customer = session.get(Customer, item["id"])
            if customer and customer.is_mock:
                customer.birth_date = date.fromisoformat(item["birth_date"])
                session.add(customer)
        for item in fixture["claims"]:
            claim = session.get(Claim, item["id"])
            if claim:
                claim.received_at = datetime.fromisoformat(item["received_iso"])
                session.add(claim)
        for claim in session.exec(select(Claim)).all():
            review_from_db(session, claim, config)
        session.commit()


if __name__ == "__main__":
    config = get_settings()
    engine = build_engine(config.DB_URL)
    create_tables(engine)
    apply_polish(engine, config)
    print("가상 시드·빈 청구 상태 보정 완료 (외부 호출 0)")
