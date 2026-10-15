"""실행 설정의 유일한 진입점: 실행 디렉터리에 관계없이 프로젝트 .env를 읽는다."""

from functools import lru_cache
from pathlib import Path
from secrets import token_urlsafe

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """환경별 설정 객체. 비밀값은 repr에서 숨겨 로그에 키가 노출되지 않게 한다."""

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")
    APP_NAME: str = "가온생명 AI"
    API_PREFIX: str = "/api"
    # T-01~04는 외부 호출이 없으므로 키 없이도 로컬 기반을 검증할 수 있어야 한다.
    UPSTAGE_API_KEY: SecretStr = SecretStr("")
    UPSTAGE_BASE_URL: str = "https://api.upstage.ai/v2"
    UPSTAGE_AGENT_ID: str = ""
    SOLAR_CHAT_MODEL: str = "solar-pro4"
    SOLAR_EMBED_QUERY_MODEL: str = "solar-embedding-2-query"
    SOLAR_EMBED_PASSAGE_MODEL: str = "solar-embedding-2-passage"
    DB_URL: str = f"sqlite:///{PROJECT_ROOT / 'data/gaon.db'}"
    QDRANT_PATH: Path = PROJECT_ROOT / "data/qdrant"
    DATA_PATH: Path = PROJECT_ROOT / "data"
    AUTO_PASS_THRESHOLD: float = Field(default=0.90, ge=0, le=1)
    USE_CACHED_RESULTS: bool = False
    POLL_INTERVAL_SEC: float = Field(default=2, gt=0)
    POLL_TIMEOUT_SEC: float = Field(default=120, gt=0)
    MAX_FILES_PER_CLAIM: int = Field(default=10, gt=0)
    REVIEW_ON_LOW_CONF: bool = True
    REVIEW_ON_NOT_IN_SOURCE: bool = True
    SESSION_COOKIE_NAME: str = "gaon_session"
    SESSION_MAX_AGE: int = Field(default=28800, gt=0)
    SESSION_HTTPS_ONLY: bool = False
    # 개발 기본값도 무작위로 생성한다. 고정값은 .env에서 지정하며 재시작 시 세션 유지에 쓴다.
    SESSION_SECRET: SecretStr = Field(default_factory=lambda: SecretStr(token_urlsafe(48)))
    SESSION_USER_KEY: str = "user_id"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    DEMO_REVIEWER_EMAIL: str = "reviewer@gaon.demo"
    DEMO_REVIEWER_NAME: str = "한지원"
    DEMO_ADMIN_EMAIL: str = "admin@gaon.demo"
    DEMO_ADMIN_NAME: str = "오세린"


@lru_cache
def get_settings() -> Settings:
    """프로세스 단위 설정을 재사용한다. 테스트에서는 명시적인 Settings를 주입한다."""
    return Settings()
