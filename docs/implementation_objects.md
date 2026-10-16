# 구현 객체 안내 — T-01~T-11

설계 원본을 변경하지 않고, 현재 코드에서 각 객체가 맡는 역할과 선택 이유를 정리한다.

## 백엔드

| 객체 | 위치 | 역할과 이유 |
|---|---|---|
| Settings | backend/app/config.py | 환경변수·경로·기본값을 모은다. 실행 폴더가 달라도 같은 프로젝트 DB를 바라보도록 절대 경로를 사용한다. 비밀값은 SecretStr로 표시를 감춘다. |
| create_app | backend/app/main.py | 설정을 주입받는 앱 팩토리. 테스트용 DB를 운영·데모 DB와 분리하고, lifespan에서 엔진을 열고 닫는다. |
| get_session | backend/app/db.py | 요청마다 SQLModel 세션을 만들고 정리한다. 전역 세션을 공유해 요청끼리 간섭하는 일을 피한다. |
| User / Role | backend/app/models.py | 데모 계정과 담당자·관리자 역할. 쿠키에는 역할을 넣지 않고 매 요청 DB의 최신 역할을 확인한다. |
| Claim | backend/app/models.py | 청구 단위 집계 루트. 제출 문서·이슈·보완 요청·이력은 청구에 연결한다. |
| Document | backend/app/models.py | 문서 유형·원본 경로·추출 원본 결과. Classify·Parse·Extract 원본과 정규화값을 보존한다. 캐시 원본은 Git 제외 경로에 둔다. |
| ExtractedField | backend/app/models.py | 문서에서 추출한 값과 원본 근거·확정값을 분리해 보관한다. 원래 추출 결과를 담당자 수정값으로 덮어쓰지 않기 위해서다. |
| Issue | backend/app/models.py | 누락·불일치·확인 필요 항목과 근거·처리 상태. services/rules.py가 필수서류·교차검증·검토 라우팅을 실행한다. |
| SupplementRequest | backend/app/models.py | 보완 서류와 모의 발송 상태. 실제 고객 발송은 하지 않는다. |
| AuditLog | backend/app/models.py | 사용자 행동과 변경 전후 값. 현재 로그인·로그아웃·설정 변경을 기록한다. |
| ReviewSettings / RequiredDocRule / CrossCheckRule | backend/app/models.py | 검토 설정과 규칙 정의. T-02에서는 정의만 적재하며 규칙 엔진을 실행하지 않는다. |
| KcdCode / DrugCatalog | backend/app/models.py | 후속 정규화·약제 항목 대조에 사용할 참조 테이블. C18.7 참조 명칭을 시드하며 실제 의료 판단을 대신하지 않는다. |
| current_user / require_admin / require_claim_access | backend/app/auth.py | 인증·관리자 역할·담당 청구 접근 검사. 프론트의 메뉴 표시와 별개로 서버에서 권한을 검사한다. |
| seed_database | backend/scripts/seed.py | 명시적으로 가상 표시된 JSON을 적재한다. 기본 실행은 기존 행을 보존하고 --demo에서만 DB 행을 초기화한다. 파일은 삭제하지 않는다. |

## 프론트엔드

| 객체 | 위치 | 역할과 이유 |
|---|---|---|
| getCurrentUser / requireUser | frontend/lib/auth.ts | 서버가 쿠키를 FastAPI에 전달해 로그인 상태를 확인한다. 응답은 no-store이며 React cache는 동일 요청 안에서만 중복 조회를 줄인다. |
| LoginForm / LogoutButton | frontend/components/ | 세션 발급·폐기는 서버 API로 요청한다. 브라우저 저장소에 토큰이나 역할을 저장하지 않는다. 실패 시 다시 시도할 메시지를 보여준다. |
| ProtectedLayout | frontend/app/(protected)/layout.tsx | 로그인 확인 후 공통 헤더와 사용자 정보를 렌더링한다. |
| WorkspaceShell / workspacePages | frontend/components/workspace-shell.tsx, frontend/lib/navigation.ts | 메뉴·검색·우하단 안내를 구성한다. 운영 관리 메뉴는 관리자에게만 표시하며 경로에서도 접근을 검사한다. |
| ComingSoon | frontend/components/coming-soon.tsx | 후속 티켓의 업무 기능이 아직 준비 중임을 표시한다. 분석·처리가 완료된 것처럼 가상 결과를 보여주지 않는다. |
| globals.css | frontend/app/globals.css | HTML 원본의 라이트·다크 색상과 글꼴을 Tailwind v4 테마에 연결한다. 글꼴 파일은 npm 패키지로 로컬 제공한다. |
| next.config.ts | frontend/next.config.ts | 같은 출처 /api 요청을 FastAPI로 전달한다. 내부 주소는 BACKEND_URL로 관리하고 브라우저 번들에 공개하지 않는다. |

