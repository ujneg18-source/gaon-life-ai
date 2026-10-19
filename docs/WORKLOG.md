## 2026-10-19 · T-19z · Vercel·무료 Render 배포 준비
- 관련 요구사항: FR-01, FR-04, FR-07~15, FR-28~35, NFR-06~07, NFR-10
- 한 일: 무료 Render용 Docker/Blueprint와 임시 디스크 부트스트랩을 추가했다. 실제 DB 대신 가상 고객 시드와 원본 대응 성공 캐시42개·Qdrant2개·구조 인덱스·기존 호출 예산 장부만 3.7MB 자산으로 묶고 SHA256 검증 후 복원한다. DB가 있으면 먼저 백업하며 캐시/기존 상태를 덮어쓰지 않는다.
  Vercel 서버 함수에서 출처 본문 외부 파일 경로가 누락되는 문제를 서버 전용 허용 목록12종으로 해결하고 Webpack 빌드를 명시했다. 디자인/문구·평가/홀드아웃/안전·기존 KB는 변경하지 않았다. 키·실제 DB/백업·개인 경로·HWP·평가 자료는 컨테이너에서 제외했다. 저장소는 비공개를 유지한다.
- 바뀐 파일: Dockerfile, .dockerignore, render.yaml, deploy/runtime-assets.*, backend/app/config.py, backend/app/scripts/deploy_start.py, backend/tests/test_deploy.py, frontend/server-data/source-texts.json, frontend/app/(protected)/data-sources/[source]/page.tsx, frontend/vercel.json, .env.example, docs/deployment.md
- 확인 방법: pytest150/live1제외, 프로젝트 지정 Ruff 범위·수정 파일 format, frontend lint/typecheck/format/Webpack 통과. HTTPS 로그인·청구 맥락4문항·초기화·재시작·자산 변조 거절·본문 동일성 검증. 빈 디스크 복원0.430초/reset0.251초, API0회. 전체 이력 키 검사·배포 묶음 키/개인 경로 검사 통과, 캐시2040개 변경/삭제0. 로컬 data/gaon.db는 건드리지 않았다.
- 남은 문제 · 질문: Docker 실행 도구가 없어 실제 Linux 이미지 빌드/호스팅 검증은 Render 배포 시 필요하다. Vercel/Render 계정 연결·실제 URL·서버 환경 변수 입력은 남아 있다. 일반 새 질문은 Render의 Upstage 키가 필요하고 호출 비용이 발생할 수 있다. 무료 Vercel Cron은 하루1회라 5~10분 핑은 외부 모니터가 필요하며 아직 생성하지 않았다. 기존 Git 이력의 작성자 메타데이터는 재작성하지 않았다. scripts 전체 Ruff 확장 검사에서는 기존 scripts/test_upstage.py의2건이 남아 있어 지정 검증 범위로 구분했다.

## 2026-10-16 · T-19y · 메인 투어 동작 설명 추가와 원격 main 반영 전 점검
- 관련 요구사항: FR-04~05, NFR-10
- 한 일: home 첫 단계 바로 뒤에 요청한 Upstage 문서 읽기/규칙 대조/Solar 근거 안내 1개만 추가했다. 기존 투어 전체를 새 단계 제거 후 원본과 비교해 동일함을 확인했다. 기존 검사와 리허설의 단계 수/인덱스만 5단계에 맞췄다.
  .env·키·DB·백업·캐시 제외와 전체 이력 비밀값 검사를 진행했다. 로컬 배포 도구/로그/검사 생성물 gitignore와 frontend의 Vercel 개발·검증 파일 제외 규칙을 추가했다. 평가/시연 기록은 보존했다.
- 바뀐 파일: frontend/lib/tours.ts, frontend/scripts/check-onboarding.mjs, frontend/e2e/demo.spec.ts, artifacts/demo/tour_home_2.png, .gitignore, frontend/.vercelignore
- 확인 방법: lint/typecheck/format·기존 check-onboarding·Webpack 빌드 통과. 실제 가이드라인에서 1/5→2/5→3/5→4/5→5/5 및 종료 확인. 요청 문구와 2단계 스크린샷 저장. 새 단계를 제외한 모든 투어 동일, CSS/컴포넌트 변경 없음. 실제 Upstage 호출0회.
- 남은 문제 · 질문: 호스팅 배포는 별도이며, Git에서 제외한 DB/캐시/Qdrant를 Render에 별도로 준비해야 한다. 기존 평가/시연 기록78.8MB는 보존했다.

## 2026-10-16 · T-19x · 브랜치 병합과 캐시 기반 시연 리허설
- 관련 요구사항: FR-01~05, FR-07, FR-13~15, FR-18~27, FR-28~34, NFR-06~07, NFR-10
- 한 일: PR #1과 feat/demo-polish를 main에 순서대로 병합(충돌 없음)하고 feat/demo-ready를 만들었다. DB 백업 후 시드·회신 상태 복원/인덱스·캐시 존재 검사 CLI와 관리자 확인 버튼을 추가했다. 프론트 revision으로 채팅/안내 상태를 초기화한다.
  시연 외부 요청 3초 한도·동일 지문 캐시 대체·실제 전송 시도 장부를 추가했다. 기본 대화 비저장과 budget/pending·홀드아웃·평가·안전·디자인·문구를 유지했다. 1440×900 전체 촬영 E2E와 관리자 확인/취소 테스트, 장면 캡처16개와 구간별 시간을 기록했다.
- 바뀐 파일: backend/app/services/demo_reset.py, backend/app/scripts/demo_reset.py, backend/app/routers/demo.py, backend/app/services/demo_deadline.py, backend/app/services/upstage.py, backend/app/agent/solar.py, backend/app/config.py, backend/app/main.py, backend/tests/test_demo_ready.py, frontend/components/demo-session-boundary.tsx, frontend/lib/demo-session.ts, frontend/app/(protected)/layout.tsx, frontend/components/operations-screens.tsx, frontend/e2e/, frontend/playwright.config.ts, frontend/package*.json, .env.example, .gitignore, docs/demo_rehearsal.md, artifacts/demo/
- 확인 방법: pytest147/live1제외·Ruff check/format·프론트 lint/typecheck/format/e2e-format/Webpack 통과. E2E2개 통과(19.2초), 콘솔0개, 실제 Upstage0회. 기존 캐시2040개 삭제/변경0, 최종 DB 고객10/청구13/서류29/보완요청0·김유정step0/빈 메모. 상세 시간·백업 경로·PNG 목록은 docs/demo_rehearsal.md와 artifacts/demo/report.json에 기록.
- 남은 문제 · 질문: 새 질문의 정확한 요청 캐시가 없으면 별도 준비 실행이 필요하다(타 요청 답변을 조작해 대신하지 않음). 로컬 Qdrant는 단일 백엔드만 허용한다. 기존 개발 lint 의존성 npm audit high5건은 주요 버전 하향 없이 남겨 두었다.

