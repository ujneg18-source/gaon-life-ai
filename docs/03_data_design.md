# 03. 데이터 설계

| 항목 | 내용 |
|---|---|
| 버전 | v1.0 (2026-10-15) |
| DB | SQLite + SQLModel (데모). 벡터 DB는 Qdrant 로컬 모드 |
| 원칙 | 표준 스키마 키는 영문 snake_case, 화면 표시는 한글 라벨 |

---

## 1. 테이블 구조 (ERD 요약)

```
customers ─< policies ─< claims
customers ──────────────< claims
users ─┬─< claims ─┬─< documents ──< fields
       │           ├─< issues
       │           ├─< supplement_requests
       │           └─< audit_logs
       └─< audit_logs
settings (1행) · required_doc_rules · cross_check_rules · kcd_codes · drug_catalog
```

### users
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| email | str | `reviewer@gaon.demo` 등 |
| name | str | 표시 이름 |
| role | enum | `reviewer` · `admin` |

### customers
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | str PK | 가상 고객 식별자 DEMO-C001. 이름으로 식별하지 않음 |
| name | str | 가상 이름, 동명이인 허용 |
| birth_date | date | 가상 생년월일 |
| contact | str | 000 시작의 명백한 가상 연락처 |
| is_mock | bool | 데모 데이터 표시 |

### policies
| 컬럼 | 타입 | 설명 |
|---|---|---|
| policy_no | str PK | 증권번호 |
| customer_id | FK customers.id | 계약 고객 |
| product_name | str | 가상 상품명 |
| riders | JSON list | 가입 특약 코드 목록 |
| contract_date | date 또는 null | 실제 계약일. 90일 면책 비교의 기준이며 보장 기간과 분리 |
| coverage_start / coverage_end | date | 보장 시작·종료일, 양 끝 날짜 포함 |
| is_mock | bool | 가상 계약 표시 |

### claims
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | str PK | 청구번호 `GA-YYMM-NNNN` |
| customer_id | FK customers.id | 고객 참조. 기존 DB 전환 중에만 null 허용 |
| customer_name | str | 접수 당시 가상 고객명 스냅샷 |
| policy_no | FK policies.policy_no | 증권번호 `L-YYYY-NNNNNN` |
| claim_types | json list | `cancer_diagnosis` · `hospitalization` · `surgery` · `medical_expense` 등 |
| received_at | datetime | 접수 일시 |
| reported_start / reported_end | date 또는 null | 앱 접수 진료 기간. 문서 기간이 아직 없을 때 CV-06의 선언된 입력으로 사용 |
| channel | json list | `app` · `silson24` |
| status | enum | `pending` · `processing` · `auto_pass` · `needs_review` · `supplement` · `to_payment_review` |
| assignee_id | int FK users | 배정 담당자 |
| step | int | 상세 화면 진행 단계 0~3 |

### documents
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| claim_id | str FK | |
| doc_type | enum | 아래 "서류 유형 코드" |
| source | enum | `image` (앱 업로드) · `silson24` (전자 데이터) |
| file_path | str | 원본 파일 경로 (silson24는 JSON 경로) |
| classify_conf | float | 분류 신뢰도 |
| page_size | json | 원본 이미지 크기 (하이라이트 좌표 계산용) |
| status | enum | `uploaded` · `parsed` · `extracted` · `failed` |
| provenance | str | `upstage` · `mock` · `silson24` · `unprocessed`. 검증 방식이며 인물/계약이 실제라는 뜻이 아님 |
| raw_result | json | Upstage 응답 원본 (디버깅용) |

