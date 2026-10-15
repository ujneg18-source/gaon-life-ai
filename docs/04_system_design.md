# 04. 시스템 설계 · API 명세

| 항목 | 내용 |
|---|---|
| 버전 | v1.0 (2026-10-15) |
| 아키텍처 그림 | `design/diagrams/architecture.png` (원본 `architecture.html`) |

---

## 1. 전체 구조

```
[Next.js 프론트]  ── REST · SSE ──>  [FastAPI 백엔드]
  로그인 · 워크스페이스 · 챗봇              │
                                        ├─ 서류 처리 파이프라인
                                        │    └─ Upstage Agents API (Studio 워크플로)
                                        │         Parse → Classify → Extract
                                        ├─ 검토 엔진 (우리 코드)
                                        │    정규화 · Pydantic 검증 · 필수서류 · 교차검증 · 라우팅
                                        ├─ 약관 대조 · 챗봇 (LangGraph)
                                        │    ├─ Qdrant 로컬 (약관 · 매뉴얼 벡터)
                                        │    └─ Solar Chat / Embedding
                                        └─ SQLite (청구 · 서류 · 항목 · 이슈 · 이력)
```

### 처리 흐름 (청구 1건)
1. 업로드 · 실손24 모의 JSON 연결 → `documents` 생성
2. 이미지 서류마다 Agents API 실행 (업로드 → 실행 → 결과 폴링)
3. 결과를 표준 스키마로 매핑 → Pydantic 검증 → `fields` 저장
4. 검토 엔진: 필수서류(4-1) → 교차검증(4-2) → 약관 대조(4-3) → 신뢰도 라우팅(4-4) → `issues`, 청구 상태
5. 이력 기록 → 프론트 갱신

---

## 2. Upstage 구성

| 구성 | 역할 | 비고 |
|---|---|---|
| Studio | 문서 유형과 추출 항목 설계, 샘플로 조정 | 결과물 = 에이전트 ID(`agt_...`) |
| Document Parse | 스캔 · PDF의 글자, 표, 레이아웃 읽기 | 권장 방식. 내부적으로 OCR 포함 |
| Document OCR | 단어 단위 글자 + 위치 | 원본 하이라이트 좌표가 필요할 때만 |
| Classify | 진단서 · 영수증 · 세부내역서 등 분류 | 기본 패키지 7종 + 조직검사 결과지 등 추가 |
| Information Extract | 유형별 항목을 정해진 스키마로 추출 | 표준 스키마 키 사용 |
| Solar Embedding | 약관 · 매뉴얼 벡터화 (RAG) | 모델명 콘솔 확인 |
| Solar Chat | 담당자용 요약, 보완 요청 초안, 약관 대조 설명 | |
| Agents API | Studio 워크플로를 백엔드에서 실행 | `POST /v2/files` → `POST /v2/responses` → `GET /v2/responses/{id}` |

우리 코드 담당: 정규화 · 검증, 필수서류 · 교차검증 규칙, 약관 대조, 신뢰도 라우팅, RAG 검색, 화면


### 공식 문서로 확인한 사항 (2026-10-15, console.upstage.ai/docs/getting-started)
| 기능 | 엔드포인트 · 모델 | 호출 방식 |
|---|---|---|
| Chat (Reasoning) | `https://api.upstage.ai/v1` · `solar-pro4` | OpenAI 호환, `reasoning_effort` 지원 |
| Document Parse | `POST /v1/document-digitization` · `model=document-parse` | multipart, `ocr=force` 옵션 |
| Information Extract | `base_url=/v1/information-extraction` · `information-extract` | OpenAI 호환, `response_format` = **JSON Schema** |
| Document Classify | `base_url=/v1/document-classification` · `document-classify` | OpenAI 호환, 분류 목록을 JSON Schema `oneOf`로 전달 |
| Embeddings | `/v1` · `solar-embedding-2-query` / `solar-embedding-2-passage` | OpenAI 호환 |
| Agents (Studio) | `/v2` | 업로드 → 실행 → 조회 |

- 가입 시 무료 크레딧 $10
- API로 보낸 데이터는 저장 · 재사용하지 않는다고 명시 (기획서 보안 항목 근거)
- Extract · Classify가 JSON Schema를 받으므로 **Pydantic 모델의 `model_json_schema()`를 그대로 넘길 수 있다** → 표준 스키마가 코드 한 곳에서 관리됨