## 2026-10-16 · T-19w · 메인 카드 설명 문구와 두 줄 구분
- 관련 요구사항: FR-04~05, SCR-02
- 한 일: 업무 어시스턴트 설명을 ‘약관, 심사 기준, 업무 절차를 물어보면 / 관련된 근거 문서와 함께 답해 드려요’로 바꿨다. 워크스페이스 설명을 ‘청구 서류 분석부터 누락 불일치 확인 보완요청까지 / 한곳에서 처리해요’로 바꿨다. 요청한 위치에 명시적 줄바꿈을 넣고 실제 메인과 온보딩에서 같은 컴포넌트를 사용한다.
- 바뀐 파일: frontend/components/home-screen.tsx, artifacts/home-card-copy.jpg
- 확인 방법: lint 및 Webpack 배포 빌드 통과. CUA 메인에서 문구 일치와 각2줄 표시를 DOM 실제 줄 좌표로 확인했다. artifacts/home-card-copy.jpg에 최종 화면을 저장했다.
- 남은 문제 · 질문: 없음. 외부 API 호출 없음.

## 2026-10-16 · T-19v · 도움말 메뉴와 데이터 출처 페이지
- 관련 요구사항: FR-04~05, FR-18, FR-28~35, SCR-02/03/10~14
- 한 일: 물음표 버튼을40→60px로 키우고 가이드라인/업무 어시스턴트/데이터 출처 메뉴를 추가했다. 가이드라인은 기존 독립 안내, 어시스턴트는 청구 맥락을 보존한 챗봇, 출처는 새 페이지로 연결한다. 메뉴는 바깥 클릭·Escape로 닫고 키보드 초점을 관리한다.
  프로젝트 실제 자료를 대조해 공개 표준약관5종·가온생명 시연 문서7종·가상 시연 데이터2종을 분류한 출처 페이지와 본문 페이지를 만들었다. 고객10명/청구13건을 표시하며 실손24는 모의 연계임을 명시했다. 본문은 인증된 경로에서 허용 목록의12개 문서만 읽고 평가 정답·참고용 실제 회사 약관을 제외한다.
  첫 소개를 ‘보상 담당자의 청구 서류 대조·검토 업무를 지원합니다.’로 바꿨다. 워크스페이스와 해당 안내 헤더에 ‘서류 검토 워크스페이스’ 배지를 복원하고 챗봇 새 채팅 위에 ‘메인으로’를 추가했다.
  추가 요청에 따라 안내창 폭을460→438px(좁은 화면410→390, 첫 메인640→610)로 조금 줄이고 글자 크기를 유지한 채 여백을 정리했다. 어시스턴트 첫 안내는 꼬리/강조 없는 중앙 모달이다. 답변 강조는 AI 표시·요약·첫 검토 항목까지 확대하고 좁은 화면은 요약 범위를 사용한다. 글꼴 준비·배치 후 iframe이 준비 메시지를 보내면 부모가 페이드로 표시해 중간 화면 노출을 막는다. 동일 출처/iframe 발신자를 확인하며 reduced-motion을 지원한다.
  메인 진입 영역은 실제 레이아웃을820→1040px, 카드 최소 높이300→350px, 제목36→42px 등으로 확대했다. 축소/확대 zoom은 사용하지 않으며 메인 안내창 크기는 유지하고2·3단계 대상 좌표를 새 크기에 맞췄다.
- 바뀐 파일: frontend/components/{onboarding-tour,data-sources-screen,app-header,chat-screen}.tsx, frontend/lib/{data-sources,tours}.ts, frontend/app/(protected)/data-sources/, frontend/app/globals.css, frontend/scripts/check-data-sources.mjs, docs/implementation_objects.md, artifacts/help-hub/
- 확인 방법: lint/typecheck/format:check/Webpack, check-onboarding 및 check-data-sources(허용12개 실파일/분류/임의 경로 제외/고객·청구 건수) 통과. CUA 도움말60×60, 메뉴3개/닫기, 가이드라인의 원래 안내 열기/닫기, 청구 맥락 챗봇 이동, 메인 링크, 출처 필터5/7/2개·실제 약관 본문·390px 메뉴/페이지 넘침 없음 확인. 1280×720·729×800 각각62단계 카드 경계/대상 비중첩 통과. 어시스턴트 중앙 모달/꼬리 숨김, 답변 강조 높이265.34px 확인. 준비 완료 후 iframe opacity1·180ms 전환·160ms 배경 애니메이션, 안내 종료 후 원래 채팅 입력 보존 확인. 메인 실제 카드510×350/콘텐츠1040px/제목42px/zoom1 확인. artifacts/help-hub/에 캡처와 검사 JSON을 기록했다.
- 남은 문제 · 질문: 없음. 별도 유료 API/실제 문자 전송 없음. 출처 본문은 이 프로젝트가 사용한 보관본이며 최신 공시 자료를 자동 동기화하는 기능은 아니다.

## 2026-10-16 · T-19u · 메인 첫 안내의 원래 비율 복원
- 관련 요구사항: FR-04~05, SCR-02
- 한 일: 소개 문장을 ‘보상담당자의 청구업무를 돕는 가온 Ai입니다.’로 바꿨다. 첫 안내에만 적용했던 zoom 0.5/0.4/0.65와 고정 폭·좌측 정렬을 제거했다. 주요기능/도입 배경/데모 범위 문구는 유지한다.
  전체 서비스 소개는 원래 크기의 메인 화면 위 중앙 모달로 표시한다. 특정 영역을 가리키는 꼬리는 첫 안내에서 숨기며, 2·3단계의 좌우 안내는 유지한다. 긴 내용은 설명 영역에서 스크롤할 수 있다.
- 바뀐 파일: frontend/lib/tours.ts, frontend/components/guide-player.tsx, frontend/app/globals.css, artifacts/onboarding/v5/
- 확인 방법: lint/typecheck/Webpack 및 check-onboarding 검사. CUA 원래 메인/안내 배경 모두 overview 820×425.49, 두 카드 각각400×300, zoom1 동일 확인. 요청 문구 일치, 중앙 모달640×488.64가1280×720 안에 표시됨을 확인했다. 729×800에서도 zoom1/모달 경계 통과. artifacts/onboarding/v5/에 캡처와 비교 JSON을 저장했다.
- 남은 문제 · 질문: 없음. 실제 업무 데이터/API 변경 없음.

## 2026-10-16 · T-19t · 메인 소개 문구와 말풍선 좌우 위치
- 관련 요구사항: FR-04~05, SCR-02
- 한 일: 메인 첫 안내를 사용자가 제공한 소개 문장과 주요기능/도입 배경/데모 범위 3행으로 교체했다. 본문은 원문대로 보존했다. 긴 표를 읽을 수 있도록 첫 안내 폭을 늘리고 설명 영역 내부 스크롤을 지원하며, 메인 화면은 같은 컴포넌트의 축소 미리보기로 함께 보여준다.
  두 번째 안내는 어시스턴트 카드의 왼쪽, 세 번째는 워크스페이스 카드의 오른쪽 바깥 여백을 우선 사용한다. 데스크톱에서 공간이 모자라면 안내용 화면의 카드 위치를 옮겨 설명 공간을 확보한다. 좁은 화면은 화면 안에 들어오는 대체 배치를 사용한다.
