## 2026-10-16 · T-18 · 통제 평가·채점 보정과 홀드아웃 전 동결
- 관련 요구사항: FR-28~35, NFR-08, T-18c
- 한 일: 사용자 홀드아웃16문항을 먼저1f55549로 커밋했다. 구/신 rubric 원문과 제한적 acceptable_sources의 문항별 근거를 CHANGELOG에 보존했고 엄격 기준은 유지했다. 기존30답변을 같은 모델/요청 seed/설정으로 구·신 rubric 각각3회 재채점, 1→0 네 문항의 두 답변/컨텍스트/판정 사유를 분석했다.
  청구 조회는 DB+실행 규칙 근거로 고정하고 일반 RAG를 제거했다. Q24 후속 행동 누락, Q26 항 중복 제거/단서 소실 및 발급비 서류명 오부스트를 개발 셋에서 보완했다. 옛 kb.py의 별도492조각 컬렉션과 현재1005조각을 복제 인덱스에서2×2 평가했다. 카드 출처 종류/보장종목·호 주소도 표시했다.
- 바뀐 파일: backend/app/agent, schemas/chat.py, services/coverage.py, scripts/eval_chat.py·eval_protocol.py·regrade_t18c.py, config.py, tests, frontend/components/chat-screen.tsx, data/eval, .env.example, artifacts/t18/runs/2026-10-16/t18c
- 확인 방법: pytest94 passed/live1 deselected, Ruff·포맷·프론트 lint/type/format 통과. next build --webpack 성공. 개발30문항 의도100/recall(a,b)93.75/엄격 인용92.11/거절100/요지96.67%, 호 recall/인용100/100(4문항). 필수4+영양제 질문 검증 통과. 모든 새 실행의 모델/요청 seed42/온도0 동일; 공식 API의 seed 적용 보장은 미확인이라 완전 결정성을 주장하지 않는다.
- 남은 문제 · 질문: freeze_before_holdout.json으로 코드/정답 해시를 고정했다. 홀드아웃은 다음 단계에서1회만 실행하며 그 결과로 코드·rubric·허용 근거를 변경하지 않는다. 과거 무seed 점수와 통제 재채점 차이를 알고리즘 효과로 혼동하지 않는다.

## 2026-10-16 · T-18 · 챗봇 품질 개선 2라운드
- 관련 요구사항: FR-30~35, T-15~18
- 한 일: 코드 수정 전에 실패24개를 검색/의도/생성/인용/도구/정답/채점으로 분류했다. 구조 트리·부모 JSON·정의/참조·규범 위계·준용, RRF/BM25/재작성/재정렬, 사용 ID 최대2개 인용을 구현했다.
  지급 결정 선행 가드, 정상 조회 오거절 방지, Pydantic 도구 최대1회 재시도와 비밀값 없는 오류 로그, 진단명 원문 대조를 보완했다. Q20 및 원본에 있는 병리 한국어 병기 정답 오류는 CHANGELOG에 남기고 모든 이전 실행/실패를 보존했다.
- 바뀐 파일: backend/app/agent/{kb,rag,graph,guardrails,tools,solar}.py, app/config.py, schemas/chat.py, services/{coverage,normalize,source_evidence}.py, scripts/{eval_chat,eval_retrieval,legacy_search,chunk_report,eval_extract,chat_smoke}.py, tests, .env.example, data/eval, 김유정 병리 정답/manifest, artifacts/t18, docs/06_eval_plan.md, deliverables/테스트결과보고서.md, implementation_objects.md, decisions.md, AGENTS.md, TODO.md
- 확인 방법: pytest89 passed/live1 deselected·Ruff/포맷 통과. 실제 최종30문항: 의도100%, recall@3 89.58%, 인용75%, 거절100%, 요지83.33%; 금지표현0/호출오류0. 별도 동일 인덱스 ablation 청킹-only60.42/dense62.50/hybrid91.67%. 호 단위 recall/인용75/75 (4문항). 필수4질문 및 준용 인용 실측 통과. 추출 캐시64/65, 정밀도/재현율100/100이나 원본 정답 수정 효과로 구분. 프론트 lint/typecheck/format 통과.
- 남은 문제 · 질문: 최종 미달14문항 원문/채점/사람 검토를 remaining_failures.md에 남겼다. 중간 요지93.33%보다 최종83.33%가 낮아졌으며 최고값을 최종으로 고르지 않았다. 프론트 배포 빌드는 Turbopack CSS 워커 소켓 EPERM으로 미확인. 계약별 보장종목/법률 충돌 쌍 holdout/독립 사람 평가가 필요하다. 일반적인 충돌 자동 판정기는 구현하지 않았다.

