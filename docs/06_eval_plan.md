# 06. 샘플 · 평가 계획

## 목업 데이터 세트 (확장 계획, 2026-10-15)
- 만드는 법: 서류 서식을 **HTML로 만들고 캡처** → Python(OpenCV/PIL)으로 촬영 왜곡(기울기, 원근, 그림자, 구김, 직인 겹침, 저해상도)을 입혀 "폰으로 찍은 사진"처럼 만든다
- 서식 주의: 보험 청구용 진료비 영수증은 **법정 서식(진료비 계산서 · 영수증)** 이다. 감열지 간이 영수증 모양은 실제 청구 서류와 다름 → 법정 서식 레이아웃을 따른다
- 병원 · 약국 이름, 주소, 전화번호, 고객 이름은 전부 가상 (실존 기관 · 사람과 겹치지 않게)
- 규모 목표: 고객 8~10명 × 청구 1~2건 × 서류 4~8장
  - 정상 통과 건, 누락 건, 불일치 건, 저신뢰(직인 · 흐림) 건, 약관 제외 항목(영양제 등) 건을 골고루
- 각 서류마다 정답 JSON(표준 스키마 값)을 같이 만든다 → 평가 정답셋으로 재사용

## 가상 서류
- Tier1 6종 × 레이아웃 변형 2~3개
- 왜곡: 기울기, 그림자, 구김, 직인 겹침, 저해상도(팩스)
- 의도적 오류 심기: 진단일 역전, 입원기간 불일치, 서류 누락

## 지표 (초안)
| 지표 | 정의 |
|---|---|
| 항목 정확도 | 정답과 일치한 추출 항목 비율 |
| 누락 탐지율 | 심어둔 누락 중 잡아낸 비율 |
| 불일치 탐지율 | 심어둔 불일치 중 잡아낸 비율 |
| 검수 대상 비율 | 전체 항목 중 사람에게 넘어간 비율 |
| 오탐률 | 문제 없는데 검수로 보낸 비율 |

## 챗봇 평가 (FR-28~35)
- 질문 30개: 약관 · 기준 12, 청구 조회 · 검토 8, 항목 보상 대상 6, 근거 없는 질문 4
- 질문마다 정답 조항 · 정답 요지를 적어 둔다 (`data/eval/chat_questions.json`)
| 지표 | 정의 |
|---|---|
| 근거 적중률 | 정답 조항이 인용 상위 3개 안에 있는 비율 |
| 답변 정확도 | 정답 요지와 맞는 답변 비율 (사람 채점) |
| 거절 정확도 | 근거 없는 질문에 "찾지 못했어요"로 답한 비율 |
| 판단 경계 위반 | 지급 여부를 단정한 답변 수 (목표 0) |

## 결과 기록
| 날짜 | 데이터 | 항목 정확도 | 탐지율 | 오탐률 | 검수 대상 비율 | 근거 적중률 |
|---|---|---|---|---|---|---|
| 2026-10-16 | 실제 API PNG7장·3고객·65항목 | 63/65 (96.92%) | 오류 검수 재현율1/2 (50%) | 0/63 (0%) | 1/65 (1.54%) | recall@3 66.67% (원본24문항) |
| 2026-10-16 T-18b | 동일 PNG 캐시·정답 병기 누락 수정 | 64/65 (98.46%) | 1/1 (100%) | 0/64 (0%) | 1/65 (1.54%) | recall@3 89.58% (수정 정답24문항) |

오류 검수 정밀도1/1(100%). 실손24 mock 포함 보조 정확도188/190(98.95%)는 OCR 성능이 아니다. 상세는 `artifacts/t18/extract_eval.md` 참고. 챗봇은 사용자 명시 전송 승인 후 동일30문항으로 전/중간/최종을 실측했다. 원본 기준 intent63.33→86.67%, recall@3 60.42→66.67%, 인용33.33→45.00%, 거절90.00→86.67%, 요지26.67→53.33%. 금지표현 정규식0건이나 Q04 의미모순은 사람이 발견했다. Q08/Q18 라벨 수정 재채점은 recall70.83%·인용47.50%로 별도 기록했다.


