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

## T-18b 구조 청킹·규범 연결 객체
- `Chunk`: `article`은 호환용 조/장, `address`는 `제4조 ③ 2호`처럼 인용 주소다. `node_id`는 문서/보장종목/조/항/호/목, `parent_id`는 확장할 부모다. `coverage_section`을 빼고 같은 조를 합치면 상해와 질병을 섞으므로 반드시 네 필드 `(source_path, coverage_section, article, paragraph)`로 묶는다.
- `Structure.nodes`: 부모 항 전체와 목 원문. 인덱스 빌드가 `KB_STRUCTURE_PATH`의 별도 JSON에 저장하고 컨텍스트 조립은 여기서 부모 항을 꺼낸다. `definitions`는 원문 정의 표제→노드 사전이다. `refs`와 `defined_terms`는 한 단계, 보충 근거 최대2개만 확장한다.
- `authority_level`: 1 표준약관 / 2 가온 주계약·상품요약 / 3 가온 특약 / 4 매뉴얼·문구. 숫자가 곧 적용 순서는 아니다. 적용 특약을 먼저 읽고 명시적 준용 `falls_back_to`로 주계약, 근거 표준약관을 잇는다. `governs`는 해당 노드의 보장종목/문서 적용 범위다. 매뉴얼은 업무 기준이며 약관 자체로 인용하지 않는다. 특약의 명시적 별도 규정 우선과 그 외 상·하위 충돌 확인 필요를 생성 프롬프트에서 구분한다. 일반 충돌 자동 법률 판정기를 구현한 것은 아니다.
- `KnowledgeBase`: 원 질문+Solar 재작성 한 개를 각각 dense/BM25로 찾고 주소 정확 일치 순위와 RRF로 합친다. 구조 주소로 중복을 줄인 후보10개를 Solar로 재정렬해 top3을 만든다. 검색 기본 보장종목은 현재 질병 청구 PoC의 `RAG_DEFAULT_COVERAGE=질병비급여`이며 명시된 상해/MRI는 해당 종목이다. 실운영은 고객 계약에서 종목을 선택하도록 확장해야 한다.
- `GroundedAnswer`: 모델이 사용한 `used_chunk_ids`를 먼저 고른다. 서버가 이 ID의 실제 원문으로 최대2개 인용을 만든다. 모델이 quote를 제안하면 정확한 부분 문자열만 통과시키고, 비워 두면 서버가 조각 원문을 그대로 쓴다. 허용되지 않은 ID와 변형 인용은 버린다.
- `refusal_reason`: 지급 결정·금액 계산·민감정보·사기·자동차 과실 질문을 의도 LLM 전에 차단한다. 일반 약관 비율·기한 설명은 허용한다. 안전 가드 통과 후 명시적 서류 읽기를 모델이 거절하는 경우는 입력에 있는 고객명으로만 읽기 경로에 보낸다. DB 도구는 매번 배정 권한을 확인한다.
- `Tools.call_with_retry`: Pydantic 검증 후 읽기 도구를 실행하고 실패 시 한 번만 재시도한다. 403은 즉시 전파, 두 번 실패하면 `확인하지 못했어요`다. 로그는 도구명/시도/상태·오류 클래스만 남긴다. 자유 도구 계획의 ID 재추측은 의도별 고정 읽기 절차로 대체했다.
- `added_diagnosis_words`: 공백/괄호를 정규화해 진단명이 원문에 없으면 번역·보정 의심으로 검토에 보낸다. 원본에 실제 병기된 번역을 오류로 분류하지 않는다.
- `eval_retrieval`/`legacy_search`: ablation 전용. 이전 검색 점수 식을 고정한 legacy+새 구조, dense-only 참고, 최종 hybrid를 나눈다. legacy는 운영에서 호출하지 않는다. 정답은 평가기만 읽는다.

## 답변 말투 처리 (T-18 후속)