# 작업 기록

새 기록은 맨 위에 추가한다. 형식은 `AGENTS.md`의 "작업 기록" 참고.

---

## 2026-10-16 · T-18 · 챗봇30문항 전후 평가와 캐시 추출 검수 평가
- 관련 요구사항: NFR-08, FR-28~35
- 한 일: 평가기·고정 rubric·정답 해시·스냅샷·문항별 체크포인트·검색 trace/오류 기록을 추가했다. 명시 전송 승인 후 동일30문항 before/after_v1/after를 모두 보존하고 검색/의도/생성/정답4범주 실패 원문을 정리했다. 일반 질문 분기·권한 내 배정 집계·전체 품목 대조·거절 문구·인용 검증·검색 보강/중복 제거·짧은 특약 문맥을 보완했다. 실제 API65항목과 전자 mock 포함190항목을 분리했다. Q08/Q18 source 라벨만 수정한 재채점을 별도로 남겼다.
- 바뀐 파일: app/scripts/{eval_chat,eval_extract}.py, agent/{graph,rag,solar,tools}.py, config.py, tests/{test_eval,test_chat,test_rag}.py, .env.example, frontend/components/chat-screen.tsx, data/eval/chat_questions.json, artifacts/t18/, docs/06_eval_plan.md, docs/deliverables/테스트결과보고서.md, docs/decisions.md, docs/implementation_objects.md, TODO.md, AGENTS.md
- 확인 방법: pytest71 passed/live1 제외·Ruff/포맷·프론트 lint/type/format 통과. 원본 정답 intent63.33→86.67%, recall60.42→66.67%, 인용33.33→45%, 거절90→86.67%, Solar 요지26.67→53.33%. 중간 요지73.33%에서 퇴행도 그대로 기록. 실제 PNG7장63/65·검수TP1/FP0/FN1/TN63, 추가 추출 호출0. 후속3문항과 Q22진단1문항은 전체점수에 섞지 않았다.
- 남은 문제 · 질문: Q04 의미상 오안내를 Solar가 통과시킨 채점 한계, Q10 운영기준 충돌, Q22 간헐적 도구 오류, Q27/28 채점 오판 후보를 보고서에 명시했다. 자동 금지표현0건을 안전성 보장으로 해석하지 않는다. File Search 미실행. 배포빌드는 Turbopack 보조 포트 권한 오류/대체 Webpack 정체로 성공 미확인, 임시 설정 원복. 기존 실행 서버 검토함13건 정상 응답을 브라우저에서 확인했다.