## 티켓별 테스트 결과

기능 구현 검증을 기록한다. 위의 정확도·탐지율 등 제품 성능 평가와는 별개다.
T-01~T-04는 WORKLOG의 당시 실행 결과를 옮겼다. 이후에는 티켓 완료 시 한 줄씩 추가하고, 같은 티켓의 추가 수정 검증은 해당 행을 갱신한다.
명령은 프로젝트 루트에서 실행하며, `cd backend`가 표시된 명령은 그 폴더에서 이어서 실행한다.

| 티켓 | 테스트 항목 | 결과 | 실행 명령 | 날짜 |
|---|---|---|---|---|
| T-01 | /health 200, SQLModel 테이블 12개 생성, 외래키 제약, 환경변수 우선순위·비밀값 표시 방지 | 통과: 당시 pytest 2개, ruff 통과 | `cd backend && .venv/bin/python -m pytest tests/test_foundation.py -q && .venv/bin/ruff check app tests` | 2026-10-15 |
| T-02 | 계정 2개·청구 6건·규칙·설정 시드, 재실행 중복 방지, --demo 초기화 | 통과: 시드 users 2 / claims 6, 당시 전체 pytest 3개, ruff 통과 | `cd backend && .venv/bin/python -m scripts.seed --demo && .venv/bin/python -m pytest && .venv/bin/ruff check app tests` | 2026-10-15 |
| T-03 | 두 역할 로그인·로그아웃, 쿠키 변조, DB 역할 변경, 관리자 API 401/403, 담당 청구 접근 | 통과: 당시 전체 pytest 9개, ruff 통과. 환경 정리 후 실제 서버 재시작 전 쿠키로 /api/me·메인 200 및 동일 사용자 확인 | `cd backend && .venv/bin/python -m pytest tests/test_auth.py -q && .venv/bin/ruff check app tests`; 재시작 검증: uvicorn 중단·재실행 후 httpx로 기존 쿠키 재사용 | 2026-10-15 |
| T-04 | 린트·타입·포맷·배포 빌드, 실제 브라우저 로그인 유지·역할 전환·관리자 경로 제한·화면 이동, 원본 로고 SVG 대조 | 통과: lint/typecheck/format:check/build, 브라우저 연동 확인. 로고 수정 후 lint/build 통과 | `cd frontend && npm run lint && npm run typecheck && npm run format:check && npm run build`; 브라우저 수동 확인(`artifacts/t04/verification.md`) | 2026-10-15 |
| T-07 | 정답 3종 연결, 값 보존, 중복 방지, 401·403·404와 수신 이력 | 전체 11개 통과 | `cd backend && .venv/bin/python -m pytest tests/test_silson24.py -q` | 2026-10-15 |
| T-08 | HTTP 모킹, v1 옵션, 캐시·오프라인·동시 중복, 재시도·타임아웃·예산·키 반사 제거 | 전체 15개 통과; 실제 API 호출 0 | `cd backend && .venv/bin/python -m pytest tests/test_upstage_client.py -q` | 2026-10-15 |
| T-09 | 스키마 타입·중첩 제약, 정규화, 형식·원문·신뢰도, 좌표, 실손24 null confidence | 전체 19개 통과 | `cd backend && .venv/bin/python -m pytest tests/test_normalize.py -q` | 2026-10-15 |
| T-10 | 정답 expected_issues 비교·필수 8종·CV-01~05·low/format/실패·라우팅 | 전체 22개 통과; 누락 1·불일치 2 정확히 검출 | `cd backend && .venv/bin/python -m pytest tests/test_rules.py -q` | 2026-10-15 |
| T-11 | 업로드·PDF/페이지·용량·권한·중복·백그라운드·실패·이력·재시작·캐시 재생·실제 4장 검증 | 31개 통과, live 1개 기본 제외; 유료 입력 12/30페이지; 핵심 3/3, 앱 37/39, 전자 77/77 | `cd backend && .venv/bin/python -m pytest`; `.venv/bin/python -m scripts.validate_engine --cached` | 2026-10-15 |
| A | 부분 코드 high·행별 급여·캐시의 실제 C18 이슈 | 33개 통과; C18 확인 필요 검출; 추가 과금 0 | `cd backend && .venv/bin/python -m pytest && .venv/bin/python -m scripts.validate_engine --cached` | 2026-10-15 |
| T-02b | 고객 10·청구 13·동명이인·FK·기존 DB 보존·CV-06·특약 | 35개 통과 | `cd backend && .venv/bin/python -m pytest` | 2026-10-15 |
| T-12 | 검색·배정 권한·집계·단계 저장·7/8 조회·화면 캡처 | 통과 (37 tests; 실측 캐시 0과금) | pytest -q; npm run lint; npm run typecheck; npm run build | 2026-10-15 |
| T-13 | 원본 권한·확정값 형식/원본 보존·규칙 재검사·확인 이력·화면 | 통과 (38 tests, 추가 API 0페이지) | pytest -q; ruff check app tests; npm run lint; npm run typecheck; npm run build | 2026-10-15 |
| T-14 | 모의 발송 상태·중복/권한·설정 재검사·Solar 캐시/표준 문구·화면 캡처/비교 | 통과 (41 tests; 문서 추가 API 0/5페이지) | pytest -q; ruff check app tests; npm run lint; npm run typecheck; npm run format:check; npm run build | 2026-10-15 |
| polish-1 | 빈 접수 엔진 차단·상태/시드/날짜/안내; 버튼 가림·비교 초점·표 첫 행 | 통과: backend 43, 날짜 1, UI 6건·build; 추가 검증: 비교 기본 100%·공유 수동 확대·강조 유지, lint/typecheck/format/build 통과; 추가 API 0 | pytest -q; Ruff; node --experimental-strip-types --test tests/dates.test.mjs; npm run lint/typecheck/format:check/build; CUA Playwright·DOM 캡처 | 2026-10-16 |
| T-15 | 조·항/절 분할·payload·reference 제외·임베딩 캐시·CV-02 4경계·실제 top-3 | 통과: 규칙/RAG 7개, 실제 2질문 2/2 적중; policy479/manual13 | pytest tests/test_rag.py tests/test_rules.py -q; uv run python -m app.scripts.build_index; retrieval.json | 2026-10-16 |
| T-16 | LangGraph·strict·6도구 권한·병렬 호출·대조·초안·거절·근거 없음 | 전체 pytest54 통과/live1 제외; 실제 필수4질문·기대10항목 통과 | pytest -q; ruff check; uv run python -m app.scripts.chat_smoke | 2026-10-16 |
| T-17 | 실제 질문4·근거/가상 표시·편집 초안·액션·청구 이슈 링크·맥락·로딩 | 통과: pytest55/live1 제외; 프론트 lint/type/format/date1/build, 브라우저 실제4질문·연결 검증 | pytest -q; ruff; npm run lint/typecheck/format:check/build; Node dates; CUA Playwright 캡처 artifacts/t17/ | 2026-10-16 |
| T-05 | 수술확인서·회신 자동 검토·CV-04 해소·회신완료·확정값/중복 보존 | pytest56 통과/live1 제외; lint/typecheck 통과; 추가 API0 | pytest -q; npm run lint/typecheck; CUA A4 캡처 | 2026-10-16 |
| T-06 | 고객10·청구13·서류29·4상태·동명이인·출처·사진 선택·90일 경계·폴더 검증·실측 | pytest62/live1 제외, Ruff/포맷·프론트 lint/type/format/build 통과; mock10/10, 신규실측74/74·3장9호출, 캐시0호출 | pytest -q; ruff check/format --check; npm run lint/typecheck/format:check/build; python -m verify_samples --folder … [--cached]; CUA 캡처 artifacts/t06/ | 2026-10-16 |
| T-18 | 구조 트리·부모 JSON·보장종목·규범 준용·RRF ablation·안전 가드·실측30문항·필수4질문·추출 정답 감사 | T-18b pytest89/live1 제외·Ruff/포맷·프론트 lint/type/format 통과. 최종 의도100/recall89.58/인용75/거절100/요지83.33%. 배포 빌드 EPERM 미확인. 이전 기록 보존 | pytest -q; ruff check/format; python -m app.scripts.chunk_report; eval_retrieval; eval_chat --out artifacts/t18/final --phase after; chat_smoke --out artifacts/t18/final-smoke; eval_extract; npm run lint/typecheck/format:check | 2026-10-16 |