### API 테스트 결과 (2026-10-15, `backend/scripts/test_upstage.py`)
- **Document Parse 성공** (모델 `document-parse-260930`, 1페이지)
  - 응답: `api, content, elements, model, ocr, usage`
  - `elements[]` = `{id, page, category(header/paragraph/heading1/table…), content{html, markdown, text}, coordinates[4점]}`
  - 좌표는 **0~1 비율, 꼭짓점 4개**. 짧은 값은 각자 요소로 잡힘 → `C18.7`, `2026.09.18`이 라벨과 별도 박스로 나옴 (직인이 겹쳐도 인식)
  - 요소별 신뢰도 값은 없음
  - 기본 출력은 `html`만 채워짐 (`markdown`, `text`는 빈 값) → 필요하면 output 형식 옵션 확인
- **결론: 원본 하이라이트 가능.** Extract 값 → Parse 요소 텍스트와 매칭 → 좌표 사용
- **Information Extract 성공** (결제 수단 등록 후, 모델 `information-extract-260904`)
  - 결과: `{"diagnosis_code": "C18.7", "diagnosis_date": "2026-09-18"}` — 날짜를 스키마 형식(ISO)으로 맞춰서 돌려줌
  - 응답은 OpenAI chat.completion 형식. **값별 신뢰도 · 좌표 없음** (기본 옵션 기준, 문서에 추가 옵션 있는지 확인 필요)
- ~~설계 변경: 자체 확인 점수~~ → **Extract 공식 옵션으로 대체 (아래)**

### Information Extract 옵션 (공식 문서, 2026-10-15)
| 옵션 (`extra_body`) | 효과 | 응답 위치 |
|---|---|---|
| `confidence: true` | 필드별 신뢰도 **`high` / `low`** (모델 자체 판단, 정확도 보장 아님) | `message.tool_calls` 중 이름 `additional_values`의 `arguments` → 필드마다 `_value` + 신뢰도 |
| `location: true` + `location_granularity` | 필드별 좌표. `element`(기본, 칸 · 문단 단위) · `word`(단어 단위) · `all` | 같은 `arguments` → `_value`, `page`, `coordinates` / `word_coordinates` (0~1 비율, 꼭짓점 4개) |
| `split: true` | 같은 유형 서류 여러 건이 한 파일에 있으면 건별로 나눠 `choices[]`로 반환 (최소 단위 페이지) | `choices[]` |

- 스키마 규칙: 루트 object, **1단계 속성은 string · integer · number · array만** (object 불가), array 안 array 불가, 표는 array of object. 동기 API는 속성 100개 · 총 15,000자 이하
- Schema Generation API: 샘플 최대 3개로 초기 스키마 자동 생성 → 손으로 다듬기
- 서로 다른 서류가 섞인 파일은 Extract 분할이 아니라 **Document Classify**로 나눈다
- 비동기 API: `POST /v1/information-extraction/async` → `GET .../jobs/{job_id}` 폴링(5~10초). 작업당 문서 20개, 1,000페이지, 파일 50MB(동기와 동일), confidence · location 지원. 상태 CREATED · IN_PROGRESS · PARTIALLY_COMPLETED · COMPLETED · FAILED · CANCELED
- **데모 결정:** 서류 1장 = 동기 호출 1회(단순 · 디버깅 쉬움). 청구 1건을 비동기 작업 1개로 묶는 방식은 실제 도입 시 확장안으로 기획서에 기재

### 결정 (위 옵션 반영)
- **신뢰도:** Extract `confidence` (high/low) + 우리 검증을 합친다
  - 담당자 확인 대상 = Extract `low` **또는** 형식 검증 실패 **또는** Parse 원문에서 값을 못 찾음 **또는** 교차검증 실패
  - 화면 표시는 숫자(0.71)가 아니라 **높음 / 낮음** + 확인 이유 (예: "모델 신뢰도 낮음", "원문 불일치")
- **좌표:** Extract `location` (`word` 단위)를 기본으로, 없으면 Parse 요소 매칭으로 대체
- 운영 관리의 "자동 통과 기준" 슬라이더 → **확인 규칙 켜기/끄기**(신뢰도 낮음 · 원문 불일치 · 형식 오류)로 변경 검토

