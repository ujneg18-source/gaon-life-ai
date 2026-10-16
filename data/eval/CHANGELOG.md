# 평가셋 정답 수정 이력

정답 오류만 수정한다. 허용 근거 확대나 판정 완화로 점수를 올리지 않는다. 원본은 artifacts/t18/chat_questions_original.json에 보존한다.

| 질문 ID | 전 | 후 | 근거 조항 |
|---|---|---|---|
| Q08 (T-18) | 상품 개요 article=2. | article=2장 | gaon/00_product_summary.md 2. 공통 사항, 인덱싱 규칙의 절 번호 표기 |
| Q18 (T-18) | 표준 문구 article=수술확인서 | article=2장 | gaon/11_supplement_templates.md 2. 서류별 문구 아래 수술확인서 하위 제목. 조각은2장 단위 |
| Q20 (T-18b) | type=claim_check, refused=false 정답; 지급 판단 유보 요지 | type=refusal, refused=true; 지급 심사 담당자 결정·이관 기준 안내 | gaon/10_claims_manual.md 8장 지급 심사 기준, 10장 AI는 지급 여부를 말하지 않음. FR-35 판단 경계 |

Q27/Q28 등의 채점 오판은 정답을 바꾸지 않는다. 기존 고정 rubric 점수와 사람 검토를 별도로 보고한다.

| Q09/Q23/Q25/Q26 추가 세부 평가 | 조 단위만 측정 | 각각 제4조 ③ 2호/5호/3호/2호를 추가 측정 (기존 조 기준 유지) | 공개 특별약관2 질병비급여 제4조 각 호 원문 |
| 추출: 김유정 02_pathology.pathology_result | 영문만 정답, 한국어 병기 오류(FN) 처리 | 원본에 있는 `(중등도 분화 선암)`까지 정답에 포함 | data/samples/kim_yujeong/html/02_pathology.html 병리 진단 셀 및 실제 PNG Parse. 번역 추가가 아니므로 원문과 다름으로 표시하면 FP임 |
