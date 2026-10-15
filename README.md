# upstage_demo — 가온생명 청구 서류 검수 PoC

> 가상의 생명보험사 **가온생명**이 Upstage Document AI를 도입한다고 가정하고,
> 서류 한 장이 아니라 **청구 한 건** 단위로 분류 · 정규화 · 누락/불일치 검출 · 검수까지 이어지는 PoC.

## 한 줄 포지션
Document AI가 뽑은 결과 **위에 얹는 청구 단위 검수 레이어**. (OCR 자체를 새로 만드는 게 아님)

## 역할 분담
| 누가 | 무엇을 |
|---|---|
| 진영 + Claude | 기획: 근거 정리, 요구사항정의서, 설계, 화면, 평가 계획, 작업 티켓 |
| GPT-Codex | 대규모 구현: 티켓 단위 개발 (`AGENTS.md` 참고) |

## 진행 순서 (기획 → 개발)
| 단계 | 산출물 | 파일 | 상태 |
|---|---|---|---|
| 0. 근거 정리 | 문제정의 근거, 출처 | `docs/00_background.md` | 초안 완료 |
| 1. 범위 확정 | 대상 사용자, 청구 유형, 서류 Tier | `docs/01_scope.md` | 초안 |
| 2. 요구사항정의서 | 기능/비기능 요구사항, 우선순위, 수용 기준 | `docs/02_requirements.md` | 뼈대 |
| 3. 데이터 설계 | 표준 스키마, 서류별 필드, 필수서류 룰, 교차검증 룰 | `docs/03_data_design.md` | 뼈대 |
| 4. 시스템 설계 | 파이프라인, Upstage API 매핑, 기술 스택, API | `docs/04_system_design.md` | 뼈대 |
| 5. 화면 설계 | 검수 콘솔, 대기열, 보완 요청 | `docs/05_ui_design.md` + `design/` | 목업 1장 있음 |
| 6. 샘플 · 평가 계획 | 가상 서류 제작, 정답셋, 지표 | `docs/06_eval_plan.md` | 뼈대 |
| 7. 개발 티켓 | Codex에 넘길 작업 단위 | `docs/07_tickets.md` | 미착수 |
| 8. 개발 · 시연 | 동작하는 데모, 시연 시나리오 | `src/` | 미착수 |

## 산출물 목록
| 산출물 | 파일 | 형식 |
|---|---|---|
| 기획서 | `docs/deliverables/01_기획서.md` | md → 나중에 docx |
| 요구사항정의서 | `docs/02_requirements.md` | md (표) |
| 화면설계서 | `docs/05_ui_design.md` + `design/` | md + 캡처 |
| 시스템 아키텍처 | `docs/04_system_design.md` + `design/diagrams/` | HTML로 그려서 캡처 |
| 데이터 설계 (ERD · 스키마) | `docs/03_data_design.md` | md + 캡처 |
| Upstage API 가이드 | `docs/upstage_api_guide.md` | md (예제 코드 · 실측) |
| API 명세 | `docs/04_system_design.md` | md |
| WBS · 일정 | `docs/deliverables/WBS.md` | md |
| 테스트 계획 · 결과 | `docs/06_eval_plan.md` | md |
| 시연 시나리오 | `docs/deliverables/시연시나리오.md` | md |

### 문서 규칙
- 모든 문서는 md로 먼저 쓰고, 최종본만 docx로 옮긴다.
- 그림(아키텍처, 흐름도, ERD, 화면)은 **항상 HTML로 만들고 캡처해서 PNG로 쓴다.** 원본 HTML은 `design/diagrams/`에 보관.

할 일 체크리스트는 `TODO.md`, 결정 기록은 `docs/decisions.md`, 작업 기록은 `docs/WORKLOG.md`.

## 폴더 구조
```
upstage_demo/
├── README.md            # 지금 이 파일: 개요 + 진행 순서
├── TODO.md              # 단계별 체크리스트
├── AGENTS.md            # Codex용 작업 규칙 · 컨텍스트
├── .env.example         # API 키 자리 (실제 키는 .env, 커밋 금지)
├── docs/                # 기획 문서 (00~07 + decisions)
├── design/              # 화면 목업 캡처 · 링크
├── data/
│   ├── samples/         # 가상 서류 이미지 (실제 개인정보 절대 금지)
│   └── mock_silson24/   # 실손24 전송 데이터 모의 JSON
└── src/                 # 개발 시작 시 생성
```