### fields (추출 항목)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| document_id | int FK | |
| key | str | 표준 스키마 키 (예: `diagnosis_date`) |
| value | str | 정규화된 값 |
| raw_value | str | 추출 원문 |
| extract_conf | enum \| null | Extract 신뢰도 `high` · `low` (실손24 데이터는 null) |
| source_found | bool | Parse 원문에서 값이 발견됐는지 |
| review_reasons | json list | 확인 필요 이유 `low_conf` · `not_in_source` · `format` |
| method | enum | `parse` · `ocr` · `data` |
| page | int | 페이지 |
| bbox | json \| null | 꼭짓점 4개 `[{x,y}...]` 0~1 비율 (Extract location `word`, 없으면 Parse 매칭) |
| confirmed_value | str \| null | 담당자 확정값 |
| confirmed_by | int \| null | |

### issues
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| claim_id | str FK | |
| kind | enum | `info` (안내, 차단하지 않음) · `missing` (누락) · `mismatch` (불일치) · `low_conf` (확인 필요) · `excluded_item` (보상 제외 가능성) · `format` (형식 오류) |
| rule_id | str | 발생시킨 규칙 ID (예: `CV-01`) |
| title | str | 화면 제목 |
| detail | str | 설명 한 줄 |
| doc_ids | json list | 관련 서류 (원본 비교용, 최대 2) |
| field_keys | json list | 강조할 항목 키 |
| evidence | json list | 근거 조항 `[{source, article, text}]` (약관 대조) |
| status | enum | `open` · `resolved` |
| resolved_by / resolved_at | | |

### supplement_requests
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| claim_id | str FK | |
| doc_types | json list | 요청 서류 |
| channel | enum | `kakao` (알림톡) · `sms` |
| message | text | 안내 문구 |
| status | enum | `draft` · `sent_mock` (회신 대기) · `received` |

### audit_logs
| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | int PK | |
| claim_id | str \| null | |
| actor_type | enum | `customer` · `ai` · `user` |
| actor_id | int \| null | |
| action | str | `view` · `upload` · `process_done` · `field_edit` · `issue_resolve` · `supplement_send` · `setting_change` |
| detail | json | 수정 전후 값 등 |
| created_at | datetime | |

### settings
| 키 | 기본값 | 설명 |
|---|---|---|
| review_on_low_conf | true | Extract 신뢰도 low면 확인 필요 |
| review_on_not_in_source | true | Parse 원문에 값이 없으면 확인 필요 |

---

## 2. 서류 유형 코드

| 코드 | 서류 | Tier |
|---|---|---|
| `diagnosis` | 진단서 | 1 |
| `pathology` | 조직검사(병리) 결과지 | 1 |
| `admission` | 입퇴원확인서 | 1 |
| `surgery_cert` | 수술확인서 | 1 |
| `medical_receipt` | 진료비 영수증 (실손24) | 1 |
| `medical_detail` | 진료비 세부내역서 (실손24) | 1 |
| `prescription` | 처방전 (실손24) | 1 |
| `outpatient` | 통원확인서 | 2 |
| `pharmacy_receipt` | 약제비 영수증 | 2 |
| `imaging_report` | 영상 판독지 | 2 |
| `disability` | 후유장해 진단서 | 2 |
| `death_cert` | 사망진단서 · 시체검안서 | 2 |
| `claim_form` | 보험금 청구서 | 2 |
| `id_copy` · `bankbook` · `family_cert` · `basic_cert` · `poa` · `seal_cert` · `consent` · `accident_report` · `accident_statement` · `medical_record` | Tier 3 서류 | 3 |
| `other` | 기타 | — |

---

## 3. 표준 스키마 (Tier 1 · 2 추출 항목)

공통: `patient_name` (환자 이름), `issuer` (발행 기관), `issued_date` (발행일)