## 2026-10-16 · T-06 · 고객 10명 시연 세트와 출처 검증
- 관련 요구사항: FR-05, FR-06, FR-14, FR-15
- 한 일: customers.json 단일 원본·공통 HTML/PNG/정답 생성기·10고객/13청구/29서류 시드·폴더별 검증 CLI를 구현했다. 상태를 엔진에서 계산하고 C73/90일 안내·코드 미기재 보완·처방 없는 OTC 대조를 추가했다. 계약일과 보장일을 분리하고 실제/mock 출처와 숨김 설정, 고객별 원본 연결, 사진 선택/fallback을 제공했다. 김유정 기존7장·동명이인·복수청구는 보존했다.
- 바뀐 파일: backend/scripts/samples/{gen_claim,render,seed_samples,verify_samples}.py, scripts/seed.py, backend/app/{models,db,config}.py, services/{rules,coverage,workspace,normalize,silson24}.py, routers/{review,supplements}.py, tests/test_demo_samples.py, data/samples/, data/mock_silson24/, frontend/components/{claim-screens,review-screen}.tsx, frontend/lib/workspace.ts, docs/03_data_design.md, docs/prompts/gpt_image_photo.md, docs/deliverables/T05-T06_시연데이터검증.md, TODO.md, artifacts/t06/
- 확인 방법: 백엔드62 passed/live1 제외·Ruff/포맷, 프론트 lint/typecheck/format/build 통과. 10고객 mock 기대 이슈10/10; 신규 실제 C002/C006 3장·9호출, 전체 정규화74/74. 김유정 캐시114/116·알려진추가2이슈 명시; 재생 전부0호출. CUA 신규22장 A4 캡처·인박스4상태·원본 비교100%와 두 이미지 로딩 확인. 생성기 direct/module 및 변경 없는 재실행 확인.
- 남은 문제 · 질문: GPT 사진4장은 사용자 제작 예정이며 사진 OCR 실측은 미진행. 신규 API 비용 추정 $0.162~0.282(VAT 별도), 실제 콘솔 차감액 미확인. 실측값·정답 mock을 혼동하지 않도록 보고서에 분리했다.

## 2026-10-16 · T-05 · 수술확인서와 보완 회신 흐름
- 관련 요구사항: FR-06, FR-13, FR-25
- 한 일: 기존 A4 HTML 토큰을 공통 모듈로 분리하고 보완 회신용 수술확인서 HTML/PNG/정답 JSON을 supplement/에 만들었다. 최초 김유정 7장에는 추가하지 않았다. 회신 업로드 시 새 서류만 처리하고 기존 원본/확정값은 보존하며 CV-04 해소·회신 완료·이력을 연결했다. 데모 모의 입력은 제공 파일의 정확한 해시와 고객 일치 시만 허용하고 표시/모드 설정을 추가했다.
- 바뀐 파일: backend/scripts/samples/{common,gen_supplement}.py, services/demo_samples.py, services/pipeline.py, routers/claims.py, config.py, frontend/components/claim-screens.tsx, data/samples/kim_yujeong/supplement/, .env.example
- 확인 방법: pytest56 passed/live1 제외; 보완 생성→모의 발송→회신 업로드→CV-04 해소→needs_review→중복 방지와 확정값 보존 통합 테스트. CUA로 기존 1240×1754 HTML 캡처. lint/typecheck 통과. 실제 API 추가0.
- 남은 문제 · 질문: T-06 고객별 공통 생성기·시드·검증 진행.

