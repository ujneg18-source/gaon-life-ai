/** 화면별 코치마크 정의. DOM 선택자와 설명을 한 곳에서 관리한다. */
export type TourStep = {
  target: string;
  title: string;
  description: string;
  detailStep?: number;
};
export const tours: Record<string, TourStep[]> = {
  home: [
    {
      target: "home-heading",
      title: "업무 시작하기",
      description:
        "약관과 업무 기준은 어시스턴트에서, 청구 서류 검토는 워크스페이스에서 시작하세요.",
    },
    {
      target: "home-workspace",
      title: "서류 검토 시작",
      description:
        "청구 검토함에서 보완 요청과 검토가 필요한 청구부터 살펴보세요.",
    },
    {
      target: "home-assistant",
      title: "업무 어시스턴트",
      description:
        "약관 조항이나 업무 기준을 질문하고 보완 요청 문구를 준비할 수 있어요.",
    },
  ],
  inbox: [
    {
      target: "inbox-table",
      title: "청구 상태 확인",
      description:
        "색과 아이콘, 상태 이름을 함께 확인하세요. 이름과 생년월일로 고객을 구분할 수 있어요.",
    },
    {
      target: "inbox-filters",
      title: "필요한 상태만 보기",
      description:
        "건수가 있는 상태만 표시해요. 탭을 선택하면 해당 청구만 볼 수 있어요.",
    },
    {
      target: "inbox-sort",
      title: "우선순위와 페이지",
      description:
        "보완 요청과 검토 필요가 먼저 나와요. 같은 우선순위에서는 최근 접수순이며 한 페이지에 10건을 보여줘요.",
    },
  ],
  detail: [
    {
      target: "detail-stepper",
      title: "네 단계로 검토",
      description: "서류 확인, 정보 대조, 검토 결과, 완료 순으로 진행하세요.",
      detailStep: 0,
    },
    {
      target: "detail-documents",
      title: "제출 서류와 접수 경로",
      description:
        "필요한 서류와 제출된 서류를 비교하세요. 실손24와 앱 업로드 출처를 구분해요.",
      detailStep: 0,
    },
    {
      target: "detail-compare",
      title: "서류 사이의 정보 대조",
      description:
        "일치한 항목도 함께 표시해요. 값을 누르면 원본 위치를 확인할 수 있어요.",
      detailStep: 1,
    },
    {
      target: "detail-summary",
      title: "검토 결과 요약",
      description:
        "확인할 건수, 누락 서류, 약관 대조를 간단히 확인하세요. 각 요약을 누르면 자세한 검토 화면으로 이동해요.",
      detailStep: 2,
    },
  ],
  workspace: [
    {
      target: "workspace-navigation",
      title: "워크스페이스 메뉴",
      description: "청구 검토, 보완 처리, 검토 이력을 선택하세요.",
    },
    {
      target: "workspace-search",
      title: "청구 찾기",
      description: "고객 이름, 청구번호, 증권번호로 검색할 수 있어요.",
    },
  ],
  review: [
    {
      target: "review-original",
      title: "원본 확인",
      description:
        "서류를 선택하고 항목 위치를 확인하세요. 확대와 축소는 직접 조절할 수 있어요.",
    },
    {
      target: "review-normalized",
      title: "추출된 서류 정보",
      description:
        "항목, 값, 출처, 신뢰도를 각각 확인하세요. 숫자 점수가 없으면 높음/낮음으로 표시하고, 실손24 정형 데이터는 대시로 표시해요.",
    },
    {
      target: "review-issues",
      title: "확인 사항과 안내",
      description:
        "원본과 비교한 뒤 확인 기록을 남기세요. 빠진 서류는 보완 요청으로 진행하세요.",
    },
  ],
  assistant: [
    {
      target: "assistant-body",
      title: "업무 질문 시작",
      description:
        "예시 질문을 선택하거나 질문을 입력하세요. 청구에서 들어왔다면 그 청구를 기준으로 확인해요.",
    },
    {
      target: "assistant-sources",
      title: "답변 근거 확인",
      description:
        "본문에서 사용한 약관과 업무 기준을 확인하세요. 가상 문서는 별도로 표시해요.",
    },
    {
      target: "assistant-actions",
      title: "해당 청구로 이동",
      description:
        "답변에 나온 확인 항목 링크를 누르면 해당 청구의 이슈로 이동해요. 아직 답변이 없다면 먼저 질문해 보세요.",
    },
    {
      target: "assistant-draft",
      title: "보완 요청 초안",
      description:
        "문구 작성을 요청하면 고객에게 보낼 초안이 나와요. 타이핑이 끝나면 수정하고 복사할 수 있어요.",
    },
  ],
};
