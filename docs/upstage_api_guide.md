# Upstage AI API 가이드 (가온생명 PoC용)

> 2026-10-15 기준으로 공식 문서(console.upstage.ai/docs)와 직접 테스트한 결과를 정리했다.
> **[실측]** = 우리가 직접 호출해서 확인한 것, **[문서]** = 공식 문서에 적힌 것, **[미확인]** = 아직 확인 못 한 것.
> 모델 버전 · 요금 · 제한은 바뀔 수 있으니 개발 시작 전에 콘솔에서 다시 확인한다.

---

## 목차
0. 시작하기 · 키 관리 · 공통 규칙
1. Document Parse (문서 → 구조화 텍스트 + 좌표)
2. Document OCR
3. Information Extract (문서 → 정해진 스키마 JSON)
4. Document Classify (서류 종류 분류)
5. Solar Chat (solar-pro4) · Structured Outputs · Tool Calling
6. Embeddings (Solar Embedding 2)
7. File Search (관리형 RAG, 베타)
8. Agents · Studio (v2)
9. LangChain 연동 (langchain-upstage)
10. 우리 PoC에서의 쓰임 정리
11. 실측 기록 · 자주 하는 실수

---

## 0. 시작하기 · 키 관리 · 공통 규칙

### 0-1. 가입과 키 발급 [문서][실측]
- 가입: https://console.upstage.ai → 오른쪽 위 `Log in`
- 가입 시 **무료 크레딧 $10** [문서]
- 키 발급: 콘솔 **API Keys** 페이지(`console.upstage.ai/api-keys`) → `Create new key`. 키는 `up_`로 시작
- **결제 수단 등록 필요** [실측]: 등록 전에는 Document Parse는 됐지만 Information Extract가 403
  `"API key suspended due to insufficient credit. Register your payment method at https://console.upstage.ai/billing"` 로 거부됐다. 등록 후 정상 호출.

### 0-2. 키 보안 (중요) [실측]
- 로그인한 상태로 콘솔 문서를 보면 **예제 코드에 내 실제 키가 자동으로 들어간다.** 키 페이지에서는 `up_****...fq2v`처럼 가려 보이지만 예제에는 전체가 들어 있다.
- 예제를 복사해서 채팅 · 이슈 · 깃허브에 붙이면 키가 노출된다 → **공유 전에 `api_key=` 줄을 지운다.**
- 노출되면 즉시 키 페이지에서 삭제 후 재발급.
- 키는 `.env`에만 둔다. `.env`는 `.gitignore`에 포함.

```bash
# upstage_demo/.env  (예시 — 실제 값은 절대 커밋하지 않는다)
UPSTAGE_API_KEY=<YOUR_API_KEY>      # 따옴표로 감싸도 됨 ("up_...")
UPSTAGE_BASE_URL=https://api.upstage.ai/v1
SOLAR_CHAT_MODEL=solar-pro4
SOLAR_EMBED_QUERY_MODEL=solar-embedding-2-query
SOLAR_EMBED_PASSAGE_MODEL=solar-embedding-2-passage
```

### 0-3. 설정은 한 곳에서 (pydantic-settings)
```python
# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env를 자동으로 읽는다 → load_dotenv() 호출 불필요
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    UPSTAGE_API_KEY: str                       # 없으면 서버 시작 시 바로 에러 (빈 키로 호출하는 사고 방지)
    UPSTAGE_BASE_URL: str = "https://api.upstage.ai/v1"
    SOLAR_CHAT_MODEL: str = "solar-pro4"
    SOLAR_EMBED_QUERY_MODEL: str = "solar-embedding-2-query"
    SOLAR_EMBED_PASSAGE_MODEL: str = "solar-embedding-2-passage"

settings = Settings()
```

### 0-4. 공통 규칙
| 항목 | 내용 |
|---|---|
| 기본 주소 | `https://api.upstage.ai/v1` (Agents · File Search · Responses는 `/v2`) |
| 인증 | 헤더 `Authorization: Bearer <API_KEY>` |
| SDK | 대부분 **OpenAI Python SDK에 `base_url`만 바꿔서** 호출 (`pip install openai`) |
| 데이터 보관 | "API로 전송된 데이터는 저장하거나 재사용하지 않는다" [문서] → 기획서 보안 근거 |
| 맥 기본 파이썬 경고 | `NotOpenSSLWarning (LibreSSL 2.8.3)` [실측] → 동작엔 문제 없음. 개발용 가상환경은 Python 3.13 권장 |

---

## 1. Document Parse