- `app/agent/tone.py`의 `TONE_PROMPT`는 말투 지침과 개발 질문을 쓰지 않은 예시3쌍이다. 업무 판단·검색·인용 정책은 기존 절차가 맡는다.
- `ToneAnswer`는 본문 하나만 받는 구조화 객체다. 생성 모델은 의도, 인용, 청구 참조, 버튼, 거절 여부를 바꿀 수 없다.
- `ChatAgent.tone`은 정책 답변의 금지 패턴을 검사하거나 DB/템플릿 답변을 문장화한다. 모든 사실 초안은 본문만 최초 문장화한 후 위반하면1회만 재생성한다. 고정 거절문은 검사만 하고 위반할 때1회 재생성한다. 계속 위반해도 추가 호출하지 않고 유형만 로그에 기록한다.
- `protected_numbers`와 `payment_assertion`은 말투 수정 중 숫자 소실과 새 지급 확정을 막는다. 실패하면 이전 사실 답변을 유지한다. 이 검사는 의미 동등성의 완전한 증명이 아니어서 실측 요지·거절·인용 회귀 평가를 함께 한다.
- `tone_trace`는 요청 객체의 메모리에만 남는다. 일반 서비스 로그에는 본문·고객명·질문·키를 넣지 않는다. 명시적 평가 CLI만 가상 답변/trace를 산출물로 보존한다.
- `scripts/tone_grade.py`는 요지 rubric을 바꾸지 않고 자연스러움/내부 용어 없음/결론 우선을 각각1~5점으로 채점한다. `eval_chat --tone`과 `eval_tone --out <새폴더>`는 개발 셋 및 필수 시연 전후 평가용이다. 기존 홀드아웃은 재실행하지 않는다.


## 시연용 답변 구조와 응답 캐시
- `claim_answer.render_claim`: 저장된 이슈/서류 값에서 결론, 보완 요청, 원형 번호 항목, 다음 행동을 만든다. 질문 문장이나 가상 고객 정답은 읽지 않는다. 병합은 같은 진단서의 코드 관련 이슈에만 적용한다. 원본 이슈/claim_refs는 유지한다.
- `ChatAgent.tone`: 청구 검토는 구조 템플릿을 유지하고 다른 의도는 해요체로 검사한다. 표준 고객 문자 원문은 기존 템플릿을 유지한다.
- `Solar`: SOLAR_RESPONSE_CACHE=false 기본. 가상 평가에서 true면 요청 내용 해시별 성공 응답을 data/cache/chat_responses에 저장한다. SOLAR_USAGE_PATH 지정 시 토큰 장부만 기록한다. 캐시 응답은 새 API 호출로 세지 않는다.
- `eval_presentation`: 관련 문항의 기존 실제 응답을 재사용하는 표시 단계 비교다. 의도/검색을 새로 실측한 평가가 아니다. 요지는 동일 rubric으로 양쪽 각1회 채점한다.
- `report_solar_usage`: 수신 토큰 정가와 중단 요청의 평균 단가 추정을 구별한다. 실제 청구액과 같다고 보장하지 않는다.


## 근거 패널과 이슈 링크의 표시 객체 (T-18 시연 마무리)
- `ChatAgent`는 tone 다음에 `display.present`를 실행한다. API의 `display_answer`는 화면용 출처 설명을 포함한다. 고객에게 보낼 문자 편집/대화 history는 원래 `answer`를 사용해 업무 기준 문구가 문자에 섞이지 않게 한다.
- `display_citations`는 본문 괄호의 문서/조항을 순서대로 현재 KB에 연결한다. 같은 조의 상해/질병을 구분하고 모호한 보장종목은 임의 선택하지 않는다. 원래 `citations`와 평가의 인용 2개 제한은 그대로이며, 화면은 사용자가 요청한 본문 인용 3개도 보여줄 수 있다.
- `Citation.display_quote`는 표시 전용이다. KB/원래 `quote`를 수정하지 않고 CV 이름과 표의 머리글:값 줄로 읽기 쉽게 바꾼다. 원문 출처 연결과 평가 기록은 보존한다.
- `DisplayClaimRef`는 기존 claim_id/issue_id에 사람이 읽는 `label`을 더한 객체다. 본문에 언급한 항목만 화면 링크로 내보내고, 병합한 질병코드 원인은 대표 링크 하나로 남긴다.
- `ChatScreen`은 같은 표시 근거 배열로 요약 카드와 오른쪽 원문 패널을 렌더링한다. 세션은 React 메모리에만 있어 새로고침/로그아웃 후 재로그인 시 사라진다. demo_reset은 이번 범위에 포함하지 않는다.
- 청구 맥락의 지급 거절문은 DB 이슈에서 목록을 만들고 LLM 말투 재생성을 거치지 않는다. 거절 판단 가드/권한/평가 기준은 그대로다.