참고: 당시 TestClient의 httpx deprecation warning 1건이 있었으며 테스트 실패는 아니다. 개발 도구 의존성 감사 결과는 WORKLOG에 별도 기록했다.

## T-18b 원본·수정·개선 비교

# T-18b 라운드 비교

정답 변경 효과는 기존 답변을 그대로 재채점한 행으로 분리했다. Solar rubric은 모든 실제 라운드에서 동일하다. 최고 점수가 아닌 마지막 전체30문항 실행을 최종값으로 보고한다.

| 실행 | 의도 | recall@3 | 인용 정밀도 | 거절 | 요지 |
|---|---:|---:|---:|---:|---:|
| 1라운드 · 원본 정답/이전 최종 | 86.67% | 66.67% | 45.00% | 86.67% | 53.33% |
| 같은 답변 · 정답 수정 후 | 90.00% | 70.83% | 47.50% | 90.00% | 53.33% |
| 2라운드 | 93.33% | 93.75% | 82.14% | 100.00% | 66.67% |
| 3라운드 · 주소 보완 전 | 100.00% | 91.67% | 80.00% | 100.00% | 93.33% |
| 3라운드 · 주소 보완 후 | 96.67% | 87.50% | 80.00% | 96.67% | 86.67% |
| 최종 · 정상 조회 오거절 보완 | 100.00% | 89.58% | 75.00% | 100.00% | 83.33% |

