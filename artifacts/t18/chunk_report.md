# 구조 기반 청킹 보고서

호/항을 검색하고 별도 JSON 부모 항을 확장한다. 길이로 단서 문장을 자르지 않는다.

| 문서 | 수 | 최소 | 중앙 | p95 | 최대 |
|---|---:|---:|---:|---:|---:|
| data/kb/gaon/00_product_summary.md | 15 | 74 | 103 | 200 | 200 |
| data/kb/gaon/01_cancer_rider.md | 23 | 52 | 84 | 126 | 238 |
| data/kb/gaon/02_hospitalization_rider.md | 11 | 37 | 70 | 170 | 170 |
| data/kb/gaon/03_surgery_rider.md | 9 | 37 | 65 | 143 | 143 |
| data/kb/gaon/04_outpatient_rider.md | 5 | 37 | 41 | 133 | 133 |
| data/kb/gaon/10_claims_manual.md | 32 | 77 | 123.0 | 296 | 307 |
| data/kb/gaon/11_supplement_templates.md | 3 | 94 | 234 | 986 | 986 |
| data/kb/policy/std_illness_injury.txt | 199 | 38 | 169 | 1383 | 5207 |
| data/kb/policy/std_life_insurance.txt | 186 | 38 | 161.0 | 1383 | 5207 |
| data/kb/policy/std_silson_basic.txt | 263 | 45 | 187 | 1013 | 2269 |
| data/kb/policy/std_silson_rider1_severe_noncovered.txt | 124 | 52 | 166.5 | 986 | 2653 |
| data/kb/policy/std_silson_rider2_nonsevere_noncovered.txt | 135 | 62 | 154 | 689 | 2643 |

전체 1005개 / 노드 1698개 / 정의 용어 19개.

영양제 원문은 상해③2·질병③2·MRI④2 세 곳에 있다. 각각 별도 주소로 보존한다.

부표를 마지막 제43조에 붙이지 않고 별도 경계로 분리한다. 원문 개정 이력의 동일 번호는 revision/occurrence 주소로 보존한다.

부모·목 원문: KB_STRUCTURE_PATH (기본 data/cache/kb_nodes.json). API 키·reference 원문은 포함하지 않는다.