## T-19 시연 보완 객체
- `claim_status.claim_status`는 현재 필수서류 누락을 사람 확인보다 먼저 적용한다. 목록과 상세는 `workspace.detail`, 챗봇 `Tools.get_claim/get_workload`도 같은 읽기 모델을 사용한다. 처음부터 이슈가 없는 건의 자동 통과와 확인 후 이관 가능한 `ready_review`를 구분한다. `to_payment_review`는 심사 이관 상태이며 지급 승인이 아니다.
- `workspace.comparisons`는 켜진 대조 규칙과 저장된 서류 값을 사용한다. 환자명은 엔진과 같이 청구 접수정보를 기준으로 각 서류와 대조한다. 보장 기간은 진료/입퇴원 시작일과 종료일을 함께 확인한다. 표의 숫자는 대조 행에서 집계하며 별도 시드 상태나 특정 고객명을 사용하지 않는다.
- `render_claim(..., as_rows=True)`는 챗봇과 상세/문서 분석 화면이 공유하는 표시 행이다. 같은 진단서의 질병코드 원인만 합치며 `related_ids`에 함께 설명한 실제 이슈 ID를 담는다. 사람이 그 항목을 확인하면 해당 ID들만 확인한다. 누락 확인은 제출을 대신하지 않는다.
- `ChatAnswer.draft_text`는 고객에게 보낼 표준 문구만 담는다. `answer`의 이미 제출 안내, 템플릿 없음 안내와 분리한다. 명시한 서류가 알려지지 않은 경우 누락 서류로 바꿔 요청하지 않고 템플릿 목록을 안내한다.
- `useTyping`은 받은 본문을 초당50글자로 표시한다. API 스트리밍이나 답변 생성 변경이 아니다. 클릭/키보드 건너뛰기와 prefers-reduced-motion을 지원하고 초안 타이핑이 끝나야 편집/복사한다. 가상 시계 단위 검증은 `node scripts/check-typing.mjs`다.
- `tours.ts`는 네 화면의 단계 데이터, `OnboardingTour`는 마스크·위치·키보드·localStorage 실패 처리를 맡는다. 투어가 없는 화면에는 작동하지 않는 안내 버튼을 남기지 않는다.
- `Original`은 비교 원본에도 재사용한다. 기본값은 추출 좌표만 사용하며 좌표가 없으면 이미지와 위치 정보 없음만 표시한다. 문서2페이지의 좌표는 그 페이지에서 시작한다. 모달은 Esc·Tab 제한과 초점 복원을 지원한다.
- 인박스는 URL로 필터/페이지를 보존하고 sessionStorage에 해당 URL/스크롤을 저장한다. 출처는 `SHOW_DEV_BADGE` 기본false, `DEMO_MODE`에서 항상 숨기며 DB provenance는 유지한다.

## T-19l 보완 안내 공통 객체
- `SupplementTemplates`: KB_PATH의 기존 파서 결과 중 보완 표준 문구를 조회하는 로컬 어댑터다. 원문/평가셋/인덱스를 수정하지 않고 Qdrant·임베딩·LLM도 열지 않는다.
- `claim_supplement_draft`: 챗봇의 Tools.draft_supplement(claim_id, [])를 호출한다. 고객 권한과 저장된 누락 이슈를 동일하게 읽고 같은 고객명/템플릿 문구를 반환한다.
- 보완 API: GET /api/supplements?claim_id=...는 권한 범위와 선택 청구를 모두 검사한다. POST /api/claims/{id}/supplements는 요청할 실제 누락이 있을 때만 초안을 생성/미발송 초안 재생성한다. 이미 발송된 요청은 덮어쓰지 않는다.
- `SupplementScreen`: 선택 청구별 응답 URL을 사용하며 응답 URL이 바뀌면 이전 고객을 로딩 상태 뒤로 숨긴다. 카드/편집기에도 선택 청구 필터를 적용한다. 새 서버 문구는 같은 초안 ID여도 편집기에 반영하고 모의 발송 피드백은 유지한다.


## T-19p/q 최신 보완 객체 (앞선 T-19l 설명 대체)
- claim_supplement_draft는 config의 SUPPLEMENT_MESSAGE_TEMPLATES 고정 JSON을 사용한다. 고객·계약·누락 서류를 검증해 실제 정보로 채우며 챗봇/LLM/벡터 검색 호출은 없다.
- workspace.field_confidences는 Extract choices[0].confidence_score의 JSON 문자열/객체에서 _value만 읽는다. 중첩 배열은 Field.key와 같은 경로로 평탄화하며 invalid/범위 밖/문맥 점수는 제외한다.
- SupplementScreen은 검색된 고객 요약을 왼쪽, 실제 발송·접수 이력과 편집기를 오른쪽에 둔다. 생성 응답을 즉시 편집기에 연결하며 고객 선택 드롭다운은 없다.
- Original은 비교 문서별 배율과 포인터 드래그 스크롤을 분리한다. 서류 정보는 문서별 탭과 이슈 field_keys만 모은 비교 항목 탭으로 한 표씩 표시한다. 탭/이슈 변경 시 첫 행으로 돌아간다.