- 바뀐 파일: frontend/lib/tours.ts, frontend/lib/guide/placement.ts, frontend/components/guide-player.tsx, frontend/app/globals.css, frontend/scripts/check-onboarding.mjs, artifacts/onboarding/v4/
- 확인 방법: lint/typecheck 및 Webpack 배포 빌드, check-onboarding 격리/빈 메모/안내 순서/좌우 우선 배치 검사 통과. CUA 1280×720·729×800에서 메인 1~3단계의 경계/대상 비중첩을 확인했다. 기본 화면 2단계는 대상 왼쪽(x17.5), 3단계는 대상 오른쪽(x787.5)이다. 첫 안내의 세 행을 원문과 대조했다. artifacts/onboarding/v4/에 캡처와 검사 JSON을 남겼다.
- 남은 문제 · 질문: 없음. 안내 전용 변경이며 실제 API 호출 없음.

## 2026-10-16 · T-19s · 챗봇 디자인 복원과 기능별 온보딩 설명
- 관련 요구사항: FR-04~05, FR-18~24, FR-28~35, SCR-02/03/10~14
- 한 일: 원본 챗봇의 한 줄 헤더와 + 새 채팅, 날짜별 대화 목록·실제 시작 시각·보라색 선택 배경을 복원했다. 실제 질문 수에 따른 위치 바로가기로 대화 안에서 이동한다. 임의 과거 대화는 넣지 않고 세션 메모리 정책을 유지한다.
  온보딩은 짧은 소개와 기능 이름/설명의 개별 행으로 구성하고 -요/-습니다 말투를 섞었다. 종료 안내는 한 줄을 유지한다. 청구 목록은 머리글과 실제 7행(좁은 화면은 2행)을 함께 강조한다. 안내 전용 담당자 메모를 비웠다. 문서 검토는 소개→상단 서류 현황→왼쪽 원본→오른쪽 추출 정보→항목·값→출처·신뢰도→하단 확인 사항→비교 기능 순서로62단계를 구성했다. 메인 첫 단계는 제목과 두 카드, 다음 단계는 각 카드 아래 좌/우 말풍선이다. 좁은 화면은 내부 스크롤과 안내 전용 여백으로 배치를 조정한다.
- 바뀐 파일: frontend/components/{app-header,brand,chat-screen,claim-screens,guide-player,home-screen,review-screen}.tsx, frontend/app/(protected)/{layout,chat/page,guide/[screen]/page}.tsx, frontend/app/globals.css, frontend/lib/{chat-history,tours}.ts, frontend/lib/guide/{placement.ts,snapshot.json}, frontend/scripts/check-{chat-history,onboarding}.mjs, docs/implementation_objects.md, artifacts/chat-design/, artifacts/onboarding/v3/
- 확인 방법: lint/typecheck/format:check/Webpack 배포 빌드 통과. 날짜 경계·실제 API 격리·기능별 설명/빈 메모/문서 안내 순서·타이핑 검사 통과. CUA 기본 챗봇/실제 시각/질문 표시, 1280×720·729×800 각각62단계에서 카드 경계/대상 비중첩 확인(수정된 2개 좁은 화면은 재검사 반영). 메인 좌우 하단 배치 및 빈 메모 확인. 캡처와 단계별 검사 JSON은 artifacts/onboarding/v3/에 기록한다.
- 남은 문제 · 질문: 없음. 실제 업무 메모/채팅은 변경하지 않는다. 유료 API 및 실제 문자 전송0회. 지난 대화는 현재 세션에서 생긴 실제 기록만 표시한다.

## 2026-10-16 · T-19r · 페이지별 독립 온보딩과 짧은 말풍선 안내
- 관련 요구사항: FR-04~05, FR-18~24, SCR-02/03/10~14
- 한 일: 메인→어시스턴트→워크스페이스 각 페이지 순서로7개 히든 안내 경로를 만들었다. 실제 화면 컴포넌트/CSS를 공유하고 고정 가상 데이터·원본·저장된 시연 답변을 독립 공급한다. 원래 페이지의 ?가 iframe을 열며 종료하면 원래 입력/채팅/서류 선택/배율로 돌아온다. 실제 API/업로드/인박스 복원 저장소 호출을 안내에서 차단한다.
  첫 초안의 긴 문구와 큰 강조 범위에 대한 사용자 피드백을 반영해60단계로 재구성했다. 최대67자 문구와 큰 볼드 제목, 아이콘, 원형 다음 버튼, 말풍선 꼬리를 사용한다. 머리글은 청구번호/고객·청구 유형/접수·상태/AI 검토 결과로 묶는다. 서류 목록/표 머리글/버튼 등 설명하는 작은 영역 전체를 강조하고, 공간이 없으면 대상부터 정렬해 카드와 겹치지 않게 한다. 마지막은 ‘궁금할 땐 언제든 ?를 눌러 주세요.’ 한 줄이다.
- 바뀐 파일: frontend/components/{onboarding-tour,guide-player,home-screen,workspace-shell,workspace-ui,claim-screens,chat-screen,review-screen,operations-screens}.tsx, frontend/lib/{tours,workspace}.ts, frontend/lib/guide/, frontend/public/guide-documents/, frontend/app/(protected)/guide/[screen]/page.tsx, frontend/app/globals.css, frontend/scripts/check-onboarding.mjs, docs/decisions.md, docs/implementation_objects.md, TODO.md, artifacts/onboarding/
- 확인 방법: pytest142 passed/1 live 제외, 프론트 lint/type/format 및 next build --webpack 통과. check-onboarding(실제 API 차단/정상 화면 유지/리소스 격리/7개 종료/4방향 배치)와 check-typing 통과. CUA 1280×720/729×800 각각60단계 대상 표시/전체 범위/카드 비중첩/화면 경계 검사 모두 통과. 7개 ? 연결·독립 종료, 채팅 입력/세션0개 보존, 입퇴원확인서120% 보존, 안내 전후 DB15테이블 동일 확인. 제목 Noto Sans KR/700 확인. 최종 캡처와 검사 JSON은 artifacts/onboarding/v2/, 첫 초안은 v1/에 보존했다.
- 남은 문제 · 질문: 없음. 실제 업무 데이터 대신 가상 예시를 사용하는 안내다. 중간 DB 비교에는 동시 청구/채팅 조회 로그2건이 섞였으나 안내 전용 전체 재검증에서는15테이블 동일했다. 별도 LLM/Upstage 호출0회, 실제 문자 발송 없음. 운영 관리 안내는 이번 범위 밖이다.