| 서류 | 키 | 라벨 | 형식 |
|---|---|---|---|
| 진단서 | `diagnosis_code` | 질병분류기호 | KCD `^[A-Z]\d{2}(\.\d{1,2})?$` |
| | `diagnosis_name` | 병명 | 문자열 |
| | `diagnosis_date` | 진단일 | `YYYY-MM-DD` |
| | `onset_date` | 발병일 | `YYYY-MM-DD` |
| 조직검사 결과지 | `pathology_result` | 병리 진단 | 문자열 |
| | `specimen` | 검체 | 문자열 |
| | `report_date` | 보고일 | `YYYY-MM-DD` |
| 입퇴원확인서 | `admit_date` · `discharge_date` | 입원일 · 퇴원일 | `YYYY-MM-DD` |
| | `stay_days` | 입원 일수 | 정수 |
| | `diagnosis_code` | 질병분류기호 | KCD |
| 수술확인서 | `surgery_name` · `surgery_date` · `surgery_code` | 수술명 · 수술일 · 수술 코드 | |
| 진료비 영수증 · 세부내역서 | `period_start` · `period_end` | 진료 기간 | `YYYY-MM-DD` |
| | `inpatient_days` | 입원 일수 | 정수 |
| | `covered_copay` · `non_covered` · `total` | 급여 본인부담 · 비급여 · 합계 | 정수(원) |
| | `items[]` | 항목 목록 `{name, code, category, covered, amount}` | |
| 약제비 영수증 · 처방전 | `items[]` | `{drug_name, days, amount, covered}` | |
| 통원확인서 | `visit_dates[]` | 통원일 | |
| 후유장해 진단서 | `disability_part` · `disability_rate` | 장해 부위 · 지급률 | |
| 보험금 청구서 | `claim_types` · `accident_date` · `bank_name` | 청구 종류 · 사고일 · 은행 | 계좌번호는 마스킹 |

- 실손24 데이터는 이미 정형이므로 같은 키로 바로 매핑한다 (`method = data`).
- Pydantic 모델로 정의해 추출 결과를 검증한다. 검증 실패 → `format` 이슈.

```python
class DiagnosisDoc(BaseModel):
    patient_name: str
    diagnosis_code: Annotated[str, Field(pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$")]
    diagnosis_name: str
    diagnosis_date: date
    onset_date: date | None = None
```

---

## 4. 규칙

### 4-1. 청구 유형별 필수 서류 (`required_doc_rules`)
| 청구 유형 | 필수 서류 | 조건부 |
|---|---|---|
| 암 진단금 `cancer_diagnosis` | 진단서, 조직검사 결과지 | |
| 입원일당 `hospitalization` | 입퇴원확인서 | |
| 수술비 `surgery` | 수술확인서 | 세부내역서에 수술 행위가 있으면 자동 추가 (CV-04) |
| 실손 `medical_expense` | 진료비 영수증, 세부내역서 | 약제비 청구 시 약제비 영수증 · 처방전 |
| 통원일당 `outpatient` | 통원확인서 | |
| 후유장해 `disability` | 후유장해 진단서 | |
| 사망보험금 `death` | 사망진단서, 가족관계증명서, 기본증명서 | |
| 공통 | 보험금 청구서, 신분증 사본 | 대리 청구 시 위임장 · 인감증명서. **데모 가정: 앱 청구는 앱 입력 · 본인인증으로 대체해 면제** |

### 4-2. 교차검증 (`cross_check_rules`)
| ID | 규칙 | 비교 | 이슈 |
|---|---|---|---|
| CV-01 | 진단일 ≥ 병리 보고일 | 진단서 `diagnosis_date` ↔ 결과지 `report_date` | mismatch |
| CV-02 | 입원 기간 일치 | 일수 1일 차이는 info, 2일 이상/명시 입퇴원일 차이는 mismatch. 진료비 산정 기간과 입퇴원일은 구분 | info / mismatch |
| CV-03 | 질병코드와 병리 진단 부합 | 진단서 `diagnosis_code` ↔ 결과지 `pathology_result` (KCD 명칭 비교) | mismatch |
| CV-04 | 수술 행위 → 수술확인서 필요 | 세부내역서 `items[].category == surgery` | missing |
| CV-05 | 환자 이름 일치 | 모든 서류 `patient_name` | mismatch |
| CV-06 | 진료 기간이 증권 보장 기간 안 | 세부내역서 기간 ↔ 계약 정보 | mismatch |

