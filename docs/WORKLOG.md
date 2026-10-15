# 작업 기록

새 기록은 맨 위에 추가한다. 형식은 `AGENTS.md`의 "작업 기록" 참고.

---

## 2026-10-15 · T-09 · 서류별 스키마·정규화·원문 및 좌표 검증
- 관련 요구사항: FR-10, FR-11
- 한 일: Pydantic 모델과 Extract 전용 변환, 날짜·KCD·금액 정규화, 원문 대조·모델 신뢰도·format 검증, word 좌표 우선과 Parse 대체, C18.7 참조 명칭을 구현했다.
- 바뀐 파일: backend/app/schemas/documents.py, to_upstage.py, services/normalize.py, config.py, backend/scripts/seed.py, backend/tests/test_normalize.py, .env.example
- 확인 방법: pytest 전체 19개 통과; ruff 통과. 실제 API 호출 0페이지.
- 남은 문제 · 질문: 없음

## 2026-10-15 · T-08 · 기능별 v1 호출·중복 방지 캐시·페이지 예산
- 관련 요구사항: FR-08, FR-09, NFR-02, NFR-08
- 한 일: httpx 기반 Classify/Parse/Extract와 confidence+word location 옵션을 구현했다. 성공·실패 응답을 파일 해시와 요청 서명으로 캐시하고 프로세스 간 잠금으로 중복 전송을 방지한다. 30페이지 보수적 예약 장부·캐시 전용 모드·제한 재시도·모호한 응답 유실 차단을 추가했다. 기본 pytest는 실제 HTTP를 금지하고 live 마커를 제외한다.
- 바뀐 파일: backend/app/services/upstage.py, config.py, backend/tests/test_upstage_client.py, conftest.py, pyproject.toml, uv.lock, .env.example, docs/decisions.md
- 확인 방법: pytest 전체 15개 통과; ruff 통과. httpx MockTransport로 옵션·캐시·429·읽기 타임아웃·예산·동시 중복·비밀값 반사 제거 확인. 실제 과금 호출 0페이지.
- 남은 문제 · 질문: 타임아웃 후 서버 처리 여부가 불명확한 요청은 자동 재전송하지 않고 수동 확인한다.

