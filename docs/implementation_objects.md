# 구현 객체 안내 — T-01~T-04

설계 원본을 변경하지 않고, 현재 코드에서 각 객체가 맡는 역할과 선택 이유를 정리한다.

## 백엔드

| 객체 | 위치 | 역할과 이유 |
|---|---|---|
| Settings | backend/app/config.py | 환경변수·경로·기본값을 모은다. 실행 폴더가 달라도 같은 프로젝트 DB를 바라보도록 절대 경로를 사용한다. 비밀값은 SecretStr로 표시를 감춘다. |
| create_app | backend/app/main.py | 설정을 주입받는 앱 팩토리. 테스트용 DB를 운영·데모 DB와 분리하고, lifespan에서 엔진을 열고 닫는다. |
| get_session | backend/app/db.py | 요청마다 SQLModel 세션을 만들고 정리한다. 전역 세션을 공유해 요청끼리 간섭하는 일을 피한다. |
| User / Role | backend/app/models.py | 데모 계정과 담당자·관리자 역할. 쿠키에는 역할을 넣지 않고 매 요청 DB의 최신 역할을 확인한다. |
| Claim | backend/app/models.py | 청구 단위 집계 루트. 제출 문서·이슈·보완 요청·이력은 청구에 연결한다. |
| Document | backend/app/models.py | 문서 유형·원본 경로·추출 원본 결과. 현재 기반 티켓에서는 실제 분석을 실행하지 않는다. |
| ExtractedField | backend/app/models.py | 문서에서 추출한 값과 원본 근거·확정값을 분리해 보관한다. 원래 추출 결과를 담당자 수정값으로 덮어쓰지 않기 위해서다. |
| Issue | backend/app/models.py | 누락·불일치·확인 필요 항목과 근거·처리 상태. 규칙 실행은 후속 티켓이다. |
| SupplementRequest | backend/app/models.py | 보완 서류와 모의 발송 상태. 실제 고객 발송은 하지 않는다. |
| AuditLog | backend/app/models.py | 사용자 행동과 변경 전후 값. 현재 로그인·로그아웃·설정 변경을 기록한다. |
| ReviewSettings / RequiredDocRule / CrossCheckRule | backend/app/models.py | 검토 설정과 규칙 정의. T-02에서는 정의만 적재하며 규칙 엔진을 실행하지 않는다. |
| KcdCode / DrugCatalog | backend/app/models.py | 후속 정규화·약제 항목 대조에 사용할 참조 테이블. 현재 실제 의료 판단 데이터는 넣지 않는다. |
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
- Next.js는 frontend/.env.local의 BACKEND_URL을 읽을 수 있다. FastAPI는 프로젝트 루트 .env를 읽는다. 실제 .env 파일은 생성·수정하지 않았다.
