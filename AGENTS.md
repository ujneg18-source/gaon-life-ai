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
- 외부: Upstage Agents API(Studio 워크플로), Document Parse, Information Extract, Solar Chat, Solar Embedding

## 설정 규칙
- 모든 상수 · 경로 · 모델명 · 임계값은 `backend/app/config.py` 한 곳에서 관리한다 (하드코딩 금지).
- 환경변수는 pydantic-settings의 `BaseSettings`로 `.env`에서 읽는다 (load_dotenv 별도 호출 불필요).
- 새 환경변수를 추가하면 `.env.example`에도 키 이름을 추가한다.

## 명령어
프로젝트 루트(`upstage_demo/`) 기준. Python 3.13, Node.js 20.9 이상이 필요하다.
현재 환경의 uv 실행 파일은 `/tmp/gaon-uv/bin/uv`이며, 일반 설치 환경에서는 `uv`를 사용한다.

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
.venv/bin/ruff check app tests scripts/seed.py

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