## 2026-10-16 · T-17 · 챗봇 화면과 청구 맥락 연결
- 관련 요구사항: FR-28~34
- 한 일: polish 토큰으로 대화 목록·질문 바로가기·중앙 대화·입력창·근거 패널을 연결했다. 답변 아래 문서명/조항/인용문·가상 표시, 청구별 이슈 상세 앵커, 자동 claim_id, 생성 단계 안내, 편집/복사 가능한 보완 초안과 액션을 제공한다. CV-02 안내를 차단 이슈와 구분해 표시한다. 처방전 자체가 없으면 약품 부재를 단정하지 않도록 대조 경계를 보완하고 모델/스키마 오류는 안전한 503으로 처리한다.
- 바뀐 파일: frontend/components/chat-screen.tsx, claim-screens.tsx, review-screen.tsx, workspace-shell.tsx, frontend/app/(protected)/chat/page.tsx, globals.css, backend/app/{routers/chat.py,services/coverage.py}, backend/tests/test_chat.py, TODO.md, docs/06_eval_plan.md, docs/deliverables/T15-T17_챗봇검증.md, artifacts/t17/
- 확인 방법: pytest55 passed/live1 제외, Ruff·포맷 통과. 프론트 lint/typecheck/format/date1/build 통과. CUA Playwright로 필수 질문1~4 실제 실행/캡처, 초안 수정·복사 버튼 성공·액션·이슈1 상세 이동·청구 맥락 자동 전달·가로 넘침 없음 확인. 실제 policy_qa도 암진단특약 제3조를 인용해 응답했다. 프로토타입 SCR-20의 3열·대화/근거 구조와 현재 polish 색/글꼴을 유지하고, pill 대신 아이콘/글자로 가상 여부·안내를 표시했다.
- 남은 문제 · 질문: 서버형 Qdrant 실제 접속과 평가30문항 전체 점수는 미검증(T-18). 대화 기록은 현재 화면 메모리이며 새로고침/재진입 시 사라진다. JSON 응답 방식은 이번 사용자 명세를 따른다.

## 2026-10-16 · T-16 · LangGraph 도구와 근거 답변
- 관련 요구사항: FR-15, FR-28~33
- 한 일: Solar strict 의도 5종→검증된 도구 호출→근거 답변 그래프와 JSON POST /api/chat을 추가했다. 읽기 도구 6종은 배정 권한을 재검사하고 조회 이력만 남긴다. 약품명 괄호 설명을 정규화해 실제 영수증 항목과 처방전을 대조하며 지급 판단은 거절한다. 근거 없는 질문은 지정 문구로 응답하고 표준 보완 문구에만 고객명을 채운다. 임베딩 외 대화 응답은 디스크에 보존하지 않는다.
- 바뀐 파일: backend/app/agent/{graph,tools,solar}.py, app/schemas/{chat,to_upstage}.py, app/services/coverage.py, app/routers/chat.py, app/main.py, app/scripts/chat_smoke.py, tests/test_chat.py, tests/test_rules.py, docs/implementation_objects.md, AGENTS.md
- 확인 방법: 전체 pytest 54 passed/live1 제외. 실제 chat_smoke 4질문과 기대10항목 모두 통과(7/8, CV-04/CV-01/세분류/CV-02 안내/액션/비타민 근거/초안/거절). artifacts/t16/chat_smoke.json에 실제 원문. 병렬 도구 전부 실행·권한·extra 인자·잘린 JSON·근거 없음·대화 미저장도 mock 테스트.
- 남은 문제 · 질문: 자동 청구 저장 이슈와 별개로 약관 대조 도구는 현재 입력의 규정 근거와 가능성만 반환한다. 실제 지급 판단은 범위 밖. T-17 화면 검증 진행.

## 2026-10-16 · T-15 · 조항 인덱싱과 CV-02 안내 분리
- 관련 요구사항: FR-14, FR-28
- 한 일: 허용 목록의 TXT/가상 MD만 조·항/매뉴얼 절로 분할하고 payload 전체를 보존했다. Solar passage/query 구분·100개 배치·내용 캐시, Qdrant 서버/로컬 설정, CLI를 구현했다. CV-02 1일 차이는 info로 분리해 차단하지 않고 2일 이상/실제 입퇴원일 차이는 불일치로 유지했다. 기대값·평가 질문을 동기화했다.
- 바뀐 파일: backend/app/agent/{kb,rag,solar}.py, app/scripts/build_index.py, config.py, models.py, services/rules.py, services/workspace.py, routers/claims.py, tests/test_rag.py, tests/test_rules.py, .env.example, pyproject.toml, uv.lock, data/eval/, data/samples/kim_yujeong/answers/_claim.json
- 확인 방법: pytest 기존+CV 44 passed / live 1 제외; RAG+규칙 7 passed. 실제 인덱싱 policy479/manual13, 2질문 모두 top-3 목표 조항 적중(특약2 제4조, 암진단특약 제3조 각각2위). artifacts/t15/retrieval.json. HWP Parse 0, reference 미포함.
- 남은 문제 · 질문: T-16 챗봇·화면 연결 진행. 긴 항/상품 개요 분할과 dense 후보 단어 가중치는 decisions.md에 기록.