### 4-3. 약관 대조 (`excluded_item`)
- 대상: 영수증 · 세부내역서 · 약제비 영수증의 `items[]`
- 방법: 항목 이름 → `drug_catalog`(샘플 분류표)로 분류 → 약관 "보상하지 않는 사항" 조항을 RAG로 검색 → 해당 시 이슈 생성 + `evidence`에 조항
- 표현: "보상 제외 가능성이 있어요. 확인해 주세요" (단정 금지)

### 4-4. 신뢰도 라우팅
1. Extract 신뢰도 `low` 또는 원문 미발견 또는 형식 오류 → `low_conf` 이슈 (이유를 `review_reasons`에 기록)
2. 규칙 위반 → 신뢰도와 무관하게 이슈
3. 열린 이슈 0건 → `auto_pass` · 누락 이슈 있음 → `supplement` · 그 외 → `needs_review`

---

## 5. 참조 데이터

| 테이블 | 내용 | 출처 |
|---|---|---|
| `kcd_codes` | 질병코드 → 공식 명칭 (데모에 쓰는 코드만) | 한국표준질병·사인분류(KCD). 적용 차수는 개발 시 통계청 고시로 확인 |
| `drug_catalog` | 약 이름 → 분류 (치료제 / 영양제 등) | 데모용 샘플 표. 실제 도입 시 의약품 공공데이터 필요 |

---

## 6. 지식 베이스 (RAG)

| 컬렉션 | 문서 | 조각 단위 | payload |
|---|---|---|---|
| `policy` | 금감원 공개 표준약관(생명보험 · 질병상해 · 실손) + 가온생명 가상 특약 | 조 · 항 단위 | `doc_name, edition, article, title, is_mock` |
| `manual` | 가상 보상 업무 매뉴얼, 보완 요청 표준 문구 | 절 단위 | 같음 |

- 검색: 벡터(Solar Embedding) + 키워드(BM25) 하이브리드
- 가상 문서는 `is_mock: true`로 표시하고 화면에도 "가상 문서"로 보여준다.

---

## 7. 시연 데이터 (김유정 고객, 가상)

| 항목 | 값 |
|---|---|
| 청구번호 | GA-2610-0482 |
| 청구 유형 | 암 진단금 · 입원일당 · 실손 |
| 질병코드 | C18.7 구불결장의 악성 신생물 |
| 제출 (7) | 앱: 진단서, 조직검사 결과지, 입퇴원확인서, 약제비 영수증 / 실손24: 진료비 영수증, 세부내역서, 처방전 |
| 필요 (8) | 위 7종 + 수술확인서 (CV-04로 추가) |
| 심어 둔 문제 | CV-01 진단일 역전, CV-02 입원 1일 차이, CV-04 수술확인서 누락, 질병코드 직인 겹침(저신뢰), 약제비 영수증 영양제 1건(약관 대조) |


## 고객·계약 시드 및 CV-06 구현 (T-02b)
- 고객 10명·계약 10개·청구 13건. 김서연 동명이인은 서로 다른 ID·생년월일로 구분한다. 복수 청구 고객이 있다.
- 김유정 기존 청구의 이름·증권번호·문서·이슈·진행 단계는 보존하며 고객·계약 FK만 연결한다.
- GA-2610-0438은 접수 진료기간 2026-09-22~09-30, 보장 시작 2026-10-01로 CV-06 확인 필요를 만든다. 문서가 있으면 문서의 실제 period_start/end 또는 admit/discharge를 우선 대조한다.
- GA-2610-0433은 수술비 청구에 surgery 특약이 없어 POLICY-RIDER 확인 필요를 만든다. 지급 거절을 자동 결정하지 않는다.
- CV-06은 진료 시작이 보장 시작 전이거나 종료가 보장 종료 후일 때 mismatch를 남긴다. 동일 시작·종료일은 범위 안이다. 형식 오류는 별도 format 규칙에 맡긴다.
- SQLite 기존 claims는 트랜잭션 안에서 FK를 추가해 재구성하며 자식 문서·이력 ID를 보존하고 foreign_key_check를 수행한다. 기본 시드는 증분이며 --demo에서만 초기화한다.