## 2026-10-15 · T-07 · 실손24 가상 전자 서류 연결
- 관련 요구사항: FR-07
- 한 일: 04·05·06 정답으로 명시적 가상 JSON을 만들고 청구 연결 API를 구현했다. 중복 연결·다른 담당자 접근을 차단하고 관리자에게는 조회만 허용한다. 수신 이력을 기록하며 실제 외부 호출은 없다.
- 바뀐 파일: data/mock_silson24/*, backend/app/services/silson24.py, routers/claims.py, auth.py, main.py, config.py, backend/tests/conftest.py, test_silson24.py, .env.example
- 확인 방법: backend/.venv/bin/python -m pytest backend/tests -q → 11개 통과; ruff check/format 통과
- 남은 문제 · 질문: 없음

## 2026-10-15 · 환경 정리 2~4 · uv·고정 세션·테스트 기록 규칙
- 관련 요구사항: FR-01~03, NFR-02, NFR-06
- 한 일: brew install uv로 /opt/homebrew/bin/uv 0.13.1을 설치하고 AGENTS의 임시 경로를 고쳤다. Git 제외 .env에 긴 임의 SESSION_SECRET을 저장했으며 값은 출력하지 않았다. .env.example에는 빈 키만 둔다. 평가 문서에 제품 성능 표와 분리된 티켓별 테스트 결과 표를 추가해 T-01~04 기록을 옮겼고, AGENTS에 매 티켓 갱신 규칙을 추가했다.
- 바뀐 파일: AGENTS.md, .env.example, docs/06_eval_plan.md, docs/implementation_objects.md; 로컬 전용 .env는 커밋하지 않음
- 확인 방법: command -v uv 및 uv --version; 프론트 API 로그인 → 백엔드 프로세스 중단·동일 포트 재시작 → 기존 쿠키만으로 /api/me 200·동일 사용자 및 메인 SSR 200 확인. 임시 쿠키 파일 삭제. backend/.venv/bin/python -m pytest backend/tests -q → 9개 통과. git diff --check 통과.
- 남은 문제 · 질문: 고정 키 적용 전 임시 키로 발급한 브라우저 세션은 한 번 다시 로그인해야 한다. 고정 키 적용 후 재시작 유지 검증은 통과. TestClient upstream deprecation warning 1건 유지.

## 2026-10-15 · 환경 정리 1 · 미추적 산출물 커밋
- 관련 요구사항: NFR-02, NFR-06
- 한 일: README·TODO·기획 문서·디자인·가상 서류·기존 생성/검증 스크립트를 추적한다. 가이드의 API 키 자리표시자를 <YOUR_API_KEY>로 바꿔 실제 키 탐지와 혼동하지 않게 했다. data/cache/는 이미 제외되어 있었다.
- 바뀐 파일: README.md, TODO.md, docs/, design/, data/samples/, backend/scripts/samples/, backend/scripts/test_upstage.py, requirements-test.txt
- 확인 방법: git status 및 staged 경로 검사에서 .env·.venv/·data/cache/ 포함 0건, staged 내용의 API 키 형식 문자열 검사.
- 남은 문제 · 질문: 없음.

## 2026-10-15 · T-04 · 요청한 브랜드 마크로 수정
- 관련 요구사항: FR-01, FR-04
- 한 일: 첨부 이미지와 일치하는 design/gaon-ai.html의 원본 로고 SVG를 공통 Brand 컴포넌트에 적용했다. 보라색(#9A89F2)으로 채운 하트 안에 흰색 십자가를 배치해 로그인·메인·워크스페이스에서 같은 마크를 사용한다. 원본 비율을 유지하는 이유를 주석으로 남겼다.
- 바뀐 파일: frontend/components/brand.tsx
- 확인 방법: npm run lint 및 npm run build 통과. 원본 SVG path와 rect 값 대조. 로컬 프론트 서버 재시작 완료.
- 남은 문제 · 질문: 브라우저 새로고침 검증은 URL 프로토콜 정책으로 차단되어 수행하지 못함. 빌드 및 원본 벡터 대조로 검증함.

## 2026-10-15 · T-04 · 프론트 골격과 실제 로그인 연동
- 관련 요구사항: FR-01~04
- 한 일: Next.js 16.4.1/App Router/TypeScript·Tailwind v4 기반을 만들고 HTML의 라이트·다크 토큰을 이식했다. 동일한 글꼴을 로컬 패키지로 제공한다. 로그인·메인 입구 2개·역할별 워크스페이스 메뉴 6개·검색 틀·우하단 어시스턴트/안내 버튼을 구현했다. 후속 업무 화면은 준비 중으로 표시한다. 서버 인증 확인과 관리자 경로 검사를 적용했다. 실제 브라우저에서 발견한 서명 쿠키 재인코딩 문제를 원본 헤더 전달로 수정했다. AGENTS 실행 명령과 객체 안내 문서를 작성했다.
- 바뀐 파일: frontend/*, AGENTS.md, docs/implementation_objects.md, artifacts/t04/*
- 확인 방법: npm run lint / npm run typecheck / npm run format:check / npm run build 통과. backend pytest 9개·ruff 통과. 프로덕션 서버를 실제 브라우저로 열어 비로그인 리다이렉트, 담당자·관리자 로그인, 로그아웃, 역할 전환, 새로고침 유지, 관리자 메뉴와 직접 경로 제한, 검색 준비 안내·도움말·두 입구 이동을 확인했다. 화면 캡처는 artifacts/t04/에 보관.
- 남은 문제 · 질문: Upstage 호출·실제 서류 검토·검색·챗봇은 후속 티켓 범위. npm audit --omit=dev는 0건; 개발 도구 eslint-config-next 하위 braces 관련 high 5건은 호환 수정 버전이 없어 남음(강제 다운그레이드는 적용하지 않음). Context7은 설치 확인했지만 이 대화에 호출 도구가 노출되지 않아 공식 문서를 참고했다. 기존 TestClient deprecation warning 1건 유지.

## 2026-10-15 · T-03 · 데모 로그인과 서버 권한 검사
- 관련 요구사항: FR-01~03, NFR-02
- 한 일: reviewer/admin 데모 로그인, 내 정보, 로그아웃을 구현했다. 서명된 httpOnly 쿠키에는 사용자 ID만 저장하고 역할은 DB에서 확인한다. 관리자 설정 변경 API와 담당 청구 접근 의존성, 외부 Origin 변경 요청 차단을 추가했다. 객체·보안 판단 이유는 한국어 주석에 기록했다.
- 바뀐 파일: backend/app/auth.py, backend/app/schemas/auth.py, backend/app/routers/auth.py, backend/app/routers/settings.py, backend/app/main.py, backend/tests/test_auth.py
- 확인 방법: backend/.venv/bin/python -m pytest backend/tests -q → 9개 통과; ruff check 통과. 두 역할 로그인·로그아웃, 쿠키 변조, DB 역할 변경, 관리자 API 401/403, 담당자별 청구 접근을 검증.
- 남은 문제 · 질문: 개발 기본 세션 키는 프로세스 재시작 시 바뀐다. 지속 세션을 쓰려면 .env의 SESSION_SECRET을 고정해야 한다. 설정 변경에 따른 재검증은 T-14에서 구현한다. 기존 TestClient deprecation warning 1건 유지.

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
