"""FastAPI 진입점. 앱 생성 시 설정을 주입해 외부 API 없이 기반을 검증한다."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session, text

from app.config import Settings, get_settings
from app.db import build_engine, create_tables


def create_app(settings: Settings | None = None) -> FastAPI:
    """앱별 엔진을 관리한다. import만으로 DB 파일이나 네트워크 호출을 만들지 않는다."""
    config = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = build_engine(config.DB_URL)
        create_tables(engine)
        app.state.engine = engine
        yield
        engine.dispose()

    app = FastAPI(title=config.APP_NAME, lifespan=lifespan)
    app.state.settings = config

    @app.get("/health")
    def health():
        """프로세스 생존뿐 아니라 DB 연결도 확인해 잘못된 시작 성공을 방지한다."""
        with Session(app.state.engine) as session:
            session.exec(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
