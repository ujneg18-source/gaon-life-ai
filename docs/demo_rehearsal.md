# 시연 리허설 (T-19x)

디자인·문구·온보딩 배치·홀드아웃·평가 정답·안전 규칙은 유지했다. 관리자 초기화 버튼만 기존 버튼 스타일로 추가했다.

## 실행

프로젝트 루트에서:

```bash
cd backend
uv run python -m app.scripts.demo_reset
# 별도 터미널에서 시연 백엔드 실행: 캐시 전용, 네트워크 호출 없음
DEMO_MODE=true SOLAR_RESPONSE_CACHE=true USE_CACHED_RESULTS=true uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

프론트 프로덕션 서버를 실행한 뒤 `cd frontend && npm run test:demo`. 관리자 버튼까지 확인하려면 `./node_modules/.bin/playwright test --reporter=line`. 테스트는 1 worker, 1440×900이며 마지막 finally에서 반드시 다시 demo_reset을 실행한다. 타이밍은 자동 조작 기준이며 발표자의 설명 시간은 포함하지 않는다.

`SOLAR_RESPONSE_CACHE=true`는 시연 응답 저장을 명시적으로 켠다. 기본 비저장 설정은 유지한다. `USE_CACHED_RESULTS=true`는 저장된 동일 요청만 재생한다. 새 질문을 캐시에 넣어야 할 때는 캐시를 보존한 채 별도의 준비 실행에서 네트워크를 허용하고(DEMO_MODE=false, SOLAR_RESPONSE_CACHE=true, USE_CACHED_RESULTS=false), 촬영 전 다시 시연/캐시 전용 모드로 돌아온다. 이번 동선은 기존 캐시로 전부 실행되어 추가 호출이 없었다.

## 병합

main에 feat/eval(PR #1) → feat/demo-polish 순서로 병합하고 원격 main에 반영했다. 충돌 파일 없음. 기존 PR #2는 기준 브랜치가 feat/eval이므로, 모든 커밋이 main에 포함된 것을 확인한 뒤 중복 PR을 닫았다. feat/demo-ready에서 후속 작업했다.

## 결과

| 구간 | 초 |
|---|---:|
| login | 0.538 |
| main-onboarding | 0.922 |
| inbox | 1.878 |
| detail-1 | 0.858 |
| detail-2-comparison | 0.073 |
| original-comparison | 0.290 |
| detail-3 | 0.360 |
| assistant | 0.366 |
| question-1 | 2.473 |
| question-2 | 0.503 |
| question-3 | 0.805 |
| question-4 | 0.625 |

초기 reset 0.626초 / 최종 reset 0.457초. 둘 다 30초 목표 충족.

최초 DB 보호 백업: `data/backup/gaon_20261016_2248.db`.
리허설 직전 백업: `data/backup/gaon_20261016_2300_01.db`.
마지막 백업: `data/backup/gaon_20261016_2300_02.db`.

SQLite backup API로 WAL을 포함한 일관된 복사본을 만든다. 같은 분에 재실행하면 `_01`, `_02`를 붙여 이전 백업을 보존한다. 백업 DB는 gitignore로 제외한다. 인덱스는 파일 존재만 확인하며 열거나 재생성하지 않는다. 시드 중 오류가 나면 해당 백업으로 복원한다.

프론트는 서버 초기화 revision을 감지해 앱 소유의 저장 상태와 메모리 채팅·안내를 비우고 메인으로 이동한다. 관리자 버튼은 확인 대화상자와 서버 관리자 권한 검사 뒤 실행하며 로그인 화면으로 돌아간다. CLI는 인증 쿠키를 바꾸지 않는다.

## 스크린샷 (artifacts/demo/)

- [01-login.png](../artifacts/demo/01-login.png)
- [onboarding-1.png](../artifacts/demo/onboarding-1.png)
- [onboarding-2.png](../artifacts/demo/onboarding-2.png)
- [onboarding-3.png](../artifacts/demo/onboarding-3.png)
- [onboarding-4.png](../artifacts/demo/onboarding-4.png)
- [06-main-onboarding.png](../artifacts/demo/06-main-onboarding.png)
- [07-inbox.png](../artifacts/demo/07-inbox.png)
- [08-detail-1.png](../artifacts/demo/08-detail-1.png)
- [09-detail-2-comparison.png](../artifacts/demo/09-detail-2-comparison.png)
- [10-original-comparison.png](../artifacts/demo/10-original-comparison.png)
- [11-detail-3.png](../artifacts/demo/11-detail-3.png)
- [12-assistant.png](../artifacts/demo/12-assistant.png)
- [13-question-1.png](../artifacts/demo/13-question-1.png)
- [14-question-2.png](../artifacts/demo/14-question-2.png)
- [15-question-3.png](../artifacts/demo/15-question-3.png)
- [16-question-4.png](../artifacts/demo/16-question-4.png)

## 검증과 제한

- pytest 147 passed / live 1 제외. Ruff 검사·포맷 통과. 프론트 lint·타입·포맷·Webpack 빌드 통과. 관리자/동선 E2E 2 passed.
- 콘솔 오류 0개. 기존 캐시 2,040개 삭제·변경 0개. 실제 Upstage 호출 0회(문서·Chat·Embedding 모두). 마지막 DB: 고객10/청구13/서류29/보완요청0, 김유정 step0·빈 메모.
- DEMO_MODE의 전체 외부 요청 대기 한도는 3초. 실패·초과 시 동일 지문의 유효 캐시만 허용하며 대체 사실은 서버 로그만 남긴다. 캐시가 없는 새 질문은 먼저 준비 실행이 필요하다. 지연된 요청은 이미 전송되었을 수 있어 취소/자동 재전송하지 않으며 완료 시 응답을 보관한다. 문서 요청의 budget/pending 보호는 유지한다.
- 로컬 Qdrant는 백엔드 프로세스 하나만 실행한다. 호스팅·실제 기간계 연동 검증은 이번 범위에 포함하지 않았다.
- npm audit에서 기존 개발용 lint 의존성 계열 5건 high가 표시된다. 제안된 Next lint 주요 버전 하향은 이번 시연 작업에서 적용하지 않았다.

상세 수치: [report.json](../artifacts/demo/report.json), 보존/최종 상태 검사: [verification.json](../artifacts/demo/verification.json).
