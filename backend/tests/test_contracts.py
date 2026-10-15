"""고객 식별·계약 관계·보장 기간·이전 DB 보존을 확인한다."""

import sqlite3
from collections import Counter

from sqlalchemy import inspect
from sqlmodel import Session, select

from app.config import Settings
from app.db import build_engine, create_tables
from app.models import Claim, Customer, Policy
from app.services.rules import review_from_db
from scripts.seed import seed_database


def test_customers_contracts_and_cv06(client):
    with Session(client.app.state.engine) as s:
        customers = s.exec(select(Customer)).all()
        claims = s.exec(select(Claim)).all()
        assert len(customers) == 10 and len(claims) == 13
        twins = [c for c in customers if c.name == "김서연"]
        assert len(twins) == 2 and twins[0].birth_date != twins[1].birth_date
        assert max(Counter(c.customer_id for c in claims).values()) >= 2
        assert all(
            c.customer_id and s.get(Policy, c.policy_no).customer_id == c.customer_id
            for c in claims
        )
        report = review_from_db(s, s.get(Claim, "GA-2610-0438"), client.app.state.settings)
        assert any(i.rule_id == "CV-06" for i in report.issues)
        report = review_from_db(s, s.get(Claim, "GA-2610-0433"), client.app.state.settings)
        assert any(i.rule_id == "POLICY-RIDER" for i in report.issues)


def test_legacy_sqlite_migration_keeps_claim_and_child(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as db:
        db.executescript("""CREATE TABLE users (id INTEGER PRIMARY KEY,email VARCHAR,name VARCHAR,role VARCHAR);
        INSERT INTO users VALUES (1,'reviewer@gaon.demo','한지원','REVIEWER');
        CREATE TABLE claims (id VARCHAR PRIMARY KEY,customer_name VARCHAR,policy_no VARCHAR,claim_types JSON,received_at DATETIME,channel JSON,status VARCHAR,assignee_id INTEGER,step INTEGER);
        INSERT INTO claims VALUES ('GA-2610-0482','김유정','L-2026-000001','["cancer_diagnosis"]','2026-10-15 00:00:00','["app"]','NEEDS_REVIEW',1,2);
        CREATE TABLE documents (id INTEGER PRIMARY KEY,claim_id VARCHAR REFERENCES claims(id),file_path VARCHAR);
        INSERT INTO documents VALUES (77,'GA-2610-0482','demo-original.png');""")
    cfg = Settings(_env_file=None, DB_URL=f"sqlite:///{path}")
    engine = build_engine(cfg.DB_URL)
    create_tables(engine)
    seed_database(engine, cfg)
    with engine.connect() as db:
        from sqlalchemy import text

        assert db.execute(text('SELECT step FROM claims WHERE id="GA-2610-0482"')).scalar() == 2
        assert db.execute(text("SELECT id FROM documents")).scalar() == 77
        assert not db.execute(text("PRAGMA foreign_key_check")).all()
    assert {"users", "customers", "policies"} <= {
        fk["referred_table"] for fk in inspect(engine).get_foreign_keys("claims")
    }