### Document Parse 입력 조건 (공식 문서)
- 형식: JPEG · PNG · BMP · TIFF · **HEIC**(아이폰 사진) · WEBP, PDF · DOCX · PPTX · XLSX · CSV · **HWP/HWPX**
- 동기: 100MB · 100페이지 / 비동기: 500MB · 2,000페이지, 페이지당 최대 2억 픽셀
- 권장: 너비 640px 이상, 가장 작은 글자가 이미지 높이의 2.5% 이상 → **목업 서류 왜곡 시 이 기준 근처로 일부만 떨어뜨려 저신뢰 사례를 만든다**
- 옵션: `merge_multipage_tables`(여러 페이지 표 병합, 세부내역서처럼 긴 표에 유용)

### 임베딩 · File Search (공식 문서, 2026-10-15)
- **Solar Embedding 2:** `solar-embedding-2-query`(질문) · `solar-embedding-2-passage`(문서), 1,024차원, 입력 8k, **정규화 벡터 → 내적 = 코사인**, 배치 요청당 100개 · 204,800토큰, RPM 100 · TPM 300,000. 별칭 없음(전체 이름으로 호출). Embedding 1은 2026-12-31 종료
- **File Search (베타):** Upstage 관리형 RAG. 파일 업로드 → `/v2/vector_stores` → 검색 → `/v2/responses`의 `file_search` 도구
  - 청킹 `auto`만(조항 단위 분할 불가), 메타데이터 필터 설명 없음, 하이브리드 언급 없음, 베타 기간 민감 데이터 업로드 금지 안내
  - **결정:** 본 구현은 Qdrant + Solar Embedding 2 + BM25 (조항 단위 분할 · `is_mock` 표시 · 하이브리드가 필요). File Search는 **평가 비교군**으로 사용 → "관리형 File Search vs 조항 단위 하이브리드 RAG" 근거 적중률 비교 (선택)

### Solar Structured Outputs (2026-10-15, docs/capabilities/generate/structured-outputs)
- 대상: Solar Chat(`solar-pro4`)의 `response_format: json_schema` — **Information Extract와 다른 기능**. 챗봇 응답(answer · citations · actions) 구조화에 사용
- 스키마 제약: 최상위 object, **모든 속성 required**, 선택 값은 `type: [x, "null"]`, `strict: true`, `additionalProperties: false`, 중첩 10단계, 로컬 `$defs`만
- 미지원: `allOf` · `oneOf` · `not` · `if/then/else` · `patternProperties` · 재귀 `$ref` (400 에러). 중첩 `anyOf` 피하기
- 결과는 `message.content` 문자열 → `finish_reason == "stop"` 확인 후 파싱 (`length`면 잘림)
- 신뢰도 · 위치 옵션 없음
- 구현 메모: Pydantic `model_json_schema()`는 Optional을 `anyOf`로, 날짜를 `format`으로 내보냄 → **Upstage용 스키마 변환 함수**(`schemas/to_upstage.py`)를 둬서 required 채우기 · nullable 변환 · additionalProperties false 적용. Information Extract에도 같은 제약이 있는지는 테스트로 확인

### 열린 질문
- ~~좌표 확보 방법~~ → Parse 요소 좌표 매칭으로 해결 (위 테스트 결과)
- Extract `confidence` + `location`을 동시에 켤 수 있는지, 응답 구조 실측 (test_upstage.py 2차)
- 문서용 임베딩 모델명, 기능별 페이지당 요금 (무료 $10 안에서 평가 규모 결정)
- 백엔드 호출 방식: Studio 에이전트(v2) vs 기능별 직접 호출(v1) → decisions.md 참고
- 외부 API 장애 대비: `config.USE_CACHED_RESULTS=True`면 저장해 둔 응답으로 시연 (시연 안정성)

---

## 3. 기술 스택

| 영역 | 선택 |
|---|---|
| 백엔드 | FastAPI, Pydantic v2, pydantic-settings, SQLModel(SQLite), httpx(async) |
| AI | LangGraph, Upstage Solar Chat · Embedding, Qdrant(로컬 모드), rank-bm25 |
| 프론트 | Next.js (App Router), TypeScript, Tailwind CSS. 화면 명세 = `design/gaon-ai.html` |
| 배포 | 프론트 Vercel, 백엔드 단일 서버(Render · Railway 등) + Qdrant 파일 동봉 |