## 2026-10-16 · T-15 · 지식 베이스 문서와 평가 질문 추가
- 관련 요구사항: FR-28
- 한 일: feat/chatbot 생성 전 polish/ui-1의 main 포함을 확인했다. 공개 표준약관·가온 가상 특약/매뉴얼·평가 질문을 추가하고 실제 회사 약관 reference/는 Git과 인덱싱 대상에서 제외한다. HWP는 보관만 하며 이번에는 Parse하지 않는다.
- 바뀐 파일: .gitignore, data/kb/README.md, data/kb/policy/, data/kb/gaon/, data/eval/chat_questions.json
- 확인 방법: git diff --cached --name-only로 reference/ 미포함 확인. 평가 JSON 30문항 파싱 확인.
- 남은 문제 · 질문: 인덱싱·검색 검증은 T-15 구현 커밋에서 진행.

## 2026-10-16 · polish-1 · 비교 기본 비율 복원 · 이동·강조 유지
- 관련 요구사항: FR-22
- 한 일: 사용자 추가 요청에 따라 비교 버튼 및 이슈 URL 직접 진입 시 자동 300% 확대를 제거하고 기본 100%로 복원했다. 두 서류 대상 칸 이동·강조와 공유 수동 확대/축소는 유지한다. 버튼 가림 방지·표 첫 행 보완 등 나머지 polish 변경은 그대로 둔다. 코드에 판단 이유를 한국어 주석으로 남겼다.
- 바뀐 파일: frontend/components/review-screen.tsx, artifacts/polish-1/after/compare-default-100*, compare-manual-zoom.jpg, docs/06_eval_plan.md, docs/deliverables/polish-1_검증과롤백.md
- 확인 방법: npm run lint / typecheck / format:check / build 통과. CUA에서 비교 버튼 진입·issue=3 직접 진입 모두 100%, 강조 박스 2개, 수동 100→120→100 및 두 서류 동시 확대 확인. 이미지 원래 비율 0.70696 / 표시 비율 0.70627(픽셀 반올림)로 왜곡 없음. 백엔드 변경·외부 API 호출 없음.
- 남은 문제 · 질문: 없음. 별도 작업의 .gitignore·data/eval/·data/kb/는 제외.

## 2026-10-16 · polish-1 · 화면 가림·비교 초점·표 스크롤 보완 (3·5·6번)
- 관련 요구사항: FR-18, FR-21~24
- 한 일: 어시스턴트 버튼을 본문 뒤 정상 흐름으로 옮겨 표 가림 제거. 비교 진입 시 공유 300% 확대·대상 칸 자동 스크롤·두 칸 강조, 320% 공유 확대도 확인. 실손24 대응 가상 서식 위치는 제공 PNG 해시 일치 시에만 표시하며 AI 좌표로 저장하지 않는다. 문서/비교 전환 시 표 컨테이너를 새로 만들어 첫 행부터 표시하고 머리글 고정. before/after 및 DOM 검증 JSON 저장. 데이터·로직 커밋 3c96d49와 별도 분리.
- 바뀐 파일: frontend/components/review-screen.tsx, workspace-shell.tsx, frontend/lib/reference-form.ts, frontend/app/globals.css, artifacts/polish-1/after/, docs/deliverables/polish-1_검증과롤백.md
- 확인 방법: pytest 43 passed (live 1 제외), 날짜 Node test 1 passed, Ruff·lint·typecheck·format:check·build 통과. DOM 검증: 처리 전 12행/김유정 제외, 기존 김유정 7/8·5이슈 유지, 두 비교 박스 모두 가시 영역 안, 확대율 양쪽 3.2 동일, 표 진입/탭 전환 scrollTop=0 및 첫 행 top>=헤더 bottom, 마지막 행/버튼 overlaps=false. 캡처는 artifacts/polish-1/before, after. 실제 Upstage 추가 호출 0.
- 남은 문제 · 질문: 없음. 여러 상태의 고객별 서류 세트는 요청대로 T-06에서 작성. 별도 작업의 .gitignore·data/kb/ 변경은 이번 커밋에서 제외한다.