## 로컬 실행 시 알아둘 점

- 세션은 서명된 httpOnly·SameSite=Lax 쿠키이며, 유효 기간은 기본 8시간이다. 쿠키는 암호화 저장소가 아니므로 사용자 ID 외의 민감한 내용을 담지 않는다.
- 개발 기본 SESSION_SECRET은 프로세스별 임의값이다. 재시작 뒤 로그인 유지가 필요하면 루트 .env에서 고정한다. 배포 HTTPS 환경에서는 SESSION_HTTPS_ONLY도 켠다.
- 데모 로그인은 비밀번호가 없는 역할 체험 기능이다. 실제 고객 인증·SSO를 대신하지 않는다.
- 데이터베이스는 data/gaon.db이다. 시드 초기화는 검증된 가상 데이터 전용 DB에서만 실행한다.
- Next.js는 frontend/.env.local의 BACKEND_URL을 읽을 수 있다. FastAPI는 프로젝트 루트 .env를 읽는다. 실제 .env는 Git에서 제외한다. 환경 정리 단계에서 긴 임의 SESSION_SECRET을 고정했으며, 값은 출력하거나 문서에 기록하지 않는다.


## 서류 처리 엔진 추가 객체 (T-07~T-11)

| 객체 | 위치 | 역할과 판단 이유 |
|---|---|---|
| attach_silson24 | backend/app/services/silson24.py | 가상 표시·청구 ID가 맞는 정형 서류 3종만 연결하며 반복 수신을 중복 저장하지 않는다. |
| UpstageClient | backend/app/services/upstage.py | Classify→Parse→Extract의 v1 직접 호출. 성공·실패 응답, 파일/요청 해시, 잠금, 30페이지 예약 장부를 관리한다. 캐시 전용은 네트워크 금지다. |
| DOCUMENT_SCHEMAS / to_extract_schema | backend/app/schemas/documents.py, to_upstage.py | Pydantic 단일 원본에서 Extract 전용 스키마를 만든다. API 제약을 위한 변환과 값 검증을 분리한다. |
| NormalizationResult | backend/app/services/normalize.py | 정규화값과 저장할 셀별 필드, KCD 참조 명칭을 묶는다. 잘못된 값도 format 이유와 함께 보존한다. |
| ReviewDocument / ReviewResult | backend/app/services/rules.py | 정답·API 없이 실행할 규칙 입력과 결과다. 검수 이유를 남기고 지급 여부를 판단하지 않는다. |
| ProcessJob | backend/app/models.py | 작업 ID·단계·진행률·결과·오류를 영속 저장한다. 활성 작업은 청구당 1개이며 서버 재시작 시 미완료 작업을 실패로 표시한다. |
| save_uploads / run_job | backend/app/services/uploads.py, pipeline.py | 파일 형식·용량·총 페이지를 검증하고 백그라운드 스레드에서 처리한다. 문서별 실패를 기록해 나머지 결과를 보존한다. |
| run_validation | backend/scripts/validate_engine.py | 입력 폴더를 받아 앱 4장+모의 전자 3종을 API 경로로 실행한 뒤 정답과 비교한다. 격리 DB와 폴더/내용 지문별 결과를 사용한다. |

