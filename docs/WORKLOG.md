# 작업 기록

새 기록은 맨 위에 추가한다. 형식은 `AGENTS.md`의 "작업 기록" 참고.

---

## 2026-10-15 · T-02 · 가상 데모 계정·청구·규칙 시드
- 관련 요구사항: FR-07 (기반 시드만, 실제 모의 수신 API는 T-07)
- 한 일: 데모 계정 2개·김유정 포함 청구 6건·필수 서류 규칙 10개·교차검증 정의 6개·설정 기본값을 적재한다. 기본 실행은 기존 데이터를 보존하고 --demo에서만 FK 역순으로 행을 초기화한다. 시연 상태는 고정 픽스처이며 AI 실행 결과가 아니다.
- 바뀐 파일: backend/scripts/__init__.py, backend/scripts/seed.py, backend/app/config.py, backend/tests/test_seed.py, data/seed/demo.json, .env.example
- 확인 방법: cd backend && .venv/bin/python -m scripts.seed --demo → users 2 / claims 6; .venv/bin/python -m pytest → 3개 통과; ruff check 통과. 재실행 중복 방지와 --demo 복구를 격리 DB에서 검증.
- 남은 문제 · 질문: 없음. 서류·실손24 JSON 연결 및 규칙 실행은 후속 티켓.


## 2026-10-15 · T-01 · 백엔드 골격과 설정·DB 기반
- 관련 요구사항: NFR-02, NFR-06
- 한 일: Python 3.13.16/uv 환경과 FastAPI 앱, 프로젝트 루트 .env를 읽는 Settings, SQLModel 12개 테이블을 구현했다. 객체별 한국어 설명과 판단 이유를 주석으로 추가했다. SQLite 외래키 검사를 활성화했다. 외부 API 호출은 추가하지 않았다.
- 바뀐 파일: .gitignore, .env.example, backend/pyproject.toml, backend/uv.lock, backend/.python-version, backend/app/*, backend/tests/test_foundation.py, docs/decisions.md
- 확인 방법: cd backend && .venv/bin/python -m pytest (2개 통과: /health 200, 테이블 12개 생성, 외래키 제약, 환경변수 우선순위·비밀값 표시 방지); .venv/bin/ruff check app tests 통과
- 남은 문제 · 질문: TestClient의 httpx 사용 관련 upstream deprecation warning 1건. 설계가 생략한 규칙 테이블 컬럼과 키 없는 초기 실행 가정은 decisions.md에 기록. uv 실행 파일은 현재 /tmp/gaon-uv/bin/uv에 설치됨.


## 2026-10-15 · 기획 · 기획 산출물 v1.0
- 관련 요구사항: FR-01~35, NFR-01~10
- 한 일: 기획서, 요구사항정의서(역할 · 데모 계정 포함), 데이터 설계(테이블 · 표준 스키마 · 규칙), 시스템 설계 · API 명세, 화면설계서, 시연 시나리오, WBS, 개발 티켓 T-01~19 작성. 아키텍처 그림 · 화면 캡처 생성
- 바뀐 파일: docs/02~07, docs/deliverables/*, design/diagrams/*, design/screens/*
- 확인 방법: docs/deliverables/01_기획서.md부터 읽기, design/diagrams/architecture.png
- 남은 문제 · 질문: Information Extract 좌표 제공 여부, Upstage 무료 범위 · 모델명, 공고 마감일, KCD 적용 차수

## 2026-10-15 · 기획 · 프로젝트 뼈대와 기획 문서 초안
- 관련 요구사항: 전체
- 한 일: upstage_demo 폴더, README · TODO · AGENTS, docs 00~07 초안 작성. 가온생명으로 이름 변경, 서류 Tier 확정, 기술 스택(FastAPI · Next.js · Qdrant 로컬) 결정. HTML 프로토타입(design/gaon-ai.html) 추가
- 바뀐 파일: README.md, TODO.md, AGENTS.md, docs/*, design/gaon-ai.html
- 확인 방법: design/gaon-ai.html을 브라우저로 열기
- 남은 문제 · 질문: Information Extract 좌표 제공 여부, Upstage 무료 사용 범위, 공고 마감일 · 직무