---

## 4. 폴더 구조

```
upstage_demo/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 앱, 라우터 등록
│   │   ├── config.py          # 모든 상수 · 경로 · 모델명 · 임계값 (BaseSettings)
│   │   ├── db.py              # SQLModel 엔진 · 세션
│   │   ├── models.py          # 테이블 (03 데이터 설계)
│   │   ├── schemas/           # 표준 스키마 Pydantic 모델 (서류별)
│   │   ├── auth.py            # 데모 로그인 · 역할 의존성
│   │   ├── routers/           # auth, claims, documents, issues, supplements, logs, settings, chat
│   │   ├── services/
│   │   │   ├── upstage.py     # Agents API 클라이언트 (업로드 · 실행 · 폴링 · 캐시)
│   │   │   ├── normalize.py   # 매핑 · 정규화 · 검증
│   │   │   ├── rules.py       # 필수서류 · 교차검증 · 라우팅
│   │   │   ├── coverage.py    # 약관 대조
│   │   │   └── audit.py       # 이력 기록
│   │   └── agent/             # LangGraph 챗봇 (router, tools, rag)
│   ├── scripts/               # seed.py, ingest_kb.py, eval.py
│   └── tests/
├── frontend/                  # Next.js
├── data/
│   ├── samples/               # 가상 서류 이미지 + 정답 JSON
│   ├── mock_silson24/         # 실손24 모의 JSON
│   ├── kb/                    # 약관 · 매뉴얼 원문
│   └── cache/                 # Upstage 응답 캐시
└── docs/ · design/
```

---

## 5. API 명세

공통: JSON. 인증은 데모 로그인 후 받은 세션 쿠키(`gaon_session`). 권한 부족 403, 없음 404.

### 인증
| 메서드 | 경로 | 설명 | 역할 |
|---|---|---|---|
| POST | `/api/auth/demo-login` | body `{role: "reviewer"\|"admin"}` → 세션 발급 | 모두 |
| POST | `/api/auth/logout` | 세션 삭제 | 로그인 |
| GET | `/api/me` | `{id, name, role}` | 로그인 |

### 청구
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/claims?status=&q=` | 목록 (담당자는 배정 건만). 응답에 상태별 건수 `counts` 포함 |
| GET | `/api/claims/{id}` | 상세: 청구 정보, 서류 체크리스트, 이슈 요약, 단계 |
| PATCH | `/api/claims/{id}` | `{step}` 저장 |
| POST | `/api/claims/{id}/documents` | 파일 업로드 (multipart, 여러 장) |
| POST | `/api/claims/{id}/silson24` | 실손24 모의 JSON 연결 |
| POST | `/api/claims/{id}/process` | 파이프라인 실행 (비동기 작업) → `{job_id}` |
| GET | `/api/claims/{id}/process/status` | `{stage: classify\|extract\|review\|done, progress}` |
| POST | `/api/claims/{id}/submit` | 지급 심사로 보내기 (열린 이슈 0건일 때만) |

### 서류 · 항목
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/documents/{id}` | 서류 정보 + `fields[]` (값 · 신뢰도 · method · bbox) |
| GET | `/api/documents/{id}/image` | 원본 이미지 |
| PATCH | `/api/fields/{id}` | `{confirmed_value}` 직접 수정 → 이력 기록, 규칙 재검사 |
| GET | `/api/claims/{id}/normalized` | 정규화 결과 표 (표준 스키마 키 기준) |

### 이슈
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/claims/{id}/issues` | 이슈 목록 (`doc_ids`, `field_keys`, `evidence` 포함) |
| POST | `/api/issues/{id}/resolve` | 확인 완료 (담당자만) |

### 보완 요청
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/supplements` | 목록 |
| POST | `/api/claims/{id}/supplements` | 누락 이슈로 초안 생성 (Solar + 표준 문구) |
| PATCH | `/api/supplements/{id}` | 문구 · 채널 수정 |
| POST | `/api/supplements/{id}/send` | 모의 발송 → `sent_mock` (실제 발송 없음) |

### 이력 · 설정
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/claims/{id}/logs` | 검토 이력 |
| GET / PATCH | `/api/settings` | 자동 통과 기준 (PATCH는 관리자만) |
| GET / PUT | `/api/rules/required-docs` | 필수 서류 규칙 (PUT은 관리자만) |

### 챗봇
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/chat` | body `{conversation_id?, message, claim_id?}` → SSE 스트림. 마지막 이벤트에 `{citations[], actions[]}` |
| GET | `/api/conversations` | 대화 목록 |
| GET | `/api/conversations/{id}` | 대화 내용 |