## 2026-10-16 · T-19q · 추출된 서류 정보 탭과 원본별 확대·이동
- 관련 요구사항: FR-19~24, SCR-12~13
- 한 일: ‘정규화 결과’를 ‘추출된 서류 정보’로 바꾸고 두 표를 나란히 두는 대신 문서별 탭/비교 항목 탭에서 한 표씩 보여준다. 비교 항목은 해당 이슈 필드만 기본 표시하며 탭 전환 시 첫 행부터 연다. 신뢰도는 실제 숫자를99.8%처럼 표시하고 줄바꿈을 방지한다.
  비교 원본마다 독립 확대/축소/맞춤을 제공하고 드래그·방향키로 이동한다. 자동 확대는 하지 않는다. 보완 화면은 드롭다운을 제거하고 왼쪽에 검색 고객/청구번호/누락 서류/총개수/문자 생성, 오른쪽에 실제 발송·접수 이력과 축소한 편집기를 둔다. 생성 응답을 즉시 바인딩해 빈 편집기 문제를 해소했다.
- 바뀐 파일: frontend/components/review-screen.tsx, frontend/components/operations-screens.tsx, frontend/app/globals.css, frontend/lib/tours.ts
- 확인 방법: lint/typecheck/format:check 및 next build --webpack 통과. CUA 진단서7개/조직검사6개/비교2개 필드, 실제99.8%/98.4%, 왼쪽120%·오른쪽100%, 드래그 왼쪽scrollLeft42→0·오른쪽0유지 확인. 고정 문자 생성 후 실제 고객·상품·접수일·누락1개와 편집기 본문 반영 확인. artifacts/final-workflow/{document-tabs,comparison-fields,supplement}.png와 supplement-letter.txt.
- 남은 문제 · 질문: SMS 회신 기능 자체는 없으며 이력은 실제 감사 로그에 있는 모의 발송/보완 서류 접수만 표시한다. 검증 중 모의 발송은 실행하지 않았다. 유료 API 호출0회.

## 2026-10-16 · T-19p · 고정 안내 문자 양식과 실제 추출 점수 복원
- 관련 요구사항: FR-19~24, SCR-12~13
- 한 일: 최신 요청에 따라 보완 문자 생성은 챗봇 어댑터 대신 data/templates/supplement_messages.json의 서류별 고정 양식으로 변경했다. 권한 범위와 실제 누락을 확인하고 고객명·청구번호·상품·접수일·서류별 준비처를 채운다. 미발송 초안만 재생성하고 발송된 기록은 보호한다. 실제 감사 로그의 발송·접수 시각을 API에 추가했다.
  T-19n 기록의 ‘API는 high/low만 제공’ 설명을 정정한다. 저장된 extract.choices[0].confidence_score는 JSON 문자열이며 각 필드의 _value 숫자를 제공했다. 중첩 품목도 읽어 API에 confidence_score를 노출하고 _ctx/Classify 점수는 사용하지 않는다. 실손24 데이터는 해당 없음으로 유지한다.
- 바뀐 파일: backend/app/services/supplement.py, backend/app/services/workspace.py, backend/app/routers/supplements.py, backend/app/config.py, .env.example, data/templates/supplement_messages.json, backend/tests/test_operations_api.py, backend/tests/test_confidence_display.py
- 확인 방법: 전체 pytest142 passed/1 live 제외, Ruff check/format 통과. 양식 전체 코드·변수 치환·외부 HTTP 금지·같은 초안 재생성·발송 보호·추출 점수 JSON/중첩/잘못된 값/실손24를 테스트했다. 실제 UI 생성 본문은 artifacts/final-workflow/supplement-letter.txt.
- 남은 문제 · 질문: 없음. Upstage 추가 호출0회. 과거 WORKLOG는 당시 기록으로 보존하며 숫자 미제공 판단은 이 기록으로 정정한다.

## 2026-10-16 · T-19o · 비교 문서별 정규화 표 분리
- 관련 요구사항: FR-19~20, SCR-12
- 한 일: 두 원본 비교 시 정규화 결과도 같은 순서의 문서별 표로 분리했다. 문서명/항목 수를 각각 표시하고 각 표의 세로·가로 스크롤을 독립시켰다. 문서/이슈가 바뀌면 표를 첫 행부터 연다. 단일 원본에서는 한 표를 유지하며 필드 수정·출처·신뢰도 표시도 그대로 사용한다.
- 바뀐 파일: frontend/components/review-screen.tsx, frontend/app/globals.css
- 확인 방법: npm run lint/typecheck/format:check, next build --webpack 통과. CUA issue5: 원본 순서와 표 순서 동일, 입퇴원확인서7행/세부내역서58행 및 네 열 확인. 오른쪽만 스크롤 후 위치[0,720], 진단서 선택 시 표1개 확인. artifacts/ui-cleanup/normalized-split.jpg. 백엔드·API/평가 변경 없음.
- 남은 문제 · 질문: 없음. 좁은 칸에서는 표를 가로로 스크롤해 네 열을 확인한다. 외부 호출 없음.

## 2026-10-16 · T-19n · 숫자 미제공 신뢰도 등급 표시 복원
- 관련 요구사항: FR-19~20, SCR-12
- 한 일: 숫자 점수가 없는 실제 high/low 정보까지 대시로 가리던 표시를 고쳤다. 숫자 점수는 %로, 숫자가 없으면 원래 높음/낮음 등급으로 표시한다. 실손24 정형 데이터와 신뢰도 자체가 없는 경우만 대시다. 확인 이유는 신뢰도 셀 툴팁으로 유지한다.
- 바뀐 파일: frontend/lib/workspace.ts, frontend/components/review-screen.tsx, frontend/lib/tours.ts
- 확인 방법: npm run lint/typecheck/format:check, next build --webpack 통과. CUA 진단서7개 항목 높음 표시, 실손24 영수증10개 항목 대시 확인. artifacts/ui-cleanup/confidence.jpg. 별도 추출/유료 API 호출 없음.
- 남은 문제 · 질문: 현재 API는 high/low만 제공하며 임의의 숫자 확률은 만들지 않는다.

## 2026-10-16 · T-19m · 비교 안내 높이와 긴 품목명 레이아웃 보정
- 관련 요구사항: FR-19~20, SCR-12
- 한 일: 긴 품목명이 18px 큰 글자와 flex 축소로 여러 줄로 꺾이던 안내를 14px 한 줄/말줄임/전체값 툴팁으로 바꿨다. 비교 시 양쪽 안내 칸을46px, 문서 제목 칸을52px로 맞춰 원본 시작 높이가 다르지 않게 했다.
  실제 대응 추출 항목이 없는 쪽은 그 사실을 표시하고 원문에 없는 값을 만들거나 강조하지 않는다. 이미지 비율과 확대율은 변경하지 않았다.
- 바뀐 파일: frontend/components/review-screen.tsx, frontend/app/globals.css
- 확인 방법: lint/type 및 Webpack 통과. CUA 처방전/약제비 영수증 비교에서 양쪽 안내46px/글자14px/뷰어 top482.4921875px 동일 확인. artifacts/supplement-scope/comparison-aligned.jpg. 외부 호출 없음.
- 남은 문제 · 질문: 없음.