- 역할은 서버에서 강제한다. 관리자에게 업로드·분석 실행 권한을 부여하지 않는다.
- 실측 word_coordinates는 단어별 다각형 배열이다. 한 단어의 기울기를 보존하고 여러 단어는 합친 영역을 사용한다. page=-1·빈 좌표는 찾지 못한 경우이므로 Parse 대체 또는 좌표 없음으로 남긴다.
- 응답을 잃은 요청은 이미 과금됐을 수 있어 자동 재전송하지 않는다. pending 파일과 예약 장부를 보존하고 수동 확인한다. 같은 파일이라도 스키마를 바꾸면 새 요청이므로 과금될 수 있다.
- 자동 테스트는 HTTP 모킹이 필수다. 일반 pytest는 live 마커를 제외한다. 실제 검증 후 반복 평가는 `python -m scripts.validate_engine --cached`를 사용한다.
- 현재 실측의 정답 비교 불일치 2건은 그대로 남겼다. 높은 confidence가 정답을 보장하지 않는다는 사례다.

## T-12~14 화면 연결 객체
- `Customer`/`Policy`: 고객 ID로 동명이인을 구분하고 청구와 증권의 보장 기간·가입 특약을 연결한다. 모든 데모 정보는 가상이다.
- `services/workspace.detail`: 저장 데이터와 현재 규칙으로 화면 DTO를 구성한다. DB 객체를 직접 수정하지 않는 새 `ExtractedField` 인스턴스로 필수서류를 재계산한다.
- `ExtractedField.value/raw_value`: 최초 추출값은 보존한다. `confirmed_value/confirmed_by`는 담당자 확정값·확정자이며 재검사 입력에만 덮어쓴다. 날짜·코드·금액 형식을 검증하고 변경 전후를 이력에 남긴다.
- `Issue`: 규칙·문서·필드 조합이 같으면 같은 이슈를 유지한다. 수동 확인은 보존하되 근거가 바뀌면 다시 연다. 설정으로 자동 해소했던 이슈가 재발해도 다시 연다.
- `SupplementRequest`: 작성 중 → 모의 발송(화면: 회신 대기). 발송된 초안은 수정할 수 없으며 동일 발송을 반복해도 이력을 중복 생성하지 않는다. 실제 알림톡·문자는 보내지 않는다.
- `ReviewSettings`: low·원문 불일치·형식 오류별 담당자 확인 여부. 관리자가 저장하면 기존 청구를 재검사한다. 문서 처리 중에는 변경을 거절한다.
- `RequiredDocRule`: 필수서류 목록과 기존 조건을 분리한다. 화면의 서류 목록 편집은 조건을 유지한다.
- `Original`: 원본 이미지와 정규화된 실제 추출 좌표를 같은 비율로 표시한다. 좌표가 없는 실손24 데이터에는 좌표를 생성하지 않고 대응 가상 서식임을 표시한다.
- `useResource`: 요청 URL별 응답·오류를 관리해 검색이 바뀌었을 때 이전 검색 결과를 새 결과로 보여주지 않는다.