## 2026-10-16 · polish-1 · 데이터·로직 보완 (1·2·4번)
- 관련 요구사항: FR-10, FR-13, FR-17~18, FR-24
- 한 일: 수정 전 550a95e에 ui-v1-before-polish 태그를 만들고 원격 push, polish/ui-1 브랜치 생성. 빈 청구의 엔진 실행을 차단하고 처리 전 상태/필터를 추가; 상태 시드 제거. 가상 생일·접수 시각 패턴 수정 및 초기화 없는 보정 스크립트 추가. 한국 시간/날짜 표시 함수와 담당자용 이슈·안내 문구 정리. before 캡처 저장. 김유정의 원문·추출값은 유지.
- 바뀐 파일: backend/app/models.py, services/rules.py, services/presentation.py, scripts/polish_ui_1.py, data/seed/demo.json, frontend/lib/dates.ts, 관련 목록/이력/상세 화면, artifacts/polish-1/before/
- 확인 방법: pytest 43 passed (live 1 제외), 날짜 함수 Node test 1 passed, Ruff·lint·typecheck 통과. 화면 디자인 검증과 최종 빌드는 별도 디자인 커밋에서 진행.
- 남은 문제 · 질문: 3·5·6번 화면 보완 진행 예정. 캐시·외부 API 호출 없음.

## 2026-10-15 · T-14 · 보완 처리 · 검토 이력 · 운영 관리 연결
- 관련 요구사항: FR-25~27
- 한 일: 누락 서류로 초안 생성·문구/채널 편집·모의 발송(회신 대기)·중복 발송 방지와 실제 감사 이력을 연결. 관리자만 low/원문 불일치/형식 오류 규칙과 필수서류 목록을 저장하며 즉시 재검사. 확정값·자동 해소 이슈 재발 처리와 화면 집계 일관성 보완, 객체 설명 추가. 프로토타입과 artifacts/t14/comparison.html에서 나란히 비교: 좌측 요청 목록/우측 보라색 문구 미리보기·시간선·운영 카드 구성 유지, 실제 목록 선택/초안 저장/모의 발송 표시 추가, 숫자 슬라이더는 요청한 3개 토글로 교체, 필수서류 10개 규칙·조건을 실제 DB에서 표시. 비교 중 발견한 배경 토큰과 버튼 클래스도 기존 토큰/btn으로 정리. T12·T13 캡처를 최종 스타일/실데이터로 갱신.
- 바뀐 파일: .env.example, backend/app/routers/supplements.py, backend/app/routers/settings.py, backend/app/services/supplement.py, frontend/components/operations-screens.tsx, docs/implementation_objects.md, artifacts/t12~t14/
- 확인 방법: pytest 41 passed / live 1 제외; Ruff·lint·typecheck·format:check·build 통과. Playwright 초안→모의발송→회신대기/이력, 관리자 토글 끄기→복원·규칙 저장, 상세 단계 저장·미해결 이슈 제출 차단 확인. 최종 DB 고객10/계약10/청구13·김유정7/8·열린이슈5·C18 세분류 누락·약제비 covered low0 확인. 외부 API 추가0페이지.
- 남은 문제 · 질문: 남은 질문 없음. Solar 실호출은 하지 않았고 HTTP 모킹으로 생성/캐시 경로를 검증; 로컬 시연은 캐시 전용 표준 문구 사용.