## 2026-10-16 · T-19l · 보완 고객 범위 고정과 챗봇 공통 안내 생성
- 관련 요구사항: FR-21~24, SCR-13
- 한 일: 보완 목록 API에 claim_id 필터와 해당 청구 권한 검사를 추가했다. 화면도 선택 고객 기준으로 목록/편집기를 제한하고 고객 전환 즉시 이전 선택과 안내를 비운다.
  버튼을 안내 문자 생성으로 바꾸고 바로 아래 실제 누락 서류를 표시했다. 누락이 없는 한누리 건은 누락 없음/생성 비활성화로 안내하며 김유정의 요청을 보여주지 않는다.
  별도 Solar 재작성·구형 문구 캐시 경로를 제거하고 챗봇 Tools.draft_supplement를 그대로 사용한다. 로컬 표준 문구만 읽으며 LLM/벡터 검색을 호출하지 않는다. 명시적으로 재생성하면 같은 미발송 초안도 새 문구로 갱신한다. 발송된 요청은 보호하고 모의 발송만 유지한다.
- 바뀐 파일: backend/app/services/supplement.py, backend/app/routers/supplements.py, backend/tests/test_operations_api.py, frontend/components/operations-screens.tsx
- 확인 방법: 전체 pytest138 passed/1 live 제외, 관련 회귀23개, Ruff check/format 통과. 프론트 lint/type/format 및 Webpack 통과. CUA 한누리→김유정 생성→한누리 전환: 요청 카드0/편집기0/생성 비활성화, 김유정 실제 누락 수술확인서/표준 문자 반영 확인. artifacts/supplement-scope/{han-nuri,kim-draft}.jpg. 도구 결과 문구 동일성·구형 초안 재생성·고객 범위/권한을 테스트로 고정했다.
- 남은 문제 · 질문: 없음. 실제 전송/Upstage 추가 호출0회. 기존 미발송 김유정 초안은 UI의 생성 동작으로 공통 문구로 갱신했다. 과거 발송 문구는 변경하지 않는다.

## 2026-10-16 · T-19k · 검토 결과를 목업의 세 줄 요약으로 간소화
- 관련 요구사항: FR-18~20, SCR-11
- 한 일: 3단계의 긴 정규화 표·품목 표·이슈 목록을 없애고 왼쪽 검토 결과 세 줄/오른쪽 담당자 메모의 목업 구성으로 바꿨다. 자세한 값 수정과 이슈 확인은 기존 문서 분석·검토 화면에서 유지한다.
  확인 필요는 같은 원인을 병합한 실제 표시 이슈로 계산한다. 누락 서류명과 약관 대조도 실제 결과에서 계산하며, 분석 전에는 대기 문구를 쓴다. 김유정은 확인2/누락 수술확인서1/보상 제외 가능성1로 표시한다.
  완료 단계 버튼을 보완 요청 보내기 (실제 누락 서류명)으로 바꾸고 보완 화면으로 연결했다. 명시적인 상세 issue 링크는 문서 검토의 같은 이슈로 연결해 기존 챗봇 이슈 이동을 유지한다. 온보딩도 요약 구성에 맞췄다.
- 바뀐 파일: frontend/components/claim-screens.tsx, frontend/app/globals.css, frontend/lib/tours.ts, frontend/app/(protected)/workspace/[section]/page.tsx
- 확인 방법: npm run lint/typecheck/format:check, next build --webpack 통과. CUA 요약 세 줄 실제 수치, 약관 요약→issue6, 보완 버튼 문구와 경로, 상세 issue3→문서 검토 issue3 확인. artifacts/ui-cleanup/{review-summary,supplement-action}.jpg. UI 변경으로 백엔드/평가 재실행 없음.
- 남은 문제 · 질문: 없음. 외부 Upstage 호출 없음. 가상 목업의 고정값(제외 항목 없음 등)은 사용하지 않았다.

## 2026-10-16 · T-19j · 상세 첫 단계 진입과 중복 복귀 링크 제거
- 관련 요구사항: FR-18~20, SCR-11
- 한 일: 상세의 일반 진입 위치를 DB의 저장 step과 분리해 항상 서류 확인(1단계)으로 연다. 청구/이슈 경로가 달라지면 컴포넌트를 재생성해 이전 로컬 탭도 남지 않는다. 명시적인 issue 링크는 해당 확인 항목을 보여주는 기존 동작을 유지한다.
  본문의 ← 청구 검토함 링크와 그 링크용 복귀 URL 상태를 제거했다. 왼쪽 청구 검토함 메뉴와 검토함 자체의 필터/스크롤 복원은 유지했다.
- 바뀐 파일: frontend/components/claim-screens.tsx, frontend/app/(protected)/workspace/[section]/page.tsx
- 확인 방법: npm run lint/typecheck/format:check, next build --webpack 통과. CUA에서3단계를 선택한 뒤 새로고침→현재1 서류 확인, 본문 복귀 링크0개/왼쪽 메뉴1개 확인. artifacts/ui-cleanup/detail-start.jpg. 저영향 UI 변경으로 별도 자동 테스트 추가 없음.
- 남은 문제 · 질문: 없음. 외부 Upstage 호출 없음.

## 2026-10-16 · T-19i · 정보 대조 화면 HTML 목업 스타일 복원
- 관련 요구사항: FR-18~20, SCR-11
- 한 일: gaon-ai.html처럼 단계 완료 체크 원/현재 단계 테두리 원과 3개의 진행 연결선을 표시했다. 정보 대조 표는 여백 없는 카드/연보라 머리글/일관된 셀 여백으로 정리하고 서류명과 값을 같은 줄에서 읽도록 바꿨다.
  불일치는 주황 경고 아이콘으로 표시하고 하단 원본 확인 링크를 추가했다. 실제 비교 16건, 1일 차이 안내 판정, 값 클릭 원본 모달 기능은 유지했다.
- 바뀐 파일: frontend/components/claim-screens.tsx, frontend/app/globals.css
- 확인 방법: npm run lint/typecheck/format:check, next build --webpack 통과. CUA 정보 대조 단계 선택 후 완료1개/연결선3개/현재 단계2/네 열/실제16행 확인. artifacts/ui-cleanup/comparison-style.jpg. 가벼운 디자인 변경으로 별도 자동 테스트 추가 없음.
- 남은 문제 · 질문: 없음. 외부 Upstage 호출 및 백엔드 변경 없음.

## 2026-10-16 · T-19h · 중복 어시스턴트 진입 버튼 제거
- 관련 요구사항: SCR-11, FR-18~20
- 한 일: 청구 상세 본문의 업무 어시스턴트에게 묻기 버튼을 제거하고 공통 우하단 가온 AI에게 묻기만 유지했다.
- 바뀐 파일: frontend/components/claim-screens.tsx
- 확인 방법: npm run lint/typecheck, next build --webpack 통과. CUA 본문 링크0개, 공통 링크 /chat?claim=GA-2610-0482 유지 확인. artifacts/ui-cleanup/chat-entry.jpg. UI 한 요소 제거이므로 별도 자동 테스트 추가 없음.
- 남은 문제 · 질문: 없음. 외부 API 호출 없음.