## T-15~17 검색·챗봇 객체
- `Chunk`: 허용 목록의 조·항/절 원문과 문서명·판본·가상 여부를 보존하는 Qdrant payload다. reference/HWP는 읽지 않는다.
- `Solar`: Settings의 비밀키로만 HTTP를 호출한다. 임베딩은 모델+내용별 캐시, 대화 응답은 디스크에 저장하지 않는다. `USE_CACHED_RESULTS=true`에서는 새 LLM 호출을 막고 사용자용 오류를 반환한다.
- `KnowledgeBase`: policy/manual 컬렉션을 만들고 dense 검색 후보에 일반 단어·명시 식별자 가중치를 더한다. CLI는 연결을 닫고, 서버는 프로세스당 클라이언트 하나를 수명 종료 시 닫는다. 로컬 Qdrant 사용 중 재인덱싱은 서버 종료 후 실행한다. 서버형 Qdrant는 QDRANT_URL/키로 전환한다.
- `ChatAgent`: LangGraph classify→tools→answer 세 노드. Solar strict 의도 분류, 허용 도구 호출/Pydantic 인자 검증, 배정 권한, 원문 인용 검증을 거친다. 청구 요약/대조/초안은 결정적 출력으로 사실을 바꾸지 않는다. 도구 조회는 감사 이력에 남기되 대화 원문은 넣지 않는다.
- `Tools`: 고객·계약·청구/이슈/서류를 읽는다. 동명이인·여러 청구는 선택을 요청한다. 주민번호/계좌/연락처는 LLM에 전달하지 않는다. 약제비 대조는 정규화/확정값을 처방전과 비교하고 비급여 기준을 읽어 가능성만 반환한다.
- `ChatAnswer`: answer/intent/citations/claim_refs/suggested_actions/refused 모두 필수. issue_id는 null 허용. API는 이번 확정 요청에 따라 JSON 응답이며 SSE·DB 대화 목록은 사용하지 않는다.
- `ChatScreen`: 대화 목록/질문 바로가기/근거 패널/편집 초안은 React 메모리다. 새로고침하면 지워지고 localStorage·DB에 저장하지 않는다.

## T-05~06 시연 데이터 객체와 경로
- `customers.json`: 고객10명·계약·청구13건·대표사례·서류 입력과 기대 이슈의 단일 원본. 상태 값은 넣지 않으며 기대 이슈는 평가에만 사용한다.
- `Policy.contract_date`: 계약일. 보장 기간과 분리해 90일 경계를 계산한다. 알 수 없으면 null이며 추정하지 않는다.
- `Document.provenance`: upstage/mock/silson24/unprocessed. 실제 검증 API 호출 여부와 가상 고객 여부는 별개다. UI 개발 표시는 설정으로 숨겨도 DB 출처는 보존한다.
- `gen_claim.generate`: 공통 HTML/정답을 만들고 `render_folder`는 HTML·PNG 해시가 달라진 문서만 재캡처한다. 김유정 기존7장은 고정 기준 자산이다.
- `prepared_rows`: mock은 정답을 명시적으로 입력하고, live/cached는 Upstage 응답에서 값을 읽는다. 정답으로 실제 모델 값을 덮어쓰지 않는다.
- `verify_samples`: 동일 규칙 엔진 결과와 기대 이슈/정규화 항목을 비교한다. 김유정 기존 세분류 오독/CV-03만 명시적 optional로 허용하고 새 예상 밖 이슈는 실패한다. png/photo 결과와 실제 photo_count를 분리한다.
- `seed_samples`: API 신규 호출 없이 성공 캐시를 재생하고, 없으면 mock으로 표시해 적재한다. 기존 문서가 있으면 증분 적재를 건너뛰고 --demo에서만 초기화한다.
- `sample_input`: 고객과 제공 파일의 정확한 해시가 맞는 데모 mock만 허용한다. 알 수 없는 파일/실측 고객 원본을 mock으로 바꾸지 않는다.
- 회신 처리: 기존 EXTRACTED 원본·확정값을 건드리지 않고 새 서류를 읽어 재검토한다. 요청 유형이 정상 제출되고 누락 과제가 해소돼야 보완 요청을 received로 바꾼다.

## T-18 평가 객체
- eval_chat.measure/aggregate: 정답은 평가기에만 주입한다. 0분모 N/A, recall macro/인용 micro/거절/요지·금지 패턴을 분리한다.
- eval_chat: SQLite/Qdrant 스냅샷에서 문항별 독립 세션 최대3개를 실행한다. 체크포인트로 완료 문항 재호출을 피하고 고정 rubric·정답 해시를 보존한다.
- eval_extract.confusion: 실제 API 필드만 주 평가로 집계한다. FIELD-* 검수 이슈와 오답의 TP/FP/FN/TN을 계산하며 업무상 CV 이슈와 구분한다.
- Tools.get_workload: 담당자 배정 범위의 현재 상태 숫자만 반환한다. 전체 고객 개인정보 목록을 반환하지 않는다.
