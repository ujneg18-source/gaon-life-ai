"""DB 수명과 세션 의존성. 앱별 엔진을 주입해 테스트 DB와 데모 DB를 격리한다."""

from collections.abc import Generator
from pathlib import Path

from fastapi import Request
from sqlalchemy import Engine, event
from sqlalchemy.engine import make_url
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


def build_engine(url: str) -> Engine:
    """SQLite 외래키 검사를 켜 잘못된 청구·문서 연결이 조용히 저장되지 않게 한다."""
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite":
        return create_engine(url)
    if parsed.database and parsed.database != ":memory:":
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    options = {"poolclass": StaticPool} if parsed.database in (None, "", ":memory:") else {}
    engine = create_engine(url, connect_args={"check_same_thread": False}, **options)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    return engine


def create_tables(engine: Engine) -> None:
    """모든 모델을 등록한 뒤 초기 테이블을 만든다. 데이터 초기화는 시드 명령만 한다."""
    from app import models  # noqa: F401 — SQLModel 메타데이터 등록 목적의 import

    SQLModel.metadata.create_all(engine)
    from app.migrations import migrate_contracts

    migrate_contracts(engine)
    if engine.dialect.name == "sqlite":
        from sqlalchemy import inspect, text

        columns = {col["name"] for col in inspect(engine).get_columns("claims")}
        with engine.begin() as connection:
            for name, kind in {
                "reported_start": "DATE",
                "reported_end": "DATE",
                "review_note": "VARCHAR NOT NULL DEFAULT ''",
            }.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE claims ADD COLUMN {name} {kind}"))

        if "review_on_format" not in {
            col["name"] for col in inspect(engine).get_columns("settings")
        }:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE settings ADD COLUMN review_on_format BOOLEAN NOT NULL DEFAULT 1"
                    )
                )


def get_session(request: Request) -> Generator[Session]:
    """요청당 세션을 열고 종료해 연결·트랜잭션이 다음 요청에 남지 않게 한다."""
    with Session(request.app.state.engine) as session:
        yield session