## 2026-10-16 · T-19g · 원본 높이 정렬과 안내별 서류 이동
- 관련 요구사항: FR-18~20, SCR-12
- 한 일: 오른쪽 두 카드가 정한 높이를 왼쪽 원본 뷰어가 채우도록 레이아웃을 바꿨다. 이미지 종횡비와 확대율은 그대로 유지하며 좁은 화면에서는 기존처럼 세로로 배치한다.
  안내 제목/본문을 키보드 접근 가능한 버튼으로 바꿨다. 실제 doc_ids와 field_keys로 단일 원본 또는 두 서류 비교를 열고 좌표가 있으면 해당 위치로 이동·강조한다. 기존 원본 비교 버튼도 같은 동작을 사용한다. 확인 기록 버튼과 서류 이동은 분리했고, 누락 항목은 원본 대신 보완 화면으로 연결한다.
- 바뀐 파일: frontend/components/review-screen.tsx, frontend/app/globals.css
- 확인 방법: lint/type/format 및 next build --webpack 통과. CUA 1280px 화면에서 원본 bottom=1195.1875, 안내 bottom=1195.1875로 차이0px. 수동120% 뒤 진단일 안내→진단서/조직검사 결과지·각 날짜 위치, 코드 안내→진단서·C18 위치, 누락→보완 처리 경로 확인. 확대율120% 유지. artifacts/search-first/{review-height,issue-open-comparison}.jpg.
- 남은 문제 · 질문: 없음. 외부 Upstage 호출 없음. 백엔드/평가/안전 규칙 변경 없음.

## 2026-10-16 · T-19f · 개별 업무 화면을 검색 후 선택으로 시작
- 관련 요구사항: FR-05, FR-18~20
- 한 일: 청구 상세/문서 분석/보완 처리/검토 이력은 청구 ID 없이 들어오면 고객 목록을 조회하지 않고 안내만 보여준다. 검색어를 제출한 뒤에만 결과를 조회한다.
  상단 검색이 현재 업무 경로를 유지하도록 바꿔 검색 결과 선택 시 해당 업무의 청구 화면으로 연결한다. 기존 검토함에서 청구를 선택하거나 청구 ID로 직접 이동하는 흐름은 유지한다.
- 바뀐 파일: frontend/components/{claim-screens,workspace-shell}.tsx, frontend/app/(protected)/workspace/[section]/page.tsx
- 확인 방법: lint/type/format 및 next build --webpack 통과. CUA로 4개 경로 모두 초기 고객 링크 0개, C001 검색 후 결과 1개와 동일 업무 경로의 claim 링크를 확인하고 클릭했다. artifacts/search-first/{detail,review,supplement,history}-empty.jpg 및 checks.json. 백엔드 변경 없음(직전 전체137개 통과).
- 남은 문제 · 질문: 없음. 실제 Upstage 호출 없음.

## 2026-10-16 · T-19e · 원본 검색창과 고객 ID 검색
- 관련 요구사항: FR-05 (사용자 변경 지시)
- 한 일: 원본 HTML의 배경·620px 독립 검색 상자·44px 높이·12px 모서리·돋보기 구성을 복원했다. 검색 안내와 실제 API 검색 대상을 고객 이름/고객 ID/청구번호로 통일하고 증권번호·생년월일 검색을 제거했다. 담당자 배정 권한 범위는 유지했다.
  메인과 챗봇 디자인은 유지했다. 우하단 도움말과 업무 버튼이 겹치지 않도록 업무 버튼의 오른쪽 여백을 확보했다.
- 바뀐 파일: backend/app/routers/claims.py, backend/tests/test_demo_polish.py, frontend/components/workspace-shell.tsx, frontend/app/globals.css
- 확인 방법: 전체 pytest137 passed/1 live 제외, 검색 포함 회귀18개 통과, Ruff·lint·typecheck·format 및 Webpack 빌드 통과. 실제 UI에서 C001 검색→김유정 GA-2610-0482 한 건을 확인했다. artifacts/ui-restore/search-customer-id.jpg. 외부 호출 없음.
- 남은 문제 · 질문: 없음. 기존 FR-05 문서의 증권번호 검색 명세보다 최신 사용자 요청을 우선했다.

## 2026-10-16 · T-19d · 고객별 업무 목록 예시 질문 연결
- 관련 요구사항: FR-22~24, SCR-20
- 한 일: 입원일수 예시 질문을 현재 조회 가능한 고객의 업무 목록 질문으로 교체했다. 청구 상세에서 진입하면 선택 고객을 사용하고 일반 화면에서는 담당자에게 배정된 첫 청구의 이름과 ID를 사용한다. 고객명과 답변은 하드코딩하지 않는다.
  권한 검증된 claim_id 맥락에서 해야 할 업무 목록은 기존 claim_check 도구/검토 답변으로 연결했다. 지급 판단 선행 가드는 그대로 유지했다. 챗봇의 레이아웃과 스타일은 변경하지 않았다.
- 바뀐 파일: frontend/components/chat-screen.tsx, backend/app/agent/graph.py, backend/tests/test_demo_polish.py
- 확인 방법: pytest136/live1 제외 및 Ruff, 프론트 lint/type/format, Webpack 빌드 통과. 실제 /api/chat을 UI에서 캐시 전용 모드로 실행해 수술확인서·세분류·진단/병리일·종합비타민정·입원일수 안내 및 보완 요청 버튼을 확인했다. 결과 artifacts/ui-restore/task-list-answer.{txt,jpg}. 외부 Upstage 호출 0회, 추가 추정 비용 $0.
- 남은 문제 · 질문: 없음. 홀드아웃/평가 기준/안전 가드 수정 없음.

## 2026-10-16 · T-19c · 원본 카드·표 복원과 수동 온보딩
- 관련 요구사항: FR-18~20, SCR-02, SCR-11, SCR-12
- 한 일: 문서 검토의 합쳐진 결과 영역을 정규화 표(위)와 확인 안내 카드(아래)로 분리하고 원본 gaon-ai.html의 테두리·간격·표 톤을 복원했다. 청구 상세도 동일한 네 열(항목/값/출처/신뢰도)로 정리했다.
  메인·챗봇 디자인은 유지하고 메인 현황 한 줄만 제거했다. 자동 온보딩을 없애고 기존 우하단 물음표를 수동 투어로 통일했다. 메인·검토함·챗봇에서 자동 대화상자 0개/버튼 클릭 후 열림을 확인했고, 문서 검토에도 안내를 추가했다.
  숫자 confidence가 없는 high/low를 임의 확률로 만들지 않는다. 숫자 점수가 제공되면 0~1은 백분율(0.7=70%), 1 초과~100은 점수 그대로 %로 표시하며 미제공/실손24는 —다.
- 바뀐 파일: frontend/components/{claim-screens,review-screen,onboarding-tour,workspace-shell}.tsx, frontend/lib/{workspace,tours}.ts, frontend/app/globals.css, frontend/app/(protected)/page.tsx
- 확인 방법: pytest 136 passed/1 live 제외, Ruff 통과. npm run lint/typecheck/format:check, next build --webpack 통과. CUA Playwright에서 실제 네 열·카드 순서·도움말 확인. 캡처 artifacts/ui-restore/{review,detail,home,tour-home,tour-workspace,tour-chat}.jpg.
- 남은 문제 · 질문: 현재 추출 API는 숫자 confidence가 아닌 high/low만 제공하므로 실제 점수 칸은 —로 표시한다. 평가셋·안전 규칙·KB 원문은 수정하지 않았다.

