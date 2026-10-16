# AGENTS.md — Codex 작업 규칙

## 프로젝트
가상 생명보험사 "가온생명"의 보험금 청구 서류 검수 PoC.
Upstage Document AI 결과를 입력으로 받아, 청구 한 건 단위로
분류 → 항목 정규화 → 필수서류 누락 체크 → 서류 간 교차검증 → 신뢰도 기반 검수 라우팅 → 검수 화면을 제공한다.

## 먼저 읽을 것
1. `docs/01_scope.md` — 범위
2. `docs/02_requirements.md` — 요구사항 (ID 기준으로 작업)
3. `docs/03_data_design.md` — 스키마 · 룰
4. `docs/04_system_design.md` — 구조 · API
5. `docs/07_tickets.md` — 지금 할 티켓
6. `docs/upstage_api_guide.md` — Upstage API 사용법 (호출 코드 · 스키마 규칙 · 실측 결과). Upstage 관련 코드는 반드시 이 문서 기준

## 작업 기록 (필수)
작업을 끝낼 때마다 `docs/WORKLOG.md` **맨 위**에 아래 형식으로 한 블록을 추가한다. 기록 없이 작업을 끝내지 않는다.

```
## YYYY-MM-DD · T-번호 · 한 줄 제목
- 관련 요구사항: FR-xx
- 한 일: (무엇을 바꿨는지 2~4줄)
- 바뀐 파일: path/a.py, path/b.tsx
- 확인 방법: (실행 명령, 열어볼 화면, 테스트)
- 남은 문제 · 질문: (없으면 "없음")
```

- 설계와 다르게 구현했다면 이유를 "한 일"에 적고, `docs/decisions.md`의 열린 질문에도 남긴다.
- 티켓 완료 시 `docs/06_eval_plan.md`의 **"티켓별 테스트 결과"** 표에 `티켓 | 테스트 항목 | 결과 | 실행 명령 | 날짜` 한 줄을 추가한다. 같은 티켓의 추가 수정은 기존 행에 검증 결과를 갱신한다. 실제 실행한 결과만 적고, 미실행·실패·제약은 명확히 쓴다.
- 이 표는 정확도·탐지율 등의 제품 성능 결과 표와 구분한다. WORKLOG 기록과 테스트 결과 표 갱신을 모두 마친 뒤 커밋한다.
- 커밋 메시지는 `T-번호: 한 줄 제목` 형식으로 쓴다.

## 규칙
- 티켓 하나만 처리하고, 커밋 메시지에 티켓 ID와 요구사항 ID를 적는다.
- API 키는 `.env`에서만 읽는다. 키 · `.env`를 절대 커밋하지 않는다.
- 데이터는 전부 가상이다. 실제 개인정보(주민번호, 계좌번호, 실명 등) 형식의 값을 만들 때는 명백한 가짜 패턴을 쓴다.
- 문서에 없는 기능을 임의로 추가하지 않는다. 애매하면 `docs/decisions.md`에 질문으로 남긴다.

## 기술 스택 (2026-10-15 결정)
- 백엔드: Python 3.13 (uv로 설치 · 가상환경 backend/.venv), FastAPI, Pydantic v2, pydantic-settings, LangGraph, SQLite(SQLModel)
- 벡터 DB: Qdrant (개발 · 데모는 로컬 모드, 서버 불필요)
- 프론트: Next.js (design/gaon-ai.html이 화면 명세)
- 외부: Upstage 기능별 v1 API 직접 호출(Classify → Parse → Information Extract), Solar Chat, Solar Embedding. Studio 에이전트 v2는 서류 처리 엔진에서 사용하지 않는다.

## 설정 규칙
- 모든 상수 · 경로 · 모델명 · 임계값은 `backend/app/config.py` 한 곳에서 관리한다 (하드코딩 금지).
- 환경변수는 pydantic-settings의 `BaseSettings`로 `.env`에서 읽는다 (load_dotenv 별도 호출 불필요).
- 새 환경변수를 추가하면 `.env.example`에도 키 이름을 추가한다.

## 명령어
프로젝트 루트(`upstage_demo/`) 기준. Python 3.13, Node.js 20.9 이상이 필요하다.
uv는 Homebrew로 정식 설치되어 있으며 `uv` 명령을 사용한다 (`/opt/homebrew/bin/uv`). 설치가 필요하면 `brew install uv`를 실행한다.

```bash
# 백엔드 설치 (잠금 파일 기준)
cd backend
uv sync --locked

# 가상 시드: 기본 실행은 기존 행 보존, --demo는 DB 행 초기화
.venv/bin/python -m scripts.seed
.venv/bin/python -m scripts.seed --demo

# 백엔드 실행 (별도 터미널)
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 백엔드 검증
.venv/bin/python -m pytest
.venv/bin/ruff check app tests scripts/seed.py scripts/validate_engine.py

# 프론트 설치·개발 (프로젝트 루트의 별도 터미널)
cd frontend
npm ci
npm run dev

# 프론트 검증·배포 빌드
npm run lint
npm run typecheck
npm run format:check
npm run build
npm run start
```

접속: `http://127.0.0.1:3000` / 백엔드 상태: `http://127.0.0.1:8000/health`.
기본 설정으로 API 키 없이 기반 화면을 실행할 수 있다. 새 프론트 환경변수는 `frontend/.env.example`을 참고한다.
객체·세션·프론트 구조의 설명은 `docs/implementation_objects.md`에 있다.


## 서류 엔진 검증 명령 (T-07~T-11)

`backend/`에서 실행한다. 일반 pytest는 실제 HTTP를 막고 live 테스트를 제외한다.

```bash
# 이미 저장한 실측 응답으로만 재평가 (추가 호출·과금 없음)
.venv/bin/python -m scripts.validate_engine --cached

# 다른 사진판을 명시적으로 실제 검증할 때만 실행 (과금 가능)
.venv/bin/python -m scripts.validate_engine --input-dir ../data/samples/kim_yujeong/photo

# 실제 API 테스트는 별도 선택할 때만 실행 (과금 가능, 성공 캐시는 우선 재사용)
.venv/bin/python -m pytest -m live tests/test_live_engine.py -q
```

이번 묶음의 API 입력 페이지 예약 합계는 12/30이다. `data/cache/_budget.json`과 `.pending`은 중복 과금 방지 상태이므로 임의로 지우지 않는다. 결과는 `data/evaluations/<입력폴더>/<내용지문>/`에 보관한다.

## 챗봇·지식 인덱스 명령 (T-15~17)
backend/에서 실행한다. 실제 회사 약관 data/kb/reference/는 커밋·인덱싱 금지. HWP Parse 없음.
```bash
uv run python -m app.scripts.build_index
# 원문 변경 후 로컬 Qdrant 서버를 종료한 상태에서 컬렉션을 다시 만들 때만:
uv run python -m app.scripts.build_index --rebuild
# 실제 Solar 호출 검증 (일반 pytest와 분리):
uv run python -m app.scripts.chat_smoke
```
일반 pytest는 LLM/임베딩 mock이며 실제 HTTP를 금지한다. 로컬 Qdrant는 프로세스 하나만 열 수 있다. 실제 챗봇 검증에는 USE_CACHED_RESULTS=false와 설정된 키가 필요하다. 대화 기록은 메모리만 사용하며 실제 smoke 평가 원문은 명시적 산출물 artifacts/t16/에 저장한다.