### 1-1. 무엇을 하나 [문서]
- 스캔 이미지 · PDF 등을 **LLM이 읽을 수 있는 구조(HTML / Markdown / text)** 로 바꾼다.
- 내부적으로 OCR을 쓰고, 그 위에 **레이아웃 분석 · 표 · 차트 이해**를 더한다 → OCR보다 상위 기능. 업스테이지 권장 방식.

### 1-2. 입력 조건 [문서]
| 항목 | 동기 API | 비동기 API |
|---|---|---|
| 최대 파일 크기 | 100MB | 500MB |
| 최대 페이지 | 100 | 2,000 |
| 초과 시 | 413 오류 | 접수 후 `failed`, 사유는 `failure_message` |

- 형식: 이미지 JPEG · PNG · BMP · TIFF · **HEIC**(아이폰 사진) · WEBP / 문서 PDF · DOC(X) · PPT(X) · XLS(X) · CSV · TSV · **HWP/HWPX**
- 해상도: 페이지당 최대 2억 픽셀 (문서 파일은 150 DPI로 변환해 계산)
- 문자: 알파벳 · 숫자 · **한글** · 가타카나 · 히라가나 지원, 한자는 베타
- **권장:** 너비 640px 이상, **가장 작은 글자가 이미지 높이의 2.5% 이상** (높이 640px이면 16px 이상)
  → 목업 서류를 만들 때 일부 서류만 이 기준 근처까지 흐리게 해서 "확인 필요" 사례를 만든다.

### 1-3. 요청 [문서][실측]
```python
import requests
from app.config import settings

def parse_document(path: str) -> dict:
    """서류 이미지/PDF 하나를 Document Parse로 읽는다."""
    with open(path, "rb") as f:
        r = requests.post(
            f"{settings.UPSTAGE_BASE_URL}/document-digitization",   # Parse 엔드포인트
            headers={"Authorization": f"Bearer {settings.UPSTAGE_API_KEY}"},
            files={"document": f},                                   # multipart 파일 필드 이름은 document
            data={
                "model": "document-parse",        # 실측 응답 model: document-parse-260930
                "ocr": "force",                   # 이미지가 아닌 PDF도 OCR을 강제 (스캔 서류 대비)
                # "base64_encoding": "['table']", # 표 영역을 이미지(base64)로도 받고 싶을 때 [문서 예제]
                # "merge_multipage_tables": "true", # 여러 페이지에 걸친 같은 구조 표 병합 (아래 1-5)
            },
            timeout=120,
        )
    r.raise_for_status()
    return r.json()
```

### 1-4. 응답 구조 [실측]
```jsonc
{
  "api": "...",
  "model": "document-parse-260930",
  "usage": {"pages": 1, "standard": [1]},       // 과금 페이지 수
  "content": { ... },                           // 문서 전체 내용
  "ocr": ...,
  "elements": [
    {
      "id": 0,
      "page": 1,
      "category": "header",                    // 실측 종류: header, paragraph, heading1, table
      "content": {
        "html": "<header id='0' style='font-size:18px'>가온생명 서류 검토 워크스페이스</header>",
        "markdown": "",                         // 기본 설정에서는 비어 있었음 (html만 채워짐)
        "text": ""
      },
      "coordinates": [                          // 꼭짓점 4개, 0~1 비율 (이미지 크기에 곱해서 픽셀로)
        {"x": 0.0426, "y": 0.0202}, {"x": 0.1987, "y": 0.0202},
        {"x": 0.1987, "y": 0.0447}, {"x": 0.0426, "y": 0.0447}
      ]
    }
  ]
}
```
- **짧은 값도 별도 요소로 잡힌다** [실측]: `질병분류기호` 라벨과 `C18.7` 값이 각각 다른 paragraph + 좌표로 나왔다. 직인이 겹쳐도 `C18.7`을 정확히 읽었다.
- **요소별 신뢰도는 없다** [실측].
- `markdown` · `text`가 필요하면 출력 형식 옵션을 지정해야 하는 것으로 보인다 [미확인: 옵션 이름은 레퍼런스에서 확인].

```python
import re

def element_text(el: dict) -> str:
    """요소의 html에서 태그를 지워 순수 텍스트만 꺼낸다 (기본 응답은 html만 채워짐)."""
    return " ".join(re.sub(r"<[^>]+>", " ", el["content"]["html"]).split())

def find_value_boxes(parse: dict, value: str) -> list[dict]:
    """Extract가 뽑은 값이 Parse 원문 어디에 있는지 찾는다.
    - 좌표 확보(Extract location이 없을 때의 대체 수단)
    - '원문에서 값을 찾았는가' 검증(확인 필요 판단 근거)에 쓴다."""
    return [
        {"page": el["page"], "coordinates": el["coordinates"]}
        for el in parse["elements"]
        if value and value in element_text(el)
    ]
```

