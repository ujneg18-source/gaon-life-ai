# Codex 프롬프트 — T-01 ~ T-04 (기반 작업)

아래를 Codex에 그대로 붙여넣는다. (작업 폴더: upstage_demo)

---

너는 이 저장소의 구현 담당이다. 가상 생명보험사 "가온생명"의 보험금 청구 서류 검토 PoC를 만든다.

## 먼저 읽을 것 (순서대로, 끝까지)
1. AGENTS.md — 작업 규칙 · 작업 기록 형식 · 기술 스택
2. docs/02_requirements.md — 요구사항 (FR-xx ID 기준으로 작업)
3. docs/03_data_design.md — 테이블 · 서류 유형 코드 · 규칙
4. docs/04_system_design.md — 폴더 구조(4장) · API 명세(5장) · config 키(7장)
5. docs/05_ui_design.md + design/gaon-ai.html — 화면 명세 (HTML을 브라우저로 열어 확인)
6. docs/07_tickets.md — 이번 작업은 T-01 → T-02 → T-03 → T-04

## 이번 작업 범위
T-01 ~ T-04만 순서대로 한다. 티켓 하나 끝날 때마다:
- 완료 조건(docs/07_tickets.md)을 실제로 실행해 확인
- docs/WORKLOG.md 맨 위에 기록 추가 (AGENTS.md 형식)
- git 커밋 `T-0N: 제목`
(저장소가 아직 git이 아니면 먼저 `git init`. .gitignore에 .env, .venv/, node_modules/가 있는지 확인)

## 기술 조건
- 백엔드: Python 3.13, FastAPI, Pydantic v2, pydantic-settings, SQLModel(SQLite), pytest
  - Python 3.13 고정. uv 사용 (`uv python install 3.13`, `uv venv --python 3.13 backend/.venv`), 의존성은 backend/pyproject.toml
  - 모든 설정은 backend/app/config.py의 Settings 한 곳 (docs/04 7장 키 전부, 하드코딩 금지)
  - .env는 읽기만. 새 키가 생기면 .env.example에 이름만 추가
- 프론트: Next.js(App Router) + TypeScript + Tailwind CSS, frontend/ 폴더
  - 색 · 글꼴 · 간격은 design/gaon-ai.html의 :root 토큰을 Tailwind 테마로 옮긴다 (연보라 브랜드, 하트 안 십자가 로고)
  - 상태 표시는 색 + 범용 선 아이콘(lucide-react) + 글자. 알약 배경 금지
- 데모 로그인: POST /api/auth/demo-login {role: reviewer|admin} → httpOnly 세션 쿠키. 비밀번호 없음
  - 데모 계정: reviewer@gaon.demo(한지원), admin@gaon.demo(오세린)
  - 역할 의존성으로 관리자 전용 API는 담당자에게 403

## 하지 말 것
- Upstage API 호출 코드 (T-08 이후). 이번 티켓에서는 필요 없음
- 문서(docs/)의 설계 내용 수정. 설계와 다르게 해야 하면 docs/decisions.md "열린 질문"에 남기고 진행
- 실제 개인정보 · 실존 기관 정보 사용 (모든 데이터는 가상)
- API 키 · .env 커밋

## 끝나면
- AGENTS.md의 "명령어" 칸에 실행 명령 채우기 (백엔드 실행, 테스트, 시드, 프론트 실행)
- 마지막에 요약: 티켓별 완료 여부, 실행 방법, 남은 질문
