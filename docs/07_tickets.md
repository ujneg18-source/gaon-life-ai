# 07. 개발 티켓 (Codex용)

규칙: 티켓 하나씩 순서대로. 끝나면 `docs/WORKLOG.md` 기록, 커밋 메시지 `T-번호: 제목`.
선행 표시 `←`: 먼저 끝나야 하는 티켓. **[진영]** 표시는 사람이 먼저 해야 하는 일.

| ID | 제목 | 요구사항 | 선행 | 완료 조건 |
|---|---|---|---|---|
| T-01 | 백엔드 골격 | NFR-02, 06 | — | `backend/` 구조(04 설계 4장), `config.py`(BaseSettings, 7장 키 전부), SQLModel 테이블(03 설계), `/health` 200, `.env.example` 갱신 |
| T-02 | 시드 데이터 | FR-07 | T-01 | `scripts/seed.py`: 데모 계정 2개, 청구 6건(김유정 포함), 규칙 · 설정 기본값. `--demo`로 초기화 |
| T-03 | 데모 로그인 · 권한 | FR-01~03 | T-01 | `/api/auth/demo-login`, `/api/me`, 역할 의존성. 담당자가 관리자 API 호출 시 403 테스트 |
| T-04 | 프론트 골격 | FR-01, 04 | T-03 | Next.js + Tailwind, 디자인 토큰(gaon-ai.html의 색 · 글꼴), SCR-01 로그인, SCR-02 메인, 워크스페이스 레이아웃(메뉴 6 · 검색 · 우하단 버튼) |
| T-05 | 목업 서류 템플릿 (**김유정 7장은 완료**: `data/samples/kim_yujeong/`, 생성기 `backend/scripts/samples/gen_kim_yujeong.py`) | — | — | `data/samples/templates/` HTML 서식 6종(진단서, 조직검사 결과지, 입퇴원확인서, 수술확인서, 진료비 영수증 · 세부내역서 법정 서식, 약제비 영수증) |
| T-06 | 목업 서류 생성기 | — | T-05 | 캡처(Playwright) → 왜곡(기울기 · 원근 · 그림자 · 직인 · 흐림) → PNG, 서류별 정답 JSON. 김유정 세트 + 고객 8명 |
| T-07 | 실손24 모의 데이터 | FR-07 | T-02 | `data/mock_silson24/*.json` (영수증 · 세부내역서 · 처방전), `/api/claims/{id}/silson24` |
| — | **[진영] Studio 워크플로 구성** | FR-08, 09 | T-06 | Studio에서 분류 + 추출 흐름 구성(표준 스키마 키), 김유정 서류로 실행 확인, 에이전트 ID 발급, **좌표 제공 여부 확인** |
| T-08 | Upstage 클라이언트 | FR-08, 09 | 위 | `services/upstage.py`: 업로드 → 실행 → 폴링, 타임아웃, 응답 캐시(`USE_CACHED_RESULTS`) |
| T-09 | 정규화 · 검증 | FR-10, 11 | T-08 | 서류별 Pydantic 스키마, 날짜 · KCD · 금액 정규화, `kcd_codes` 명칭 연결, 검증 실패 → `format` 이슈. 단위 테스트 |
| T-10 | 규칙 엔진 | FR-13, 14, 16, 17 | T-09 | `services/rules.py`: 필수서류(4-1), CV-01~05, 신뢰도 라우팅, 청구 상태. 김유정 세트에서 누락 1 · 불일치 2 · 저신뢰 1 검출 테스트 |
| T-11 | 파이프라인 API | FR-06, 12 | T-10 | 업로드 · process · status API, 백그라운드 작업, 이력 기록 |
| T-12 | 검토함 · 상세 화면 | FR-05, 18~20 | T-04, T-11 | SCR-10, SCR-11(단계 4개, 직접 수정) API 연결 |
| T-13 | 문서 분석 · 검토 화면 | FR-21~24 | T-12 | SCR-12: 원본 이미지 + bbox 박스, 확대/축소, 원본 비교, 이슈 확인, 정규화 표 |
| T-14 | 보완 · 이력 · 운영 관리 | FR-25~27 | T-12 | SCR-13~15, 모의 발송, 설정 변경 시 재검사 |
| T-15 | 지식 베이스 구축 | FR-28 | T-01 | `data/kb/` 표준약관 원문 + 가상 특약 · 매뉴얼, `scripts/ingest_kb.py`(조항 단위 분할 → Solar Embedding → Qdrant 로컬), BM25 인덱스 |
| T-16 | 약관 대조 | FR-15 | T-10, T-15 | `services/coverage.py`, `drug_catalog` 샘플, 김유정 약제비 영양제 1건 → `excluded_item` + 근거 조항 |
| T-17 | 챗봇 | FR-28~35 | T-15, T-16 | LangGraph(의도 분류 · 도구 5개 · RAG), `/api/chat` SSE, SCR-20 화면(히스토리 · 질문 막대 · 근거 패널) |
| T-18 | 평가 | NFR-08 | T-10, T-17 | `scripts/eval.py`: 항목 정확도, 탐지율, 오탐률, 검수 대상 비율, 챗봇 근거 적중률 → `docs/06_eval_plan.md` 결과 표 |
| T-19 | 배포 | NFR-10 | T-17 | 프론트 Vercel, 백엔드 단일 서버, 시연용 캐시 모드 확인 |