## 2026-10-16 · T-19b · 전체 UX 검수 반영
- 관련 요구사항: FR-20~35, NFR-08
- 한 일: 수정 전 UX 보고서에13건을 기록하고 명확한11건을 수정했다. 내부 항목명·날짜·41px 필드표·56px 인박스·툴팁·원본 창 키보드·초안 조사/타이핑·발송 피드백·공유 이슈/이력 표시를 보완했다. 큰 구조 제안2건은 미적용으로 남겼다.
  대조는 엔진과 같은 접수 환자명/진료 기간 양 끝/활성 규칙을 사용한다. 명확한 청구 지시어만 도구에 연결하고 나머지는 기존 모델 분류/거절 판단을 유지한다. 알려지지 않은 서류는 누락 서류로 바꾸지 않고 템플릿 목록만 안내한다. 코드와 실제 추출 좌표를 보존하며 화면에서만 가독성을 바꾼다.
- 바뀐 파일: backend/app/agent/{graph,claim_answer}.py, services/{workspace,claim_status,presentation}.py, config.py, tests/test_demo_polish.py, frontend/components/{claim-screens,chat-screen,review-screen,operations-screens,onboarding-tour}.tsx, lib/workspace.ts, scripts/check-typing.mjs, globals.css, AGENTS.md/.env.example, docs/{implementation_objects,decisions,06_eval_plan,WORKLOG}.md, TODO.md, artifacts/demo/
- 확인 방법: pytest135 passed/live1 제외, Ruff 검사/포맷, 프론트 lint/type/format, next build --webpack 통과. 실제 훅 가상 시계로50자/초·건너뛰기·reduced-motion 검증. CUA로 로그인~관리자, 네 맥락 질문/복사/지급 거절, 빈 상태/오류/모의 발송/이관 상태, 필터/페이지/스크롤172.5복원,1440/1920와 투어 확인. PNG39장 경로는 artifacts/demo/README.md.
- 남은 문제 · 질문: 대조 항목별 접기와 문서별 필드 접기는 사용자 결정 제안으로 남겼다. OS 모션 설정과 저장 차단 브라우저는 직접 변경하지 않았고 해당 분기는 코드/가상 시계/예외 처리로 검증했다. 검수 상태는13청구/29서류·요청0·단계0으로 복구, 김유정7/8 보완 요청이다. Upstage 외부0회/문서0페이지, 추가 추정$0. 정상 실행 모드로 복귀했다. 홀드아웃/평가/안전 가드/KB/기존 T18 산출물은 불변.

## 2026-10-16 · T-19a · 시연 전 화면·기능 보완
- 관련 요구사항: FR-20~35, NFR-08
- 한 일: ui-v2-before-demo 태그와 feat/demo-polish 브랜치를 만들었다. 상태를 실제 누락 기준의 공통 함수로 통일하고 누락 확인만으로 자동 통과하는 오류를 막았다. 실제 값 대조 표/원본 위치, 공유 확인 사항, 밀도 높은 표/인박스 10건 페이징, 고객 맥락 질문/분리 초안/타이핑, 화면별 코치마크를 추가했다.
- 바뀐 파일: backend/app/services/{claim_status,workspace,rules}.py, routers/{claims,review}.py, agent/{tools,graph,claim_answer,display}.py, models/config/schemas, frontend/components·lib/tours.ts·lib/use-typing.ts·globals.css, tests/test_demo_polish.py, .env.example, artifacts/demo/
- 확인 방법: pytest129 passed/live1 제외, Ruff/프론트 lint/type/next build --webpack 통과. seed --demo로 13청구/29서류 복구, 복구 전 상태 증거를 로컬 캐시에 보존했다. CUA로 메인/검토함/상세/어시스턴트 1차 확인과 캡처. UX 보고서를 수정 전에 작성했다.
- 남은 문제 · 질문: artifacts/demo/ux_review.md의 중간 7건을 T-19b에서 수정하고 관리자/오류/되돌아가기까지 전체 검수한다. 구조 제안2건은 적용하지 않는다. 홀드아웃/평가 기준/안전 가드는 변경하지 않았다.

## 2026-10-16 · T-18 · 답변 본문 목록을 실제 글머리표로 표시
- 관련 요구사항: FR-28~35
- 한 일: 답변 표시에서 연속된 `- ` 줄을 ul/li로 묶고 disc 글머리표를 적용했다. 일반 문단·번호 제목·조항 강조와 API 원문은 그대로 보존했다.
- 바뀐 파일: frontend/components/chat-screen.tsx, frontend/app/globals.css, docs/{WORKLOG,06_eval_plan}.md, artifacts/t18/ui-bullets/
- 확인 방법: 프론트 lint/type/포맷·next build --webpack 통과. CUA Playwright로 지급 거절 답변의 UL/LI3개와 list-style-type=disc 확인, bullet_list.jpg 캡처. 외부 Upstage 추가 호출0회.
- 남은 문제 · 질문: 없음.

## 2026-10-16 · T-18 · 시연 근거 패널·이슈 링크·거절 목록 마무리
- 관련 요구사항: FR-28~35, NFR-08
- 한 일: 본문 인용 순서의 display_citations와 실제 언급 이슈만 담는 display_claim_refs를 별도 조립했다. 평가용 citations/claim_refs/KB는 보존하며 패널은 원문, 답변 카드는 문서명과 조항 요약만 표시한다. 매뉴얼 표는 머리글:값 줄, 내부 규칙 코드는 담당자용 이름으로 화면에서만 바꾼다.
  청구 맥락의 지급 거절은 남은 항목 목록과 필수 이관 안내로 고정했다. 실제 원문 서류명, 중복 괄호 제거, 조항 표기 통일과 보장종목 구분을 반영했다. 보라색 질문 바로가기 막대를 제거했다. 사용자 추가 지시에 따라 demo_reset/초기화 버튼은 만들지 않고 새로고침/재로그인 초기화만 검증했다.
- 바뀐 파일: backend/app/agent/{display,graph,claim_answer}.py, backend/app/{config.py,schemas/chat.py}, backend/tests/test_chat.py, frontend/components/chat-screen.tsx, frontend/app/globals.css, docs/{06_eval_plan,implementation_objects,WORKLOG}.md, TODO.md, artifacts/t18/ui-final/
- 확인 방법: pytest119 passed/live1 제외, Ruff/포맷, 프론트 lint/type/format, next build --webpack 통과. CUA Playwright 시연4질문/첫 질문 최종 근거 재확인, 이슈6 상세 이동, 새로고침/재로그인 빈 목록 확인. 캡처6장은 artifacts/t18/ui-final/. 외부 Upstage 호출0, 응답 캐시9회, 추가 추정$0.
- 남은 문제 · 질문: 없음(요청 범위). demo_reset은 다음 P4에서 구현 예정. 기존 DB의 옛 이슈 근거는 수정하지 않고 현재 KB와 본문의 명확한 보장종목으로 화면만 연결한다. 평가/홀드아웃은 재실행하지 않았으며 새 성능 수치를 주장하지 않는다. 진단서 C18과 비교되는 C18.7의 실제 원문 출처는 입퇴원확인서다.

