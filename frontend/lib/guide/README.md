# 독립 온보딩 데이터

- `/guide/{home,assistant,inbox,detail,review,supplement,history}`에서만 사용하는 가상 예시다. 메뉴에는 노출하지 않으며 로그인과 noindex를 적용한다.
- 원래 화면의 `?`는 가이드라인/업무 어시스턴트/데이터 출처 메뉴를 연다. 가이드라인을 선택하면 해당 페이지의 안내를 iframe으로 연다. 종료하면 iframe만 제거하므로 원래 검색어, 대화, 입력, 문서 배율과 선택 항목을 보존한다.
- 실제 화면 컴포넌트와 CSS를 재사용한다. `GuideContext`가 읽기 전용 응답을 제공하고 `api()`는 안내 경로의 모든 실제 요청을 차단한다. 파일 업로드와 검토함 복원 저장소도 별도로 격리한다.
- `snapshot.json`은 2026.10.16의 가상 시드 13건, 김유정 서류7/필수8, 원문 좌표/실제 저장된 추출 점수와 시연 답변의 고정 복사본이다. 업무 DB를 초기화하거나 실제 청구 상태가 바뀌어도 설명 예시는 그대로 유지된다. 성능 평가셋이 아니다.
- 답변 원문/근거는 `artifacts/t18/ui-final/demo_answers.json`의 첫 답변을 재사용했다. 원문과 평가 기록은 변경하지 않았다. 예시 질문은 업무 리스트 요청으로 표시하며 LLM을 새로 호출하지 않는다.
- 원본은 `frontend/public/guide-documents/`의 가상 서류 이미지 복사본이다. `/api/documents/.../image`를 호출하지 않는다.
- 보완 문자는 `artifacts/final-workflow/supplement-letter.txt`를 재사용했다. 모의 발송 예시는 안내 안에서만 표시하며 발송/접수 API는 실행하지 않는다. 실제 고객의 회신 문자를 꾸미지 않는다.
- 문구/순서는 `lib/tours.ts`, 격리 경계는 `context.tsx`, 응답은 `data.ts`, 화면 진행은 `components/guide-player.tsx`에 있다.
- 검증: `node scripts/check-onboarding.mjs`; 화면 캡처와 단계별 검수는 `artifacts/onboarding/`.

- 안내 iframe은 글꼴과 말풍선 배치가 준비됐다는 동일 출처 메시지를 확인한 후 페이드로 표시한다. 중간 로딩 화면을 노출하지 않으며 reduced-motion에서는 전환 효과를 생략한다.