### 1-5. 여러 페이지 표 병합 [문서]
- 파라미터 `merge_multipage_tables=true`: 페이지마다 끊긴 **같은 구조의 표**를 첫 번째 표 요소로 합친다.
- 세부내역서처럼 여러 장짜리 긴 표에 유용. 병합 후 요소 id가 바뀔 수 있으니 실제 응답을 확인하고 쓴다.

---

## 2. Document OCR [문서]
- 글자와 그 **위치**만 반환 (레이아웃 · 표 구조 없음).
- 우리 PoC에서는 기본적으로 안 쓴다. 위치는 Extract `location`(3-5) 또는 Parse 좌표로 충분하다.

| | OCR | Document Parse |
|---|---|---|
| 결과 | 글자 조각 + 위치 | 제목 · 문단 · 표가 구분된 HTML/Markdown + 요소 좌표 |
| 표 | 칸이 깨져 직접 맞춰야 함 | 행 · 열 유지 |
| 용도 | 단어 위치만 필요할 때 | LLM 입력, 추출의 기반 |

---

## 3. Information Extract

### 3-1. 무엇을 하나 [문서]
- 문서 이미지/PDF를 넣고 **"이 모양으로 채워줘"라는 JSON Schema**를 주면 그 틀에 맞춘 값을 돌려준다. (Pydantic 모델을 LLM 구조화 출력에 넘기는 것과 같은 감각)
- 템플릿 · 재학습 없이 여러 양식에 쓴다.

### 3-2. 기본 호출 [문서][실측]
```python
import base64, json
from openai import OpenAI
from app.config import settings

# Extract는 base_url이 기능별로 다르다
ie_client = OpenAI(
    api_key=settings.UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1/information-extraction",
)

def to_data_url(path: str) -> str:
    """파일을 base64 data URL로. 문서 예제는 MIME을 application/octet-stream으로 보낸다."""
    with open(path, "rb") as f:
        return "data:application/octet-stream;base64," + base64.b64encode(f.read()).decode()

schema = {
    "type": "object",
    "properties": {
        "diagnosis_code": {"type": "string", "description": "질병분류기호 (KCD 코드, 예: C18.7)"},
        "diagnosis_date": {"type": "string", "description": "진단일 YYYY-MM-DD"},
    },
}

resp = ie_client.chat.completions.create(
    model="information-extract",                       # 실측 응답 model: information-extract-260904
    messages=[{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": to_data_url("diagnosis.png")}},
    ]}],
    response_format={"type": "json_schema",
                     "json_schema": {"name": "diagnosis", "schema": schema}},
)
data = json.loads(resp.choices[0].message.content)   # 결과는 문자열 → 파싱
```
- **[실측] 결과:** `{"diagnosis_code": "C18.7", "diagnosis_date": "2026-09-18"}`
  화면에는 `2026.09.18`이었는데 description에 적은 `YYYY-MM-DD`로 바꿔서 돌려줬다 → **description에 원하는 형식을 쓰면 정규화 일부를 해 준다.**
- 응답은 OpenAI `chat.completion` 형식 (`id`, `choices[0].message.content`, `usage.prompt_tokens` 등).
- requests로 직접 부를 때 주소: `POST https://api.upstage.ai/v1/information-extraction/chat/completions` [실측]

### 3-3. 스키마 작성 규칙 [문서]
| 규칙 | 내용 |
|---|---|
| 루트 | 반드시 `object` |
| 타입 | string · number · integer · boolean · array · object |
| **1단계 속성** | string · integer · number · **array만** (1단계에 object 불가) |
| array | `items` 필수. **array 안에 array 불가** |
| 표 | `array` of `object`로 표현 (예: 세부내역서 항목) |
| 이름 길이 | 모든 속성 · 정의 이름 합계 10,000자 이하 |
| 동기 API | object 속성 최대 100개, 총 15,000자 |
| 비동기 API | object 속성 최대 5,000개, 총 120,000자 |
| 팁 | 키 이름과 description을 명확하게. 모호한 일반 이름 피하기 |