#### 챗봇 응답 구조 (구조화 출력)
```json
{
  "answer": "김유정 고객 청구 1건을 찾았어요 ...",
  "citations": [{"n": 1, "doc": "보상 업무 매뉴얼", "article": "3.2", "text": "...", "is_mock": true}],
  "actions": [{"label": "보완 요청 작성", "href": "/workspace/supplements?claim=GA-2610-0482"}],
  "needs_choice": null
}
```

---

## 6. 챗봇 (LangGraph)

```
질문 → [의도 분류] ─┬─ policy_qa ──> RAG 검색(하이브리드) → 근거 있음? ─ 예 → 답변 + 인용
                    │                                         └ 아니오 → "관련 규정을 찾지 못했어요"
                    ├─ claim_check ─> 고객 찾기 → 동명이인? → 서류 · 이슈 조회 도구 → 요약 + 바로가기
                    ├─ item_coverage > 항목 조회 → 약관 대조(RAG) → "보상 제외 가능성" + 근거
                    └─ draft ───────> 표준 문구 검색 → 초안 생성
```

| 도구 | 설명 |
|---|---|
| `find_customer(name)` | 이름으로 청구 찾기 (권한 범위 안에서만) |
| `get_claim_documents(claim_id)` | 제출 · 필요 서류, 누락 |
| `get_claim_issues(claim_id)` | 불일치 · 확인 필요 |
| `get_items(claim_id, doc_type)` | 영수증 항목 |
| `search_kb(query, collection)` | 약관 · 매뉴얼 검색 |

안전장치: 근거 없으면 거절, 지급 판단 문구 금지, 조회 시 이력 기록.

**도구 호출 (Solar Tool Calling, docs/capabilities/generate/tool-calling)**
- `solar-pro4` Chat Completions의 `tools`(type function · name · description · JSON Schema parameters), `tool_choice: "auto"` 또는 특정 함수 강제, `parallel_tool_calls` 지원
- 흐름: 응답 `tool_calls` 확인 → 함수 이름 허용 목록 대조 → 인자 파싱 · 검증 → 실행 → `role: tool` 메시지(`tool_call_id`) 추가 → 재호출
- 구현 규칙
  - 모델이 낸 인자는 **항상 검증** (JSON 파싱 실패 · 허용되지 않은 키 · 범위 오류 처리)
  - **권한은 도구 안에서 서버가 판단**: `find_customer`는 로그인 사용자의 배정 범위 안에서만 검색 (모델 인자를 믿지 않음)
  - 병렬 호출이면 `tool_calls` **전부** 실행 후 재호출 (공식 예시처럼 [0]만 처리하지 않기)
  - 의도 분류처럼 정해진 도구가 있으면 `tool_choice`로 강제해 흔들림을 줄임
  - 스트리밍 중 도구 호출 처리는 문서에 없음 → 도구 단계는 비스트리밍, 최종 답변만 스트리밍


---

## 7. 설정 (`config.py`)

| 키 | 예시 | 설명 |
|---|---|---|
| `UPSTAGE_API_KEY` | `.env` | |
| `UPSTAGE_BASE_URL` | `https://api.upstage.ai/v2` | |
| `UPSTAGE_AGENT_ID` | `.env` | Studio 워크플로 ID |
| `SOLAR_CHAT_MODEL` | `solar-pro4` | |
| `SOLAR_EMBED_QUERY_MODEL` · `SOLAR_EMBED_PASSAGE_MODEL` | `solar-embedding-2-query` · `solar-embedding-2-passage` | 1,024차원 |
| `DB_URL` | `sqlite:///./data/gaon.db` | |
| `QDRANT_PATH` | `./data/qdrant` | 로컬 모드 |
| `AUTO_PASS_THRESHOLD` | `0.90` | settings 기본값 |
| `USE_CACHED_RESULTS` | `false` | 시연용 캐시 |
| `POLL_INTERVAL_SEC` · `POLL_TIMEOUT_SEC` | `2` · `120` | |
| `MAX_FILES_PER_CLAIM` | `10` | |