## 2026-10-15 · T-13 · 원본 좌표 · 비교 · 확정값 검토 연결
- 관련 요구사항: FR-21~24
- 한 일: 인증된 원본 조회, 실제 word/Parse bbox, 확대·축소, 이슈의 두 서류 나란히 비교, 출처·높음/낮음·검토 이유 표, 담당자 확정값과 이슈 확인 API 및 이력을 연결. 변경값으로 규칙 재검사하며 AI 원래 값은 보존. artifacts/t13/comparison.html에서 프로토타입과 비교: 2열/보라색 톤 유지, 가상 자리표시 문서→실제 제공 PNG, 숫자 신뢰도→높음/낮음, 카드형 이슈→압축 행, 양쪽 높이 700px 동일화. 실손24는 대응 가상 서식 표시를 명시.
- 바뀐 파일: backend/app/routers/review.py, backend/app/services/rules.py, frontend/components/review-screen.tsx, artifacts/t13/
- 확인 방법: pytest 38 passed / live 1 제외; Ruff·lint·typecheck·build 통과; Playwright 좌표 선택/120% 확대/입원일수 원본 비교 및 캡처
- 남은 문제 · 질문: 없음

## 2026-10-15 · T-12 · 검토함 · 청구 상세 API 연결
- 관련 요구사항: FR-05, FR-18~20
- 한 일: 실제 고객·계약·청구·서류·이슈로 검색/필터/집계를 연결하고 4단계 저장, 메모, 업로드·캐시 처리·제출 게이트를 구현. 김유정 실측 캐시를 DB에 연결해 제출 7/필요 8과 이슈 5건을 표시. 프로토타입과 나란히 비교(artifacts/t12/comparison.html): 보라색 토큰·사이드바·4단계·2열 구성 유지, 시연값 5/6→실데이터 7/8, 동명이인 구분용 생년월일·계약기간·특약·실행 버튼 추가; 헤더는 기존 로그인 사용자 표시를 유지.
- 바뀐 파일: backend/app/services/workspace.py, backend/app/routers/claims.py, frontend/components/claim-screens.tsx, frontend/lib/workspace.ts, artifacts/t12/
- 확인 방법: pytest 37 passed / live 1 제외; Ruff 통과; lint/typecheck/build 통과; Playwright 검토함→김유정 상세 탐색 및 캡처; 캐시 초기화 스크립트 외부 호출 0
- 남은 문제 · 질문: 없음

## 2026-10-15 · T-02b · 고객·계약 테이블과 시드 확장
- 관련 요구사항: FR-07, FR-14
- 한 일: 고객·계약 FK, 가상 고객 10명·청구 13건·동명이인·복수 청구·기간 밖·미가입 특약 사례를 추가했다. 기존 청구와 자식 문서를 보존하는 SQLite 트랜잭션 마이그레이션, CV-06·가입 특약 대조를 구현하고 데이터 설계를 갱신했다.
- 바뀐 파일: backend/app/models.py, db.py, migrations.py, services/rules.py, backend/scripts/seed.py, data/seed/demo.json, backend/tests/test_contracts.py, test_seed.py, test_foundation.py, docs/03_data_design.md
- 확인 방법: pytest 35개 통과. 이전 claims/자식 documents를 유지하며 FK 전환·시드·동명이인·계약기간·특약 대조 확인.
- 남은 문제 · 질문: 없음

