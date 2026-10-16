# polish-1 검증과 롤백 (2026-10-16)

## 6건 결과
1. 빈 청구는 엔진을 호출하지 않고 처리 전(pending)으로 둔다. 기존 잘못된 자동 누락 이슈는 이력을 보존하며 해소한다. 상태 고정값은 시드에서 제거했다. 실제 로컬 데이터는 처리 전 12건 / 보완 요청 1건, 김유정은 제출 7 / 필요 8 · 기존 이슈 5건이다. 여러 처리 결과를 갖는 서류 세트는 T-06 범위로 남긴다.
2. 가상 고객 10명의 생일과 청구 13건의 접수 시각은 중복 패턴을 제거했다. 동명이인·고객/계약 관계는 유지한다. 화면은 날짜 YYYY.MM.DD, 시각 포함 YYYY.MM.DD HH:mm. 기존 접수 시각의 한국 현지시간과 UTC 감사 이력을 구분했다.
3. 어시스턴트 버튼은 본문 뒤의 정상 레이아웃에 둬 스크롤 중에도 표를 덮지 않는다. 마지막 행과 버튼 영역의 겹침 없음 확인.
4. 담당자용 문구로 변경하고 필드/서류의 내부 코드를 한글 이름으로 표시한다. 검증 방식의 한계는 코드 주석에 보존했다.
5. 비교 진입 시 두 문서를 같은 100%로 표시하고 각각 대상 칸을 가운데로 이동한다. 자동 300% 확대는 사용자 추가 요청으로 제거했다. 두 칸의 박스를 강조한다. 확대/축소는 공유한다. 실손24는 제공된 대응 가상 서식 이미지의 SHA-256이 일치할 때만 검증한 서식 위치를 표시하며, AI 추출 좌표로 기록하지 않는다. 다른 서식에 고정 위치를 적용하지 않는다.
6. 문서/비교 대상이 바뀌면 정규화 표의 스크롤 컨테이너를 새로 만들어 scrollTop=0에서 시작한다. 머리글은 고정하고 첫 행이 머리글 아래에 완전히 보이는지 확인했다.

## 검증
- 백엔드: pytest 43 passed / live 1 제외, Ruff 통과.
- 프론트: lint · typecheck · format:check · build 통과.
- 날짜 함수: Node test 1 passed (생일, 접수 시각, UTC 이력의 날짜 경계 포함).
- 브라우저: 처리 전 필터 12행 / 김유정 제외, 김유정 접수 2026.10.15 09:12, 비교 두 칸 모두 영역 안에 표시, 문서 전환 후 표 scrollTop=0 및 첫 행 안 잘림, 마지막 행/버튼 겹침 없음.
- 실제 Upstage 호출 없음. 캐시/원본/최초 추출값/신뢰도는 수정하지 않았다.

## 캡처
- `artifacts/polish-1/before/`: inbox.jpg, inbox-bottom.jpg, compare.jpg, review-table.jpg
- `artifacts/polish-1/after/`: inbox.jpg, inbox-pending.jpg, inbox-bottom.jpg, compare.jpg, compare-focused.jpg, review-table.jpg
- `after/*-check.json`: 실제 DOM에서 읽은 비교 칸 가시성·확대율, 표 첫 행 위치, 마지막 행/버튼 겹침 여부.
- 비교 캡처는 내부 스크롤 위치를 보존하는 viewport 캡처다. 전체 페이지 캡처는 캡처 도구가 내부 스크롤을 초기화하므로 초점 검증에 사용하지 않았다.

## 롤백
롤백 기준 태그: `ui-v1-before-polish` → `550a95e` (원격에도 저장됨).

디자인만 되돌리기: 데이터·상태·시드 커밋은 유지하고 다음 명령으로 별도 화면 커밋만 취소한다.

```bash
git revert $(git log --format=%H --grep='^polish-1: 화면' -1)
```

수정 전 전체 상태를 로컬에서 복원하려면 백엔드/프론트 서버를 종료하고 프로젝트 루트에서 실행한다. main의 이력은 그대로 두고 복원 브랜치를 만든다.

```bash
git switch -c rollback/ui-v1 ui-v1-before-polish
cp data/ui-v1-before-polish.db data/gaon.db
```

그다음 해당 브랜치의 프론트를 다시 빌드하고 서버를 실행한다. 태그는 Git 코드만 보관하므로 pending 상태를 모르는 이전 백엔드로 돌아갈 때 DB도 함께 복원해야 한다. `data/ui-v1-before-polish.db`는 로컬 전용이며 Git에 포함하지 않았다.

## 추가 요청 반영: 기본 비율 복원 (2026-10-16)
- 자동 확대만 제거했다. 비교 버튼/이슈 URL 직접 진입 모두 100%이며, 대상 칸 이동·강조와 두 서류 공유 수동 확대/축소는 유지한다.
- lint · typecheck · format:check · build 통과. 브라우저에서 버튼/직접 진입 100%, 강조 2개, 수동 100→120→100 및 이미지 원래 종횡비 유지를 확인했다.
- 최신 캡처: `after/compare-default-100.jpg`, `after/compare-manual-zoom.jpg`. 검증: `after/compare-default-100-check.json`. 기존 300% 캡처는 이전 작업 기록이다.