```python
# 세부내역서 예시: 1단계는 원시값/배열만, 표는 array of object
detail_schema = {
    "type": "object",
    "properties": {
        "patient_name":   {"type": "string",  "description": "환자 성명"},
        "period_start":   {"type": "string",  "description": "진료 시작일 YYYY-MM-DD"},
        "period_end":     {"type": "string",  "description": "진료 종료일 YYYY-MM-DD"},
        "inpatient_days": {"type": "integer", "description": "입원 일수"},
        "items": {                                   # 표 → 객체 배열 (배열 안 배열은 금지)
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name":     {"type": "string",  "description": "항목명 (예: 진찰료, 수술료)"},
                    "category": {"type": "string",  "description": "분류 (진찰, 검사, 수술, 약제 등)"},
                    "covered":  {"type": "boolean", "description": "급여 항목이면 true"},
                    "amount":   {"type": "integer", "description": "금액(원), 숫자만"},
                },
            },
        },
    },
}
```

### 3-4. 신뢰도 `confidence` [문서]
- `extra_body={"confidence": True}`
- 결과: 필드마다 **`high` / `low`** 두 단계 (숫자 아님)
- 위치: `choices[0].message.tool_calls` 중 함수 이름 `additional_values`의 `arguments` (JSON 문자열) → 필드마다 `_value`와 신뢰도
- 의미: 모델의 **주관적** 판단. 정확도를 보장하지 않는다 → 사람 확인 흐름(Human-in-the-Loop)의 보조 기준으로 쓴다.

### 3-5. 위치 좌표 `location` [문서]
- `extra_body={"location": True, "location_granularity": "word"}`
- `location_granularity`: `element`(기본, 칸 · 문단 단위, 빠름) · `word`(단어 단위, 정밀, 조금 느림) · `all`(둘 다)
- 결과: 같은 `additional_values` → 필드마다 `_value`, `page`, `coordinates`(element) / `word_coordinates`(word)
- 좌표: 0~1 비율, 꼭짓점 4개 `{x, y}` (Parse와 같은 형식)

```python
resp = ie_client.chat.completions.create(
    model="information-extract",
    messages=[{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": to_data_url("diagnosis.png")}},
    ]}],
    response_format={"type": "json_schema", "json_schema": {"name": "diagnosis", "schema": schema}},
    extra_body={                       # OpenAI SDK에 없는 업스테이지 전용 옵션은 extra_body로
        "confidence": True,            # 필드별 high/low
        "location": True,              # 필드별 좌표
        "location_granularity": "word" # 원본 하이라이트용으로 단어 단위
    },
)
msg = resp.choices[0].message
values = json.loads(msg.content)                       # 기본 추출값
extras = {}
for tc in msg.tool_calls or []:
    if tc.function.name == "additional_values":        # 신뢰도 · 좌표가 여기에 담긴다
        extras = json.loads(tc.function.arguments)
# [미확인] confidence + location 동시 사용 시 extras의 정확한 키 구조 → test_upstage.py 2차 실행으로 확인
```
> requests로 보낼 때는 `extra_body` 대신 요청 JSON 최상위에 `"confidence": true` 등을 그대로 넣는다 (OpenAI SDK가 extra_body를 본문에 합쳐 보내는 것과 같음).

### 3-6. 분할 `split` [문서]
- `extra_body={"split": True}`: **같은 유형** 서류 여러 건이 한 파일에 있으면 건별로 나눠 `choices[]`에 하나씩 반환.
- 기준은 스키마 구조의 반복 (예: `invoice_number` 같은 건별 고유값이 있으면 건수만큼 분리).
- 최소 단위는 **페이지** (한 페이지에 영수증 2장이면 못 나눈다).
- **서로 다른 종류**가 섞였으면 Extract 분할이 아니라 **Document Classify**를 쓴다.

### 3-7. 스키마 자동 생성 [문서]
- Schema Generation API: 샘플 파일 **최대 3개** → 초기 스키마 생성. 결과는 message content의 문자열 JSON.
- 시스템 메시지로 의도 전달 (예: "Generate schema about bank_name.")
- 레퍼런스: https://console.upstage.ai/ko/api/information-extraction/universal-information-extraction/schema-generation
- 사용법: 목업 서류가 나오면 이걸로 초안을 만든 뒤 **표준 스키마 키 이름으로 다듬는다.**

### 3-8. 비동기 Extract [문서]
| 항목 | 내용 |
|---|---|
| 생성 | `POST /v1/information-extraction/async` → `job_id` 즉시 반환 |
| 조회 | `GET .../jobs/{job_id}` (5~10초 간격 폴링), 목록 `GET .../jobs` (limit/offset) |
| 상태 | CREATED · IN_PROGRESS · PARTIALLY_COMPLETED · COMPLETED · FAILED · CANCELED |
| 제한 | 작업당 문서 20개, 최대 1,000페이지, 파일 50MB, 속성 5,000개 |
| 옵션 | confidence · location 지원 |