## 2026-10-15 · A · 원문 대조 정밀화·약제비 구분 판단
- 관련 요구사항: FR-10, FR-14, FR-16
- 한 일: 부분 코드와 청구 내 독립 Parse 근거의 세분류 차이를 표시하고 high여도 확인 필요로 보낸다. 약제비 구분은 유일한 품명 행의 Parse 표 근거로 판정하며 모델 low 원본은 보존한다.
- 바뀐 파일: backend/app/services/source_evidence.py, normalize.py, rules.py, pipeline.py, backend/scripts/validate_engine.py, backend/tests/test_source_refinement.py, docs/deliverables/T07-T11_실제검증.md, docs/decisions.md, data/evaluations/png/*
- 확인 방법: 자동 테스트 33개 통과, --cached 재생에서 FIELD-diagnosis_code/not_in_source/원문과 다름(세분류 누락) 확인. 약제비 covered 확인 필요 4→0, 추가 API 0페이지.
- 남은 문제 · 질문: 없음

## 2026-10-15 · T-11 · 업로드·백그라운드 파이프라인·실제 검증
- 관련 요구사항: FR-06, FR-12, NFR-02, NFR-05, NFR-08
- 한 일: 이미지/PDF 업로드·실손24 연결·비동기 process·영속 상태 조회·이력 API를 연결했다. 파일/페이지/용량/역할/이중 실행 검증, 서버 재시작 실패 복구, 문서별 실패 보존을 구현했다. 입력 폴더 인자와 폴더/내용 지문별 평가 스크립트, 기본 제외 live 테스트를 추가했다. 실제 v1 호출은 앱 4장에 한 번만 수행하고, 실측 파서 보완은 캐시 전용으로 재생했다. 프론트는 변경하지 않았고 API 가이드는 11절만 갱신했다.
- 바뀐 파일: backend/app/services/pipeline.py, uploads.py, upstage.py, silson24.py, normalize.py, rules.py, routers/claims.py, models.py, config.py, main.py; backend/tests/*; scripts/validate_engine.py; pyproject.toml·uv.lock; .env.example·.gitignore·AGENTS.md; docs/upstage_api_guide.md(11절), implementation_objects.md, decisions.md, deliverables/T07-T11_실제검증.md; data/evaluations/png/*
- 확인 방법: pytest 31개 통과(live 1개 기본 제외), ruff check/format 및 git diff --check 통과. 실제 요청 12회×1페이지, 모두 200, 예약 12/30·재시도 0, 62.04초. 이미지 분류 4/4, 앱 항목 37/39(94.87%), 실손24 77/77, 기대 핵심 이슈 3/3. 캐시 재평가 신규 요청 0. 로컬 서버 /health 200·비로그인 status 401·로그인 status 200 확인.
- 남은 문제 · 질문: C18.7→C18(high)·병리 한글 설명 추가로 정답 2개 불일치. 추가 CV-03 1건·약제비 covered low 4건, 직인 low 없음. 사진판·T-16 약관 대조·CV-06은 제외. 기존 TestClient deprecation warning 1건.

## 2026-10-15 · T-10 · 청구 단위 필수서류·교차검증·라우팅
- 관련 요구사항: FR-13, FR-14, FR-16, FR-17
- 한 일: 필수 서류 조건·CV-01~05·high/low 및 원문·형식 라우팅을 구현했다. 모든 관련 문서 쌍을 대조하고 cross_check 이유를 필드에 남긴다. 동일 이슈 재생성을 방지하고 엔진은 정답을 읽지 않는다. 누락은 supplement, 나머지 문제는 needs_review, 문제가 없을 때만 auto_pass로 보낸다.
- 바뀐 파일: backend/app/services/rules.py, config.py, models.py, backend/tests/test_rules.py, .env.example, docs/decisions.md
- 확인 방법: pytest 전체 22개 통과. 정답 7장 입력 → CV-04 누락 1, CV-01/02 불일치 2 정확히 검출; 강제 low 입력 시 확인 필요 1 추가. 정상·형식 오류·설정 off·CV-03·CV-05·처리 실패도 검증.
- 남은 문제 · 질문: CV-03은 시연용 제한 참조어 대조다. CV-06 계약기간과 T-16 약관 대조는 제외.

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
