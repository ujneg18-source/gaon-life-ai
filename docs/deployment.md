# Vercel + Render 무료 시연 배포

저장소는 비공개로 유지한다. 디자인·문구·평가·홀드아웃·안전 규칙은 변경하지 않는다.

## 포함할 자료

- 코드와 가상 고객 10명/청구 13건의 시드·서류. 실제 작업 DB는 업로드하지 않는다.
- `deploy/runtime-assets.tar.gz`: 가상 PNG 원본 해시에 대응한 성공 Document AI 캐시 42개, 공개/가상 문서만 색인한 Qdrant 2개, 구조 인덱스·문서 호출 예산 장부(기존 예약 21페이지). manifest SHA256 검증 후 복원한다.
- 프론트 출처 본문은 허용 목록 12종을 서버 전용 JSON으로 묶었다. 인증된 기존 페이지에서만 읽는다. 원본 텍스트와의 동일성은 테스트한다.
- `.env`, 키, DB·백업, 업로드/회신 기록, 기존 채팅 캐시, 평가/홀드아웃 자료, 실제 회사 참고 약관, HWP 원본, 사용자 경로와 Git 이력은 **컨테이너에 포함하지 않는다**. 로컬 원본과 기존 캐시는 삭제하지 않는다.
- 기존 Git 이력을 재작성하지 않는다. 저장소 공개 전 이력에 있는 작성자 이메일·이름·로컬 경로는 별도 검토가 필요하다.

## 1. GitHub 연결

Vercel 가져오기에서 저장소가 안 보이면 **GitHub 앱 구성하기 → Only select repositories → gaon-life-ai**를 선택한다. 공개 전환할 필요는 없다. Render에도 같은 저장소 접근 권한을 부여한다.

## 2. Render 먼저 배포

Blueprint에서 저장소 main과 `render.yaml`을 선택한다. 또는 Web Service를 Docker / Free / Singapore로 만들고 루트 `Dockerfile`을 지정한다. Health check는 `/health`다.

환경 변수:

| 이름 | 값 |
|---|---|
| DEPLOY_RUNTIME_DIR | `/tmp/gaon-demo` |
| DEMO_MODE | `true` |
| SESSION_HTTPS_ONLY | `true` |
| SESSION_SECRET | Blueprint 자동 생성. 수동 생성 시 충분히 긴 무작위 비밀값 |
| CORS_ORIGINS | `["https://실제-프로젝트.vercel.app"]` (JSON 배열) |
| UPSTAGE_API_KEY | Render 대시보드에서만 입력. Git/Vercel/브라우저 변수에 넣지 않는다 |
| SOLAR_RESPONSE_CACHE | `true` |
| USE_CACHED_RESULTS | `false` (성공 캐시 우선, 미스만 실제 호출) |

가상 서류의 기본 적재와 청구 맥락 4문항은 API 키 없이 검증했다. 일반 약관 질문/새 문서에는 키가 필요하며 Upstage 비용은 호스팅 무료 여부와 별개다. 완전 오프라인 시연은 `USE_CACHED_RESULTS=true`로 바꾸되 저장되지 않은 질문은 연결 오류가 될 수 있다. 평가용 응답을 시연 답변으로 재사용하지 않는다.

첫 시작 시 자산을 `/tmp/gaon-demo`에 풀고 DB·가상 업로드를 생성한다. 같은 디스크에서 프로세스만 재시작되면 기존 캐시/서류를 보존하고 DB를 백업한 뒤 증분 시드한다. Render가 디스크를 비우면 초기 시연 상태로 복원된다. 영구 디스크/외부 DB는 생성하지 않는다.

## 3. Vercel 배포

- 저장소: `ujneg18-source/gaon-life-ai`, 브랜치 `main`
- Root Directory: `frontend`, Framework: Next.js, Node.js: 22.x
- Build Command: `vercel.json`의 `npm run build -- --webpack`
- 환경 변수 `BACKEND_URL=https://실제-서비스.onrender.com` (끝 `/`와 `/api` 없음)
- API 키/SESSION_SECRET은 Vercel에 넣지 않는다.
- Vercel 실제 주소가 정해지면 Render `CORS_ORIGINS`를 그 주소로 갱신한다. 브라우저는 Vercel의 같은 출처 `/api`를 사용한다.

로그인 → 메인 투어 1/5~5/5 → 김유정 상세 → 원본 비교 → 청구 맥락 질문 → 데이터 출처 본문을 확인한다. 잘못된 CORS 주소는 로그인 POST를 403으로 만든다. 백엔드 주소 변경 시 Vercel을 다시 배포한다.

## 4. 무료 서비스 핑과 촬영

[Render 공식 안내](https://render.com/docs/free): 15분 무요청 시 휴면, 재시작 시 디스크 소실, 복귀 약 1분. **1시간마다 핑은 휴면 방지가 되지 않는다.** 외부 모니터를 사용한다면 Render의 실제 `https://서비스.onrender.com/health`에 5~10분 간격 GET을 보내는 방식이다. API/채팅을 핑 대상으로 쓰지 않아 Upstage 호출을 발생시키지 않는다. 상태 점검은 서버 수신 요청이며 항상 켜짐/데이터 보존을 보장하지 않는다.

[Vercel Hobby Cron](https://vercel.com/docs/cron-jobs/usage-and-pricing)은 하루 1회만 지원하므로 무료 Vercel Cron으로 5분 핑을 구성하지 않는다. 이 저장소는 외부 모니터 가입이나 예약을 생성하지 않았다. 촬영 직전 Render `/health`를 열어 깨어난 후 시작하는 것으로 두 서비스만으로도 시연 가능하다.

로컬과 달리 Render 임시 디스크의 DB 백업도 재시작 시 사라진다. 실제 개인정보를 입력/업로드하지 않는다. 데모 로그인/관리자 초기화가 있는 시연 서비스다.
