"""기존 SQLite 데모 DB를 보존하는 증분 마이그레이션. 실패하면 DDL·데이터를 함께 롤백한다."""

import hashlib

from sqlalchemy import inspect


def migrate_contracts(engine):
    """SQLite는 기존 열에 FK를 추가할 수 없어 claims만 원자적으로 재구성한다."""
    if engine.dialect.name != "sqlite":
        return
    info = inspect(engine)
    if any(fk["referred_table"] == "policies" for fk in info.get_foreign_keys("claims")):
        return
    connection = engine.raw_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("SELECT * FROM claims")
        columns = [c[0] for c in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.execute("""CREATE TABLE claims_new (
            id VARCHAR NOT NULL PRIMARY KEY, customer_name VARCHAR NOT NULL,
            policy_no VARCHAR NOT NULL REFERENCES policies(policy_no),
            customer_id VARCHAR REFERENCES customers(id), claim_types JSON NOT NULL,
            received_at DATETIME NOT NULL, channel JSON NOT NULL, status VARCHAR NOT NULL,
            assignee_id INTEGER NOT NULL REFERENCES users(id), step INTEGER NOT NULL)""")
        for row in rows:
            customer_id = "legacy-" + hashlib.sha256(row["policy_no"].encode()).hexdigest()[:12]
            cursor.execute(
                "INSERT OR IGNORE INTO customers (id,name,birth_date,contact,is_mock) VALUES (?,?,?,?,1)",
                (customer_id, row["customer_name"], "1900-01-01", "DEMO-미등록"),
            )
            cursor.execute(
                "INSERT OR IGNORE INTO policies (policy_no,customer_id,product_name,riders,coverage_start,coverage_end,is_mock) VALUES (?,?,?,?,?,?,1)",
                (
                    row["policy_no"],
                    customer_id,
                    "가상 기존 계약",
                    row["claim_types"],
                    "2020-01-01",
                    "2099-12-31",
                ),
            )
            cursor.execute(
                "INSERT INTO claims_new VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    row["id"],
                    row["customer_name"],
                    row["policy_no"],
                    customer_id,
                    row["claim_types"],
                    row["received_at"],
                    row["channel"],
                    row["status"],
                    row["assignee_id"],
                    row["step"],
                ),
            )
        cursor.execute("DROP TABLE claims")
        cursor.execute("ALTER TABLE claims_new RENAME TO claims")
        cursor.execute("CREATE INDEX ix_claims_assignee_id ON claims (assignee_id)")
        cursor.execute("CREATE INDEX ix_claims_customer_id ON claims (customer_id)")
        if cursor.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("마이그레이션 외래키 검증 실패")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.close()