- **데모 결정:** 서류 1장 = 동기 1회 (단순 · 디버깅 쉬움). "청구 1건 = 비동기 작업 1개"는 실제 도입 시 확장안.

---

## 4. Document Classify [문서]
- 미리 정한 카테고리로 서류를 분류. 분류 목록을 JSON Schema의 **`oneOf` + `const` + `description`** 으로 넘긴다.
  (주의: Solar Chat 구조화 출력은 `oneOf`를 지원하지 않는다. Classify는 예외로 이 형식을 쓴다.)

```python
cls_client = OpenAI(api_key=settings.UPSTAGE_API_KEY,
                    base_url="https://api.upstage.ai/v1/document-classification")

DOC_CLASSES = [  # const = 우리 서류 유형 코드(03_data_design 2장), description = 판별 힌트
    {"const": "diagnosis",        "description": "진단서. 병명, 질병분류기호(KCD), 진단일, 담당의 서명"},
    {"const": "pathology",        "description": "병리조직검사 결과지. 검체, 병리 진단(예: Adenocarcinoma), 보고일"},
    {"const": "admission",        "description": "입퇴원확인서. 입원일, 퇴원일, 입원 일수"},
    {"const": "surgery_cert",     "description": "수술확인서. 수술명, 수술일, 수술 코드"},
    {"const": "medical_receipt",  "description": "진료비 계산서·영수증(법정 서식). 급여/비급여, 본인부담금"},
    {"const": "medical_detail",   "description": "진료비 세부내역서. 항목별 코드, 단가, 횟수, 금액 표"},
    {"const": "pharmacy_receipt", "description": "약제비 영수증. 약국 발행, 조제료, 약품비"},
    {"const": "others",           "description": "위에 해당하지 않는 서류"},
]

resp = cls_client.chat.completions.create(
    model="document-classify",
    messages=[{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": to_data_url("unknown.png")}},
    ]}],
    response_format={"type": "json_schema", "json_schema": {
        "name": "document-classify",
        "schema": {"type": "string", "oneOf": DOC_CLASSES},
    }},
)
doc_type = resp.choices[0].message.content   # [미확인] 반환 형식(문자열 그대로인지, 신뢰도 포함인지)
```
- [미확인] 최대 카테고리 수, 분류 신뢰도 제공 여부, 섞인 파일 분할 규칙의 파라미터 이름.

---

## 5. Solar Chat (solar-pro4)

### 5-1. 기본 · 추론 [문서]
```python
chat = OpenAI(api_key=settings.UPSTAGE_API_KEY, base_url="https://api.upstage.ai/v1")

resp = chat.chat.completions.create(
    model="solar-pro4",
    messages=[{"role": "user", "content": "..."}],
    reasoning_effort="medium",        # 추론 강도 조절
)
msg = resp.choices[0].message
reasoning = getattr(msg, "reasoning", None)   # 추론 과정이 오면 여기에 (없을 수 있음)
answer = msg.content
```
- Responses API(`/v2/responses`)는 Solar Pro 4 · Solar Mini 4에서 사용 가능.

### 5-2. Structured Outputs (구조화 출력) [문서]
- `response_format={"type":"json_schema", "json_schema":{...}}` → 스키마를 지킨 JSON 문자열
- JSON mode(`{"type":"json_object"}`)는 유효한 JSON만 보장(스키마 미보장), 프롬프트에 "JSON" 단어가 없으면 400

| 규칙 | 내용 |
|---|---|
| 루트 | object |
| required | **모든 속성을 required에 넣는다** |
| 선택 값 | 키는 유지하고 타입에 null 추가 `"type": ["string", "null"]` |
| strict | `true` |
| additionalProperties | 모든 object에서 `false` |
| 중첩 | 최대 10단계, `$defs` + 로컬 `$ref`만 |
| 미지원 (400) | `allOf` · `oneOf` · `not` · `dependentRequired` · `dependentSchemas` · `if/then/else` · `patternProperties` · 재귀 `$ref` |
| 권장 | 중첩 `anyOf` 피하고 `enum` / nullable 사용 |