## 2026-10-16 · T-18 · 시연 답변 형식과 문단 표시 마무리
- 관련 요구사항: FR-28~35, NFR-08
- 한 일: 청구 검토 합쇼체·실데이터 기반 결론/누락/번호 항목/제안, 코드 원인 병합과 우선순위, 안내 명시를 구현했다. 다른 의도는 기본 용어를 살리고 내부 용어·문장 중간의 명사형 종결을 검사한다. 지급/개인정보 거절은 직접 근거1개와 대안/남은 항목을 제시한다. 기본 비활성의 가상 평가 응답 캐시와 호출/토큰 장부를 추가했다. React 안전한 문단·굵은 제목·연한 근거를 적용했다.
- 바뀐 파일: backend/app/agent/{claim_answer,graph,tone,solar}.py, config.py, scripts/{eval_presentation,report_solar_usage}.py, tests/{test_chat,test_tone}.py, .env.example, frontend/components/chat-screen.tsx, frontend/app/globals.css, artifacts/t18/presentation/와시연PNG/원문, docs/{06_eval_plan,decisions,implementation_objects,WORKLOG}.md, docs/deliverables/테스트결과보고서.md, TODO.md
- 확인 방법: pytest113 passed/live1 제외·Ruff/포맷·프론트 lint/type·Webpack 빌드 통과. 관련21문항 동일 rubric 각1회: 거절100/요지100 유지, 잔존 패턴0/21. CUA Playwright로 시연4개 실제실행·4장+하단/초안 추가 캡처, DOM8문단/제목5개/10px/근거 색 확인. HTTP48(성공47·중단1), 로컬 캐시18, 정가 추정$0.011188. 추가 문서API0페이지. 홀드아웃 미사용.
- 남은 문제 · 질문: 엄격 인용86.36→81.82%로 무하락 목표는 미달이다. 새 매뉴얼9장 필수 인용과 Q29 빈 정답의 충돌, 지급 근거2→1개 제한 영향을 그대로 공개했다. Q08/Q26은 기존 실행의 생성 변동을 기록만 했다. 요지 단회는 비용 절약 선택이며 과거3회 점수와 혼동하지 않는다. 중단1회 비용은 평균 추정, 실제 콘솔 차감액 미확인. 긴 답변은 화면 스크롤이 필요하며 하단 추가 캡처를 남겼다.

## 2026-10-16 · T-18 · 자연스러운 해요체와 말투 회귀 검증
- 관련 요구사항: FR-28~35, NFR-08
- 한 일: 사실/근거 확정 뒤 본문만 문장화하는 tone 노드, 독립 예시3쌍, 패턴 검사/1회 재생성/잔존 유형 로그를 추가했다. 숫자 소실·새 지급 확정은 되돌리고 인용·의도·거절·버튼은 보존한다. Solar1~5점 문체 평가와 개발30/시연4의 전후 원문, 같은 실행 초안의 대응 채점도 보존했다. 정답/요지 rubric/검색/안전 가드는 변경하지 않았고 홀드아웃은 재실행하지 않았다.
- 바뀐 파일: backend/app/agent/{graph,tone}.py, scripts/{eval_chat,eval_tone,eval_tone_pair,tone_grade,chat_smoke}.py, tests/{test_chat,test_tone}.py, data/eval/CHANGELOG.md, docs/{implementation_objects,decisions,06_eval_plan,WORKLOG}.md, docs/deliverables/테스트결과보고서.md, TODO.md, artifacts/t18/tone_before_after.md와runs/2026-10-16/tone/
- 확인 방법: pytest108 passed/live1 제외·Ruff/포맷 통과. 최종 개발30: 의도100/엄격 인용89.47/거절100/요지100%, 금지표현0/호출오류0. 이전 답변 말투3.87→4.07/5, 같은 실행 초안3.90→4.07·패턴60→80%·요지96.67→100·인용/거절 동일. 시연12검사 통과. 백엔드 재시작/health ok.
- 남은 문제 · 질문: 이전 별도 실행 엄격 인용92.11→89.47%로 무하락 목표는 미달이다. 같은 실행에서는 인용을 바꾸지 않으며 Q08 인용 수 감소/Q26 정의 조문 추가를 분리 공개했다. 문체 패턴6/30과 시연P1의7문장 잔존은1회 재생성 후 로그만 남겼다. 자연어 의미 보존은 수치 가드만으로 증명할 수 없고 Solar 점수도 변동하므로 완전한 품질 보장을 주장하지 않는다.

## 2026-10-16 · T-18 · 홀드아웃1회·회귀 감사·ADR 최종 결과
- 관련 요구사항: FR-28~35, NFR-08, T-18c
- 한 일: 동결8da75c9 이후 홀드아웃16문항을1회 실행하고 답변당3회 채점 다수결을 기록했다. 원점수·실패 원문·10%p 격차를 보존했고 홀드아웃 결과로 코드/rubric/정답/허용 근거를 바꾸지 않았다. 호 인용 계산기의 doc_name 단위 분모 문제는 재호출 없는 별도 감사로 공개했다. H01은 이 집계 범위 문제만 있고 기본 지표를 통과한다.
  ADR-01에 실제 옛 조각 실패, 계층/준용/하이브리드 결정과2×2·개발/홀드아웃·한계를 남겼다. T18b 보고서를 별도 보존하고 최종 보고서와 평가 계획을 추가 갱신했다.
- 바뀐 파일: artifacts/t18/holdout/, artifacts/t18/runs/2026-10-16/t18c/{holdout,holdout_failures,dev_holdout_comparison,fine_scope_audit,freeze_audit}, docs/{decisions,06_eval_plan,WORKLOG}.md, docs/deliverables/테스트결과보고서*.md, TODO.md
- 확인 방법: 개발100/93.75/92.11/100/96.67%, 홀드아웃93.75/75/78.95/100/87.50%(의도/recall/엄격 인용/거절/요지). 런타임·정답 해시 불변, completed 1회. pytest94 passed/live1 제외·Ruff/포맷·프론트 lint/type/format, next build --webpack 성공. 필수4+영양제5답변/실제 카드 표시 확인.
- 남은 문제 · 질문: 홀드아웃 검색·엄격 인용 격차는 과적합 가능성이다. H08 고객명 정규식 오인, H15/H16 거절 근거/세부 설명 누락을 수정하지 않고 공개했다. 호 인용 원점수72.73%와 주소 범위 검산8/8을 병기하며 주 지표78.95%는 그대로다. 실제 약관/큰 독립 평가·사람 채점과 새 홀드아웃이 필요하다. seed의 서버 적용 보장은 미확인. File Search 선택 비교 미실행.

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