최종 호 단위: recall@3 75.00%, 인용 정밀도 75.00% (Q09/Q23/Q25/Q26 4문항만 추가 측정). 조 기준을 호 기준으로 대체하거나 완화하지 않았다.

최종 금지 표현0 / 호출 오류0. 최종 요지25/30. 3라운드 중간 요지28/30보다 내려갔으며 아래 원문과 채점 오판 후보도 보존한다.

## 청킹·검색 ablation

| 같은 새 구조 인덱스에서의 검색 | recall@3 |
|---|---:|
| 이전 점수식 고정 = 청킹/머리말만 변경 | 60.42% |
| 순수 dense 참고 | 62.50% |
| RRF+재작성+재정렬 | 91.67% |

dense 참고를 청킹-only라고 보고하지 않는다. legacy는 기존 점수식을 유지하고 주소 묶음 키만 새 구조로 바꾼 통제 실험이다. 이전 운영 검색 자체(수정 정답70.83%)와 달리 청킹-only는 성능이 낮아졌다. 구조만으로 검색 품질이 자동 개선된다는 주장은 하지 않는다.

## 정답·추출 비교

| 추출 기준 | 정확도 | 오류 검수 정밀도 | 재현율 |
|---|---:|---:|---:|
| 원본 정답 | 63/65 · 96.92% | 100% | 50% |
| 원본 문서 병기 누락 정답 수정 후 | 64/65 · 98.46% | 100% | 100% |
| 검증 코드 개선 후 | 64/65 · 98.46% | 100% | 100% |

정답에는 영문만 있었지만 원본 HTML과 Parse 모두 한국어 병기를 포함했다. FN→정상은 정답 수정 효과이며 탐지 알고리즘의 개선 효과가 아니다. 실제 오독은 C18.7→C18 한 건뿐이다. 번역·추가 단어 검증은 별도 회귀 테스트를 통과했다.


실패24개 선분류는 failure_triage.md, 최종 미달14문항의 원문·rubric·사람 검토는 remaining_failures.md에 있다. 원문 진단명 병기 누락 정답 수정으로 오른 추출 수치는 알고리즘 개선으로 보고하지 않는다. 준용 실측은 hierarchy_smoke.json, 필수4질문은 final-smoke/chat_smoke.json, 프론트 실패 지점은 frontend_build.md를 참고한다.