## T-05~T-06 고객별 서류 세트 (2026-10-16)
- 단일 원본: `data/samples/customers.json`. 고객10명·계약10개·청구13건(대표10건+기존 복수청구3건), 원본 입력·검증 허용 방식·기대 이슈를 함께 관리한다. `data/seed/demo.json`은 규칙만 보관한다.
- `gen_claim --customer <id>`는 공통 A4 HTML/정답을 생성하고 변경된 HTML만 PNG로 렌더링한다. 기존 김유정7장은 해시/좌표 보존을 위해 재캡처하지 않는다. `gen_kim_yujeong.py`는 호환 진입점이다.
- `seed --demo`는 기존 행을 초기화하고 29장과 실제 규칙 결과를 적재한다. 상태 고정값은 사용하지 않는다. 기본 seed는 기존 데이터 보존용 고객·규칙 시드이며 새 API 호출은 없다.
- 이가온(C002), 한누리(C006)는 새 실제 검증 허용 대상이다. 김유정(C001)은 기존 캐시만 재사용한다. 캐시 없는 환경에서는 모의 입력으로 대체하고 실제 API로 표기하지 않는다. 나머지 고객은 정답 기반 mock, 실손24는 구조화 모의 JSON이다.
- 화면의 `development_origin`은 SHOW_DEVELOPMENT_BADGES 설정으로 숨길 수 있다. DB provenance는 유지하고 mock 필드의 출처를 실제 OCR/실손24로 꾸미지 않는다.
- 소액암 C73: 가상 암진단특약 제2조·제4조의 20% 기준을 `POLICY-C73` info로 안내한다. 지급액 계산은 하지 않는다.
- 계약일+90일 전 암 진단: `CV-06-WAIT` info, C73 소액암은 해당 특약 예외. 날짜는 `contract_date`로만 계산하고 정보가 없으면 추정하지 않는다. 보장 기간 밖 진료의 CV-06 mismatch는 그대로다.
- 진단서 질병분류기호 누락: format+REQ-diagnosis-code missing으로 보완 요청한다. 코드가 없는 상태에서 CV-03 부합 여부는 추정하지 않는다.
- 처방전에 없는 비급여 일반의약품: 제출된 처방전과 명칭/분류를 대조하고 동일 KB 원문의 제4조·매뉴얼6장 근거를 `coverage` excluded_item에 저장한다. 처방전이 없으면 부재를 단정하지 않는다.
- 전자 통합 약제비 3종 경로: 실손24 영수증·세부내역·처방전이 모두 전자로 들어오고 별도 약제비 영수증이 없는 데모 경로는 처방전만 필수에 추가한다. 앱 업로드 약제비에는 기존 영수증+처방전 규칙을 유지한다. 본인인증 후 앱 접수라는 가정이다.
- `info`만 있는 청구는 서류 확인 완료 상태다. 실제 지급 심사는 별도이며, 인박스에서는 안내 확인과 이관 가능(열린 이슈 없음)을 구분한다.
- 수술확인서는 `kim_yujeong/supplement/`의 별도 회신용이다. 업로드 시 기존 추출/확정값을 보존하고 신규 서류만 처리한다. CV-04 해소 후 보완 요청은 received, 남은 과제가 있으면 needs_review다.
- `--use-photo`는 존재하는 사진만 골라 쓰고 없는 장은 PNG로 돌아간다. 사진이 같은 stem에 두 개면 중단한다. 결과는 png/photo별로 분리하고 실제 photo_count를 기록한다.
