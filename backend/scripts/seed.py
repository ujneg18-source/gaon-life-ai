"""데모 계정·청구·규칙 시드. 기본 실행은 비어 있는 DB만 채우고 --demo만 초기화한다.

실행: cd backend && .venv/bin/python -m scripts.seed --demo
기본 실행은 고객·계약·규칙만 채운다. --demo는 가상 서류와 캐시/모의 엔진 결과도 적재한다.
외부 Upstage 호출이나 실제 수신·의료 판단은 하지 않는다.
"""

import argparse
import json
from datetime import date, datetime

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, delete, select

from app.config import Settings, get_settings
from app.db import build_engine, create_tables
from app.models import (
    Claim,
    CrossCheckRule,
    Customer,
    KcdCode,
    Policy,
    RequiredDocRule,
    ReviewSettings,
    Role,
    User,
)


def seed_database(engine: Engine, settings: Settings, *, reset: bool = False) -> dict[str, int]:
    """시드를 한 트랜잭션으로 적재한다. 초기화 실패 시 기존 데이터를 롤백한다."""
    fixture = json.loads(settings.DEMO_SEED_PATH.read_text())
    if fixture.get("is_mock") is not True:
        raise ValueError("가상 데이터 표시가 없는 시드는 사용할 수 없습니다.")
    profiles = json.loads(settings.DEMO_CUSTOMERS_PATH.read_text())
    fixture = {**fixture, **profiles}
    create_tables(engine)
    with Session(engine) as session:
        if reset:
            # FK의 자식부터 삭제한다. DB 파일·원본 문서·사용자의 .env는 삭제하지 않는다.
            for table in reversed(SQLModel.metadata.sorted_tables):
                session.exec(delete(table))
        # 기존 데모 DB도 새 참조 표를 받을 수 있게 초기화 여부와 별개로 보충한다.
        for code, name in settings.KCD_DEMO_CODES.items():
            if session.get(KcdCode, code) is None:
                session.add(KcdCode(code=code, name=name))
        users = []
        for email, name, role in [
            (settings.DEMO_REVIEWER_EMAIL, settings.DEMO_REVIEWER_NAME, Role.REVIEWER),
            (settings.DEMO_ADMIN_EMAIL, settings.DEMO_ADMIN_NAME, Role.ADMIN),
        ]:
            user = session.exec(select(User).where(User.email == email)).first()
            if user is None:
                user = User(email=email, name=name, role=role)
                session.add(user)
                session.flush()
                users.append(user)
        reviewer = session.exec(
            select(User).where(User.email == settings.DEMO_REVIEWER_EMAIL)
        ).one()
        for item in fixture["customers"]:
            if session.get(Customer, item["id"]) is None:
                session.add(
                    Customer(**{**item, "birth_date": date.fromisoformat(item["birth_date"])})
                )
        session.flush()
        for item in fixture["policies"]:
            policy = session.get(Policy, item["policy_no"])
            values = {
                **item,
                "contract_date": date.fromisoformat(item["contract_date"])
                if item.get("contract_date")
                else None,
                "coverage_start": date.fromisoformat(item["coverage_start"]),
                "coverage_end": date.fromisoformat(item["coverage_end"]),
            }
            if policy is None:
                session.add(Policy(**values))
            elif policy.product_name == "가상 기존 계약":
                for key, value in values.items():
                    setattr(policy, key, value)
                session.add(policy)
        session.flush()
        added = 0
        for item in fixture["claims"]:
            item = dict(item)
            for key in ("reported_start", "reported_end"):
                if item.get(key):
                    item[key] = date.fromisoformat(item[key])
            received_at = datetime.fromisoformat(item.pop("received_iso"))
            claim = session.get(Claim, item["id"])
            if claim is None:
                session.add(Claim(**item, received_at=received_at, assignee_id=reviewer.id))
                added += 1
            elif claim.customer_id is None or claim.customer_id.startswith("legacy-"):
                # 기존 청구의 문서·이슈·진행 단계·고객명은 보존하고 참조만 연결한다.
                claim.customer_id = item["customer_id"]
                session.add(claim)
        if session.get(ReviewSettings, 1) is None:
            session.add(
                ReviewSettings(
                    review_on_format=settings.REVIEW_ON_FORMAT,
                    review_on_low_conf=settings.REVIEW_ON_LOW_CONF,
                    review_on_not_in_source=settings.REVIEW_ON_NOT_IN_SOURCE,
                    auto_pass_threshold=settings.AUTO_PASS_THRESHOLD,
                )
            )
        for rule in fixture["required_rules"]:
            if session.get(RequiredDocRule, rule["id"]) is None:
                session.add(RequiredDocRule(**rule))
        for rule in fixture["cross_rules"]:
            if session.get(CrossCheckRule, rule["id"]) is None:
                session.add(CrossCheckRule(**rule))
        session.flush()
        for customer in session.exec(
            select(Customer).where(Customer.id.startswith("legacy-"))
        ).all():
            if (
                not session.exec(select(Claim).where(Claim.customer_id == customer.id)).first()
                and not session.exec(
                    select(Policy).where(Policy.customer_id == customer.id)
                ).first()
            ):
                session.delete(customer)
        session.commit()
    return {"users": len(users), "claims": added}


def main() -> None:
    """--demo는 명시적인 개발 초기화 옵션이며 실제 보험사 데이터에는 사용하지 않는다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="데모 DB 행을 초기화하고 다시 적재")
    parser.add_argument(
        "--use-photo", action="store_true", help="앱 원본 대신 photo/를 사용(없으면 오류)"
    )
    args = parser.parse_args()
    settings = get_settings()
    engine = build_engine(settings.DB_URL)
    try:
        result = seed_database(engine, settings, reset=args.demo)
        if args.demo:
            from scripts.samples.seed_samples import seed_samples

            result["documents"] = seed_samples(engine, settings, use_photo=args.use_photo)
        print(json.dumps(result, ensure_ascii=False))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
