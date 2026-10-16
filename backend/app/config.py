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
    UPSTAGE_BASE_URL: str = "https://api.upstage.ai/v1"
    UPSTAGE_AGENT_ID: str = ""
    SOLAR_CHAT_MODEL: str = "solar-pro4"
    SOLAR_EMBED_QUERY_MODEL: str = "solar-embedding-2-query"
    SOLAR_EMBED_PASSAGE_MODEL: str = "solar-embedding-2-passage"
    DB_URL: str = f"sqlite:///{PROJECT_ROOT / 'data/gaon.db'}"
    QDRANT_URL: str = ""
    QDRANT_API_KEY: SecretStr = SecretStr("")
    KB_PATH: Path = PROJECT_ROOT / "data/kb"
    KB_COLLECTIONS: tuple[str, ...] = ("policy", "manual")
    KB_CHUNK_MAX_CHARS: int = 1800
    KB_TOP_K: int = 3
    KB_CANDIDATES: int = 12
    KB_KEYWORD_LIMIT: int = 512
    KB_MIN_SCORE: float = 0.20
    KB_TERM_BOOST: float = 0.08
    KB_IDENTIFIER_BOOST: float = 0.25
    EMBED_BATCH_SIZE: int = Field(default=100, ge=1, le=100)
    EMBED_DIMENSIONS: int = 1024
    CHAT_MAX_TURNS: int = 12
    CHAT_MAX_TOOL_ROUNDS: int = 4
    CHAT_MAX_MESSAGE: int = 2000
    QDRANT_PATH: Path = PROJECT_ROOT / "data/qdrant"
    DEMO_SAMPLE_MOCKS: bool = True
    SHOW_DEVELOPMENT_BADGES: bool = True
    DEMO_SEED_PATH: Path = PROJECT_ROOT / "data/seed/demo.json"
    DATA_PATH: Path = PROJECT_ROOT / "data"
    MOCK_SILSON24_PATH: Path = PROJECT_ROOT / "data/mock_silson24"
    UPLOAD_PATH: Path = PROJECT_ROOT / "data/uploads"
    SAMPLE_PATH: Path = PROJECT_ROOT / "data/samples/kim_yujeong"
    VALIDATION_OUTPUT_PATH: Path = PROJECT_ROOT / "data/evaluations"
    UPLOAD_MAX_BYTES: int = Field(default=20 * 1024 * 1024, gt=0)
    UPLOAD_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".pdf")
    KCD_PATHOLOGY_NEGATIVE: tuple[str, ...] = (
        "benign",
        "양성",
        "no evidence of malignancy",
        "no evidence of adenocarcinoma",
    )
    CACHE_PATH: Path = PROJECT_ROOT / "data/cache"
    UPSTAGE_CLASSIFY_MODEL: str = "document-classify"
    UPSTAGE_PARSE_MODEL: str = "document-parse"
    UPSTAGE_EXTRACT_MODEL: str = "information-extract"
    UPSTAGE_CLASSIFY_PATH: str = "/document-classification/chat/completions"
    UPSTAGE_PARSE_PATH: str = "/document-digitization"
    UPSTAGE_EXTRACT_PATH: str = "/information-extraction/chat/completions"
    UPSTAGE_TIMEOUT_SEC: float = Field(default=120, gt=0)
    UPSTAGE_CONNECT_TIMEOUT_SEC: float = Field(default=10, gt=0)
    UPSTAGE_MAX_RETRIES: int = Field(default=1, ge=0, le=3)
    UPSTAGE_RETRY_DELAY_SEC: float = Field(default=1, ge=0)
    # 응답을 못 받은 요청도 페이지를 예약해 전체 호출량이 상한을 넘지 않게 한다.
    UPSTAGE_PAGE_LIMIT: int = Field(default=30, gt=0, le=30)
    UPSTAGE_OCR_MODE: str = "force"
    UPSTAGE_EXTRACT_OPTIONS: dict = {
        "confidence": True,
        "location": True,
        "location_granularity": "word",
    }
    UPSTAGE_DOC_CLASSES: dict[str, str] = {
        "diagnosis": "진단서. 병명·질병분류기호·진단일·의사 서명",
        "pathology": "병리조직검사 결과지. 검체·병리 진단·보고일",
        "admission": "입퇴원확인서. 입원일·퇴원일·입원 일수",
        "surgery_cert": "수술확인서. 수술명·수술일·수술 코드",
        "medical_receipt": "진료비 계산서 영수증. 급여·비급여·본인부담금",
        "medical_detail": "진료비 세부내역서. 항목별 코드·분류·금액 표",
        "prescription": "처방전. 처방 의약품명·투약 일수·용법",
        "pharmacy_receipt": "약국 발행 약제비 영수증. 약품·조제료·금액",
        "outpatient": "통원확인서. 통원 진료일",
        "imaging_report": "영상 판독지. MRI·CT 소견",
        "disability": "후유장해 진단서. 장해 부위·지급률",
        "death_cert": "사망진단서 또는 시체검안서",
        "claim_form": "보험금 청구서. 청구 유형·사고일",
        "id_copy": "신분증 사본",
        "bankbook": "통장 사본",
        "family_cert": "가족관계증명서",
        "basic_cert": "기본증명서",
        "poa": "위임장",
        "seal_cert": "인감증명서",
        "consent": "개인정보 동의서",
        "accident_report": "사고 사실확인원",
        "accident_statement": "사고 경위서",
        "medical_record": "진료기록 사본",
        "other": "다른 유형에 속하지 않는 문서",
    }
    KCD_PATHOLOGY_HINTS: dict[str, dict[str, list[str]]] = {
        "C18.7": {"result": ["adenocarcinoma", "선암", "악성"], "specimen": ["sigmoid", "구불결장"]}
    }
    CLAIM_TYPE_LABELS: dict[str, str] = {
        "cancer_diagnosis": "암 진단금",
        "hospitalization": "입원일당",
        "medical_expense": "실손",
        "surgery": "수술비",
        "outpatient": "통원일당",
        "disability": "후유장해",
        "death": "사망보험금",
    }
    FIELD_LABELS: dict[str, str] = {
        "patient_name": "환자 성명",
        "issuer": "발행 기관",
        "issued_date": "발행일",
        "diagnosis_code": "질병분류기호",
        "diagnosis_name": "진단명",
        "diagnosis_date": "진단일",
        "onset_date": "발병일",
        "pathology_result": "병리 진단명",
        "specimen": "검체",
        "report_date": "병리 보고일",
        "admit_date": "입원일",
        "discharge_date": "퇴원일",
        "stay_days": "입원 일수",
        "inpatient_days": "입원 일수",
        "period_start": "진료 시작일",
        "period_end": "진료 종료일",
        "items": "진료 항목",
        "covered": "급여 구분",
        "amount": "금액",
        "total": "합계",
        "patient_total": "환자 부담 합계",
        "covered_copay": "급여 본인부담",
        "covered_nhis": "공단 부담",
        "non_covered": "비급여",
        "drug_name": "품명",
        "name": "항목명",
        "category": "분류",
        "code": "코드",
        "date": "진료일",
        "days": "일수",
        "per_day": "일일 횟수",
    }
    KCD_DEMO_CODES: dict[str, str] = {"C18.7": "구불결장의 악성 신생물"}
    AUTO_PASS_THRESHOLD: float = Field(default=0.90, ge=0, le=1)
    USE_CACHED_RESULTS: bool = False
    POLL_INTERVAL_SEC: float = Field(default=2, gt=0)
    POLL_TIMEOUT_SEC: float = Field(default=120, gt=0)
    MAX_FILES_PER_CLAIM: int = Field(default=10, gt=0)
    REVIEW_ON_FORMAT: bool = True
    SOLAR_CHAT_PATH: str = "/chat/completions"
    SUPPLEMENT_MAX_CHARS: int = 2000
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