```python
# 챗봇 답변 형식 (04_system_design 5장)
answer_schema = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "citations": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "n": {"type": "integer"},
                "doc": {"type": "string"},
                "article": {"type": "string"},
                "text": {"type": "string"},
                "is_mock": {"type": "boolean"},
            },
            "required": ["n", "doc", "article", "text", "is_mock"],
            "additionalProperties": False,
        }},
        "actions": {"type": "array", "items": {
            "type": "object",
            "properties": {"label": {"type": "string"}, "href": {"type": "string"}},
            "required": ["label", "href"],
            "additionalProperties": False,
        }},
        "needs_choice": {"type": ["array", "null"], "items": {"type": "string"}},  # 동명이인 선택지, 없으면 null
    },
    "required": ["answer", "citations", "actions", "needs_choice"],
    "additionalProperties": False,
}

resp = chat.chat.completions.create(
    model="solar-pro4",
    messages=messages,
    response_format={"type": "json_schema",
                     "json_schema": {"name": "answer", "strict": True, "schema": answer_schema}},
)
choice = resp.choices[0]
if choice.finish_reason == "length":      # 토큰 한도로 잘림 → max_tokens 늘려 재시도
    raise RuntimeError("응답이 잘렸어요")
result = json.loads(choice.message.content)   # stop일 때만 파싱
```
- 스트리밍 시 `delta.content` 조각을 **모두 모은 뒤** 파싱 (SSE는 `data: [DONE]`으로 끝남)
- "스키마를 지켰다고 값이 믿을 만한 건 아니다" → 도메인 검증 · 권한 확인은 우리 코드에서 [문서]

#### Pydantic → 업스테이지용 스키마 변환
Pydantic `model_json_schema()`는 Optional을 `anyOf`로, 날짜를 `format`으로 내보내 규칙과 어긋난다 → 변환 함수를 둔다.
```python
# backend/app/schemas/to_upstage.py (뼈대)
def to_upstage_chat_schema(schema: dict) -> dict:
    """Solar 구조화 출력 규칙에 맞게 바꾼다.
    1) 모든 properties를 required로
    2) anyOf[{type: X}, {type: null}] → type: [X, "null"]
    3) 모든 object에 additionalProperties: false
    4) format/pattern 등 미지원 가능 키워드 제거(검증은 Pydantic이 따로 함)"""
    ...
```
> Information Extract는 다른 규칙(3-3)을 따른다. 실측에서 `required` 없이도 동작했다. 서류 스키마는 3-3 규칙으로 따로 만든다.

### 5-3. Tool Calling (도구 호출) [문서]
```python
tools = [{
    "type": "function",
    "function": {
        "name": "find_customer",
        "description": "고객 이름으로 청구 건을 찾는다 (로그인 담당자의 배정 범위 안에서만)",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "고객 이름"}},
            "required": ["name"],
            "additionalProperties": False,
        },
    },
}]

resp = chat.chat.completions.create(
    model="solar-pro4", messages=messages, tools=tools,
    tool_choice="auto",               # 특정 함수 강제: {"type":"function","function":{"name":"find_customer"}}
    parallel_tool_calls=True,         # 한 번에 여러 도구 호출 허용
)
msg = resp.choices[0].message
if msg.tool_calls:
    messages.append(msg)                                   # 1) 어시스턴트 메시지를 히스토리에
    for tc in msg.tool_calls:                              # 2) 병렬이면 전부 실행 (공식 예시처럼 [0]만 처리하지 말 것)
        if tc.function.name not in ALLOWED_TOOLS:          # 3) 허용 목록 대조
            continue
        try:
            args = json.loads(tc.function.arguments)       # 4) 모델 JSON이 깨질 수 있음 → 에러 처리
        except json.JSONDecodeError:
            args = None
        result = run_tool(tc.function.name, args, user=current_user)  # 5) 권한은 서버가 판단
        messages.append({"role": "tool", "tool_call_id": tc.id,
                         "name": tc.function.name, "content": json.dumps(result, ensure_ascii=False)})
    resp = chat.chat.completions.create(model="solar-pro4", messages=messages, tools=tools)  # 6) 재호출
```
- strict 옵션 · 스트리밍 중 도구 호출은 문서에 없음 → **도구 단계는 비스트리밍, 최종 답변만 스트리밍**
- Responses API에서는 `output`의 `function_call` → 실행 → `function_call_output`(call_id, output)을 입력에 추가해 재호출

---

