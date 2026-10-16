# GPT 이미지: 고객별 사진 버전 계획

실제 사진 생성은 사용자가 GPT 이미지에서 진행합니다. 깨끗한 PNG와 정답은 덮어쓰지 않습니다.

## 고객 10명과 사진 대상

| 고객 ID | 고객 · 사례 | 사진 대상 |
|---|---|---|
| DEMO-C001 | 김유정 · 기존 복합 청구 | 01_diagnosis, 02_pathology, 03_admission (3장) |
| DEMO-C002 | 이가온 · 완결 서류 | 없음 · 깨끗한 PNG/실손24 유지 |
| DEMO-C003 | 박가람 · 갑상선 소액암 | 없음 · 깨끗한 PNG/실손24 유지 |
| DEMO-C004 | 최새봄 · 90일 면책 기간 | 없음 · 깨끗한 PNG/실손24 유지 |
| DEMO-C005 | 정다온 · 실손24 통원·약제비 | 없음 · 깨끗한 PNG/실손24 유지 |
| DEMO-C006 | 한누리 · 처방전 미기재 일반의약품 | 07_pharmacy_receipt (1장) |
| DEMO-C007 | 김서연 · 질병분류기호 누락 | 없음 · 깨끗한 PNG/실손24 유지 |
| DEMO-C008 | 김서연 · 환자 이름 불일치 | 없음 · 깨끗한 PNG/실손24 유지 |
| DEMO-C009 | 윤가온 · 입원 2일 차이 | 없음 · 깨끗한 PNG/실손24 유지 |
| DEMO-C010 | 서지우 · 서류 미제출 | 없음 · 깨끗한 PNG/실손24 유지 |

## 파일 이름과 위치

- 김유정: `data/samples/kim_yujeong/photo/01_diagnosis.jpg`, `02_pathology.jpg`, `03_admission.jpg`
- 한누리(6번): `data/samples/han_nuri/photo/07_pharmacy_receipt.jpg`
- 그 외에도 폴더 구조는 `<sample_id>/photo/`로 통일합니다. `photo/README.md`가 자리 표시자입니다.
- 원본 PNG와 같은 stem, 확장자는 jpg/jpeg/png 중 하나만 사용합니다. 같은 stem의 사진이 두 장이면 오류로 중단합니다.
- --use-photo는 사진이 있는 앱 서류만 교체하고 없는 장은 png/로 돌아갑니다. 실손24는 JSON을 유지합니다.

## 한 장씩 입력할 프롬프트

```text
첨부한 가상 서류를 출력해 밝은 회색 책상 위에 놓고 스마트폰으로 촬영한 사진처럼 바꿔 주세요.
모든 글자, 숫자, 이름, 날짜, 금액, 표, 선, 도장, SAMPLE · 가상 데이터 표시를 한 글자도 바꾸거나 지우거나 추가하지 마세요.
서류 배치와 표 위치도 유지해 주세요. 새 로고/번호/QR/주소/전화번호는 추가하지 마세요.
사진 효과만: 가벼운 구김, 약한 실내 조명 그림자, 5도 이내 촬영 각도. 글자는 읽을 수 있게 유지해 주세요.
```

진단서는 가벼운 흔들림, 병리 결과지는 왼쪽 위 얕은 그림자, 입퇴원확인서는 한 번 접은 자국, 약제비 영수증은 약한 원근만 각각 하나씩 추가할 수 있습니다.

## 확인·사용

```bash
cd backend
uv run python -m scripts.samples.gen_claim --customer DEMO-C001 --use-photo
uv run python -m verify_samples --folder data/samples/kim_yujeong --use-photo
uv run python -m scripts.seed --demo --use-photo
```

기본 verify는 mock 기반 규칙 검증이라 사진 속 글자 변경/OCR 정확도를 증명하지 않습니다. 사진의 글자는 먼저 눈으로 대조하고, 사진 OCR을 측정할 때만 별도 예산 범위에서 --live 또는 --cached로 검증합니다. 신규 실제 호출 허용 고객은 김유정·완결 건·6번이며, 이번 작업에서는 새 사진 실측을 하지 않습니다. 결과는 artifacts/t06/<id>/photo/에 분리하고 photo_count로 실제 사진 사용 수를 남깁니다.
