# 지식 베이스 (챗봇 RAG 원천)

챗봇(T-15~T-17)이 근거로 쓰는 문서 모음. **공개 문서**와 **가상 문서**를 구분해서 관리한다.

## 폴더
```
data/kb/
├── policy/                         # 공개 문서 (is_mock=false)
│   ├── [별표 15] 표준약관(...).hwp  # 원문: 금융감독원 「보험업감독업무시행세칙」 [별표15], 2026.8.28. 개정
│   ├── std_life_insurance.txt                  # 생명보험 표준약관 (원문에서 텍스트 추출)
│   ├── std_illness_injury.txt                  # 질병·상해보험 표준약관(손해보험 회사용)
│   ├── std_silson_basic.txt                    # 기본형 실손의료보험(급여)
│   ├── std_silson_rider1_severe_noncovered.txt # 실손 특별약관1(중증 비급여)
│   └── std_silson_rider2_nonsevere_noncovered.txt # 실손 특별약관2(비중증 비급여)
├── gaon/                           # 가온생명 가상 문서 (is_mock=true)
│   ├── 00_product_summary.md       # 상품 구성 · 특약 코드 · 공통 사항
│   ├── 01_cancer_rider.md          # 암진단특약
│   ├── 02_hospitalization_rider.md # 질병입원일당특약
│   ├── 03_surgery_rider.md         # 질병수술비특약
│   ├── 04_outpatient_rider.md      # 질병통원일당특약
│   ├── 10_claims_manual.md         # 보상 업무 매뉴얼 (필수 서류 · 교차검증 · 실손 비급여 확인)
│   └── 11_supplement_templates.md  # 보완 요청 표준 문구
└── reference/                      # 참고용 실제 회사 약관 — git 제외 (.gitignore), 지식 베이스에 넣지 않음
```

## 인덱싱 규칙 (T-15)
| 컬렉션 | 문서 | 조각 단위 | payload |
|---|---|---|---|
| `policy` | `policy/std_*.txt`, `gaon/00~04` | **조(제N조) 단위**, 조가 길면 항(①②) 단위 | `doc_name, edition, article, title, is_mock, source_path` |
| `manual` | `gaon/10~11` | **절(## 제목) 단위** | 같음 |

- 표준약관 원문은 HWP다. Upstage Document Parse가 HWP를 지원하므로, 시연용으로 **필요한 부분만** Parse로 처리해 txt 추출본과 비교해도 된다 (전체 HWP는 페이지가 많아 크레딧 주의). 기본 인덱싱 입력은 `std_*.txt`.
- 가상 문서는 답변 · 근거 패널에 "가상 문서"로 표시한다.
- `reference/`는 형식 참고용이다. 인덱싱하지 않고 커밋하지 않는다.

## 문서와 엔진 규칙의 연결
| 엔진 규칙 | 근거 문서 |
|---|---|
| 필수 서류 규칙 | `10_claims_manual.md` 2장, 각 특약 "보험금의 청구" 조 |
| CV-01 진단일 vs 병리 보고일 | `01_cancer_rider.md` 제3조 ③, 매뉴얼 4장 |
| CV-02 입원 일수 (1일 차이 허용 기준) | `02_hospitalization_rider.md` 제5조, 매뉴얼 4장 |
| CV-04 수술확인서 | `03_surgery_rider.md` 제5조 |
| 원문과 다름(세분류 누락) | `01_cancer_rider.md` 제2조 ④, 매뉴얼 3장 · 5장 |
| 약관 대조(영양제) | `std_silson_rider2_...txt` 제4조 ③ 제2호, 매뉴얼 6장 |
| 보완 요청 문구 | `11_supplement_templates.md` |