## 6. Embeddings (Solar Embedding 2) [문서]
| 항목 | 내용 |
|---|---|
| 모델 | `solar-embedding-2-query`(질문 · 검색어) / `solar-embedding-2-passage`(문서 · 조각) — **별칭 없음, 전체 이름** |
| 차원 | 1,024 |
| 입력 | 8k 컨텍스트 |
| 배치 | 요청당 텍스트 100개, 총 204,800토큰 |
| 한도 | RPM 100, TPM 300,000 |
| 벡터 | 길이 1로 정규화 → **내적 = 코사인 유사도** |
| 기반 | microsoft/harrier-oss-v1-0.6b 파인튜닝 [문서 기재] |
| 종료 예정 | Solar Embedding 1(`embedding-query`/`embedding-passage` 별칭)은 2026-12-31 종료 |

```python
def embed_passages(texts: list[str]) -> list[list[float]]:
    """약관 조각 임베딩. 100개씩 끊어서 배치 호출."""
    out = []
    for i in range(0, len(texts), 100):
        r = chat.embeddings.create(model=settings.SOLAR_EMBED_PASSAGE_MODEL, input=texts[i:i+100])
        out += [d.embedding for d in r.data]
    return out

def embed_query(q: str) -> list[float]:
    """사용자 질문은 query 모델로 (passage 모델과 섞지 않는다)."""
    return chat.embeddings.create(model=settings.SOLAR_EMBED_QUERY_MODEL, input=q).data[0].embedding
```

```python
# Qdrant 로컬 모드 (서버 없이 파일로 저장)
from qdrant_client import QdrantClient, models
qc = QdrantClient(path="./data/qdrant")
qc.recreate_collection("policy", vectors_config=models.VectorParams(
    size=1024, distance=models.Distance.DOT))   # 정규화 벡터라 DOT = COSINE
```

---

## 7. File Search (관리형 RAG, 베타) [문서]
- 흐름: Files API 업로드(`file_id`) → `POST /v2/vector_stores` → `POST /v2/vector_stores/{id}/files` (배치는 `file_batches`, 50개) → 상태 폴링(`completed`/`failed`) → `POST /v2/vector_stores/{id}/search` → `POST /v2/responses`에 `file_search` 도구 + `vector_store_ids`
- 형식: PDF · DOCX · PPTX · XLSX · HWP/HWPX · MD · TXT, 이미지 JPEG · PNG · BMP · TIFF · HEIC (모두 Parse로 텍스트화 후 인덱싱)
- 청킹: **`auto`만** (조정 불가). 메타데이터 필터 · 하이브리드 설명 없음
- 결과: 일치 텍스트, 관련도 점수, 출처 파일
- 제한: 사용자당 벡터 스토어 50개, 스토어당 파일 500개, `max_num_results` 1~20(기본 5)
- 배치 완료 판단: `status`가 아니라 `file_counts.in_progress == 0`, 실패는 `file_counts.failed`
- **베타 기간 민감 · 기밀 데이터 업로드 금지 안내**
- **우리 결정:** 본 구현은 Qdrant + Solar Embedding 2 + BM25(조항 단위). File Search는 **평가 비교군**(선택).

---

## 8. Agents · Studio (v2)
- **Studio** [문서·관찰]: 콘솔에서 노드(Parse · Classify · Extract · Instruct, 라이브러리 예시엔 Merge · Validate도 표시)를 이어 문서 처리 흐름을 만드는 화면. 결과물은 에이전트 ID `agt_...`
- **라이브러리 보험 예시** [관찰]:
  - 보험금 지급 심사 자동화 패키지: Parse → Classify(7종) → Extract(7종), 페이지당 예상 $0.04 — https://studio.upstage.ai/library/agt_mnm8A9CTafEUjK9V4MKc54
  - 언더라이팅 고지의무 · 건강검진 리스크 판정: Parse → Classify → Extract ×4 → Merge → Validate(Green/Yellow/Red) → Instruct, 페이지당 예상 $0.06 — https://studio.upstage.ai/library/agt_5Za3XWQaZGF9inyCFMsmCw
  - 그 밖에 보험금 청구 문서 세트 자동 처리, 자동차 정비견적 교차검증, 불완전판매 사전점검
- **Agents API** [업스테이지 확장 허브 소개 페이지 기준, 미실측]: 기본 주소 `https://api.upstage.ai/v2`
  - `POST /v2/files` 업로드 → `POST /v2/responses` 실행 → `GET /v2/responses/{id}` 결과 (agt_ 에이전트는 백그라운드 실행 → 폴링)
  - `POST /v2/agents`, `POST /v2/agents/{id}/configs`로 코드에서 흐름 정의 가능, Config는 불변(바꾸면 새로 생성)
- **우리 결정(제안):** 백엔드는 기능별 v1 직접 호출(스키마를 Pydantic 한 곳에서 관리), Studio는 흐름 설계 · 튜닝 · 시연용

