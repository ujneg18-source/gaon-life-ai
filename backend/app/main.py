"""FastAPI 진입점. 앱 생성 시 설정을 주입해 외부 API 없이 기반을 검증한다."""

from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, text
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from app.config import Settings, get_settings
from app.db import build_engine, create_tables
from app.routers import auth, chat, claims, review, supplements
from app.routers import settings as settings_router
from app.services.pipeline import recover_interrupted


def create_app(settings: Settings | None = None) -> FastAPI:
    """앱별 엔진을 관리한다. import만으로 DB 파일이나 네트워크 호출을 만들지 않는다."""
    config = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = build_engine(config.DB_URL)
        create_tables(engine)
        app.state.engine = engine
        recover_interrupted(engine)
        yield
        if hasattr(app.state, "chat_kb"):
            app.state.chat_kb.client.close()
        engine.dispose()

    app = FastAPI(title=config.APP_NAME, lifespan=lifespan)
    app.state.settings = config
    app.add_middleware(
        SessionMiddleware,
        secret_key=config.SESSION_SECRET.get_secret_value(),
        session_cookie=config.SESSION_COOKIE_NAME,
        max_age=config.SESSION_MAX_AGE,
        same_site="lax",
        https_only=config.SESSION_HTTPS_ONLY,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def check_origin(request: Request, call_next):
        """쿠키 인증의 변경 요청은 허용한 origin만 받는다. CLI는 Origin 없이 검증 가능하다."""
        origin = request.headers.get("origin")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and origin:
            source = urlsplit(origin)
            same_origin = (
                source.scheme == request.url.scheme and source.netloc == request.url.netloc
            )
            if not same_origin and origin not in config.CORS_ORIGINS:
                return JSONResponse({"detail": "허용되지 않은 요청 출처입니다."}, status_code=403)
        return await call_next(request)

    app.include_router(chat.router, prefix=config.API_PREFIX)
    app.include_router(supplements.router, prefix=config.API_PREFIX)
    app.include_router(review.router, prefix=config.API_PREFIX)
    app.include_router(auth.router, prefix=config.API_PREFIX)
    app.include_router(claims.router, prefix=config.API_PREFIX)
    app.include_router(settings_router.router, prefix=config.API_PREFIX)

    @app.get("/health")
    def health():
        """프로세스 생존뿐 아니라 DB 연결도 확인해 잘못된 시작 성공을 방지한다."""
        with Session(app.state.engine) as session:
            session.exec(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