---

## 9. LangChain 연동 (langchain-upstage) [문서 예제]
```python
# pip install -qU langchain-core langchain-upstage
from langchain_upstage import UpstageDocumentParseLoader

loader = UpstageDocumentParseLoader("diagnosis.png", ocr="force")   # 키는 환경변수 UPSTAGE_API_KEY
pages = loader.load()          # 또는 lazy_load()
```
- LangGraph 챗봇에서 Solar 채팅 · 임베딩을 LangChain 방식으로 쓸 수 있다 (`ChatUpstage`, `UpstageEmbeddings` 등 — [미확인] 클래스 이름은 패키지 문서로 확인)
- LangChain `with_structured_output`은 구조화 출력 문자열을 객체로 파싱해 준다 [문서]

---

## 10. 우리 PoC에서의 쓰임

| 단계 | API | 옵션 / 설정 | 비고 |
|---|---|---|---|
| 서류 분류 | Document Classify | `oneOf` 7종 + others | 섞인 파일 분할은 Classify |
| 원문 읽기 | Document Parse | `ocr=force`, (세부내역서) `merge_multipage_tables` | 원문 대조 · 좌표 대체 |
| 값 추출 | Information Extract | 서류별 스키마(3-3 규칙), `confidence`, `location`(word) | description에 형식 명시 |
| 확인 필요 판단 | 우리 코드 | Extract `low` 또는 원문 미발견 또는 형식 오류 또는 교차검증 실패 | 화면은 높음/낮음 + 이유 |
| 원본 하이라이트 | Extract `location` | 없으면 Parse 요소 매칭 | 0~1 좌표 × 이미지 크기 |
| 챗봇 | Solar Chat `solar-pro4` | 도구 호출 + 구조화 출력 | 근거 없으면 거절 |
| RAG | Solar Embedding 2 + Qdrant + BM25 | query/passage 구분, DOT | 조항 단위 |
| 보완 문구 | Solar Chat | 표준 문구 근거 | 단정 금지 |

---

## 11. 실측 기록 · 자주 하는 실수

### 실측 (2026-10-15, `backend/scripts/test_upstage.py`, 입력: 프로토타입 화면 캡처 1장)
| 호출 | 결과 |
|---|---|
| Document Parse | 200, 요소 36개(header 2 · paragraph 31 · heading1 1 · table 2), 좌표 있음, 1페이지 과금 |
| Information Extract (결제 수단 등록 전) | 403 `api_key_is_not_allowed` (크레딧 부족) |
| Information Extract (등록 후) | 200, `{"diagnosis_code":"C18.7","diagnosis_date":"2026-09-18"}`, 기본 옵션에선 신뢰도 · 좌표 없음 |
| Extract + confidence + location(word) | [미확인] 2차 실행 예정 |

### 자주 하는 실수
1. 문서 예제를 복사하다 **실제 키를 공유** → 공유 전 `api_key=` 줄 삭제
2. 결제 수단 미등록 → Extract 403
3. Extract 1단계 속성에 object 사용 → 스키마 오류. 표는 array of object
4. 질문을 passage 모델로 임베딩 → 검색 품질 저하
5. 구조화 출력에서 `finish_reason` 확인 없이 파싱 → 잘린 JSON
6. 병렬 도구 호출에서 첫 번째만 처리
7. Classify 스키마(`oneOf`)를 Solar Chat에 그대로 사용 → 400
8. `.env` 값에 따옴표 → 직접 파싱하면 따옴표가 남음 (pydantic-settings는 처리)

### 참고 링크
- 시작하기: https://console.upstage.ai/ko/docs/getting-started
- Parse: https://console.upstage.ai/ko/docs/capabilities/parse · 입력 요구사항 `/parse/input-requirements` · 표 병합 `/parse/merge-multipage-table` · 출력 이해 `/parse/understanding-output` · 대용량 `/parse/handling-large-documents` · OCR `/parse/document-ocr`
- Extract: 스키마 `/extract/writing-a-schema` · 범용 `/extract/universal-extraction` · 신뢰도 `/extract/confidence` · 좌표 `/extract/location-coordinates` · 분할 `/extract/document-split` · 비동기 `/extract/universal-extraction-async`
- Chat: 구조화 출력 `/generate/structured-outputs` · 도구 호출 `/generate/tool-calling`
- Embed: `/capabilities/embed` · File Search: `/search/file-search`
- (모두 `https://console.upstage.ai/ko/docs/capabilities` 아래)
