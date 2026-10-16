/** 페이지마다 독립 실행하며 설명과 강조 영역은 짧고 명확한 단위로 묶는다. */
export type TourStep = {
  target: string;
  title: string;
  description: string;
  stage?: string;
  detailStep?: number;
};
export const tours: Record<string, TourStep[]> = {
  home: [
    {
      target: "home-heading",
      title: "안녕하세요. 가온생명 AI입니다",
      description:
        "청구 서류 확인과 약관 검색을 돕는 데모예요.\n가상 자료로 구성했으며, 지급 판단은 담당자가 해요.",
    },
    {
      target: "home-assistant",
      title: "궁금한 업무는 대화로 물어보세요",
      description:
        "약관과 업무 기준을 찾고,\n고객의 확인할 일과 안내 문구를 정리해 드려요.",
    },
    {
      target: "home-workspace",
      title: "청구 서류를 한곳에서 검토하세요",
      description:
        "제출 서류와 누락·불일치를 확인해요.\n보완 요청부터 지급 심사 이관까지 이어갈 수 있어요.",
    },
    {
      target: "guide-help",
      title: "언제든 다시 확인하세요",
      description: "궁금할 땐 언제든 ?를 눌러 주세요.",
    },
  ],
  assistant: [
    {
      target: "assistant-intro",
      title: "업무 어시스턴트와 함께 확인해요",
      description:
        "약관, 업무 절차, 고객의 청구 건을 물어보세요.\n김유정 고객의 저장된 예시로 살펴볼게요.",
    },
    {
      target: "assistant-new-chat",
      title: "다른 업무는 새 채팅에서 시작해요",
      description:
        "새 주제나 다른 고객을 확인할 때 눌러 주세요.\n현재 대화는 새로고침하거나 재로그인하면 비워져요.",
    },
    {
      target: "assistant-input",
      title: "평소 말하듯 질문해 주세요",
      description:
        "고객명이나 청구번호를 함께 적으면 좋아요.\nEnter로 보내고, Shift+Enter로 줄을 바꿀 수 있어요.",
    },
    {
      target: "assistant-question",
      title: "고객의 업무 리스트를 물어볼게요",
      description:
        "“김유정 고객님 관련해서 해야 하는 업무 리스트 좀 뽑아줘”\n이렇게 고객명과 필요한 업무를 함께 말해 주세요.",
      stage: "question",
    },
    {
      target: "assistant-answer-summary",
      title: "제출 현황과 확인할 일을 정리해요",
      description:
        "누락 서류를 먼저 안내하고, 확인할 일을 이어서 보여드려요.\n항목 링크를 누르면 해당 청구로 이동할 수 있어요.",
      stage: "answer",
    },
    {
      target: "assistant-sources",
      title: "답변의 근거를 함께 확인하세요",
      description:
        "인용한 문서와 조항, 원문을 여기서 볼 수 있어요.\n약관·업무 기준과 가상 문서 표시를 확인해 주세요.",
      stage: "answer",
    },
    {
      target: "guide-help",
      title: "언제든 다시 확인하세요",
      description: "궁금할 땐 언제든 ?를 눌러 주세요.",
      stage: "answer",
    },
  ],
  inbox: [
    {
      target: "workspace-navigation",
      title: "청구 검토는 여기서 시작해요",
      description:
        "왼쪽의 다섯 메뉴를 따라\n서류 확인부터 보완 요청과 이력까지 살펴볼 수 있어요.",
    },
    {
      target: "workspace-menu-1",
      title: "1. 검토할 청구를 찾아보세요",
      description:
        "배정된 청구와 처리 상태를 한눈에 봐요.\n고객을 검색하거나 상태별로 목록을 좁힐 수 있어요.",
    },
    {
      target: "workspace-menu-2",
      title: "2. 청구의 전체 흐름을 확인해요",
      description:
        "제출 서류, 정보 대조, 검토 결과를 살펴보고\n다음에 처리할 업무를 정리하는 화면이에요.",
    },
    {
      target: "workspace-menu-3",
      title: "3. 원본과 추출 정보를 대조해요",
      description:
        "서류 원문을 보며 읽어 온 값을 확인해요.\n필요하면 두 서류를 나란히 비교할 수 있어요.",
    },
    {
      target: "workspace-menu-4",
      title: "4. 누락 서류를 안내해요",
      description:
        "고객에게 필요한 서류와 안내 문구를 준비해요.\n데모에서는 실제 전송 없이 모의 발송만 해요.",
    },
    {
      target: "workspace-menu-5",
      title: "5. 처리한 내용을 되짚어 봐요",
      description:
        "접수와 분석, 담당자 확인, 보완 요청을\n시각과 처리 주체별로 확인할 수 있어요.",
    },
    {
      target: "workspace-search",
      title: "고객 이름이나 번호로 검색하세요",
      description:
        "고객 이름, 고객 ID 또는 청구번호를 입력해 주세요.\n검색 버튼이나 Enter로 결과를 확인할 수 있어요.",
    },
    {
      target: "inbox-filters",
      title: "필요한 상태만 모아 보세요",
      description:
        "상태를 선택하면 해당 청구만 보여드려요.\n옆의 숫자는 현재 조회 범위의 건수예요.",
    },
    {
      target: "inbox-heading-person",
      title: "청구번호와 고객을 함께 확인하세요",
      description:
        "같은 이름이나 같은 고객의 여러 청구를 구분해요.\n생년월일과 청구번호를 함께 확인해 주세요.",
    },
    {
      target: "inbox-heading-receipt",
      title: "청구 유형과 접수 시각을 살펴봐요",
      description:
        "어떤 보장을 청구했는지, 언제 접수됐는지 보여드려요.\n청구 유형에 따라 필요한 서류가 달라져요.",
    },
    {
      target: "inbox-heading-status",
      title: "처리 상태와 확인할 일을 구분해요",
      description:
        "보완 요청은 서류가 빠진 건, 검토 필요는 확인이 남은 건이에요.\nAI 검토 결과에서 남은 확인 사항을 짧게 보여드려요.",
    },
    {
      target: "inbox-heading-status",
      title: "자동 통과는 지급 확정이 아니에요",
      description:
        "현재 확인 규칙에서 문제가 발견되지 않았다는 뜻이에요.\n지급 여부와 금액은 지급 심사 담당자가 결정해요.",
    },
    {
      target: "guide-help",
      title: "언제든 다시 확인하세요",
      description: "궁금할 땐 언제든 ?를 눌러 주세요.",
    },
  ],
  detail: [
    {
      target: "claim-search-results",
      title: "검색 결과에서 고객을 확인하세요",
      description:
        "이름이 같아도 다른 고객일 수 있어요.\n생년월일과 청구번호를 확인한 뒤 선택해 주세요.",
      stage: "search",
    },
    {
      target: "detail-stepper",
      title: "네 단계로 차례대로 검토해요",
      description:
        "서류 확인 → 정보 대조 → 검토 결과 → 완료 순서예요.\n안내에서 움직이는 단계는 실제 청구에 저장되지 않아요.",
      detailStep: 0,
    },
    {
      target: "detail-step-0",
      title: "1. 필요한 서류부터 살펴보세요",
      description:
        "청구 유형에 필요한 서류가 모두 들어왔는지\n제출 목록과 오른쪽 요약을 함께 확인해 주세요.",
      detailStep: 0,
    },
    {
      target: "detail-documents",
      title: "제출 서류와 누락 서류를 확인해요",
      description:
        "각 서류의 제출 여부와 접수 경로가 보여요.\n김유정 예시에서는 수술확인서 1개가 빠져 있어요.",
      detailStep: 0,
    },
    {
      target: "detail-extracted",
      title: "주요 청구 정보를 요약해 드려요",
      description:
        "질병분류기호, 날짜, 가입 특약과 접수 경로를 보여요.\n중요한 값은 원문과 함께 확인해 주세요.",
      detailStep: 0,
    },
    {
      target: "detail-step-1",
      title: "2. 서로 다른 서류의 값을 비교해요",
      description:
        "날짜나 환자 정보가 서로 맞는지 살펴봐요.\n아래 표에서 대조한 서류와 결과를 확인해 주세요.",
      detailStep: 1,
    },
    {
      target: "compare-key",
      title: "무엇을 비교했는지 먼저 읽어 주세요",
      description:
        "진단일과 보고일, 입원일수처럼\n함께 확인할 정보의 이름이에요.",
      detailStep: 1,
    },
    {
      target: "compare-a",
      title: "첫 번째 서류와 값을 보여드려요",
      description:
        "서류 A의 이름과 읽어 온 값이에요.\n오른쪽 서류 B와 짝지어 확인해 주세요.",
      detailStep: 1,
    },
    {
      target: "compare-b",
      title: "함께 대조할 서류를 보여드려요",
      description:
        "서류 B의 이름과 값이에요.\n두 서류의 날짜나 내용을 비교해 주세요.",
      detailStep: 1,
    },
    {
      target: "compare-result",
      title: "일치·불일치·안내를 구분해요",
      description:
        "일치는 정보가 맞고, 불일치는 추가 확인이 필요해요.\n안내는 참고 사항이며, 1일 차이는 산정 방식 차이일 수 있어요.",
      detailStep: 1,
    },
    {
      target: "detail-step-2",
      title: "3. 남은 업무를 정리하세요",
      description:
        "확인할 사항과 누락 서류를 요약하고,\n전달할 내용은 담당자 메모에 남겨 주세요.",
      detailStep: 2,
    },
    {
      target: "detail-summary",
      title: "남은 확인 사항을 한눈에 봐요",
      description:
        "확인 건수, 누락 서류, 보상 제외 가능성을 보여드려요.\n요약을 누르면 자세한 검토 화면으로 이동해요.",
      detailStep: 2,
    },
    {
      target: "detail-note",
      title: "확인한 내용과 전달 사항을 남겨요",
      description:
        "판단 근거와 추가 확인 내용을 적어 주세요.\n저장한 메모는 다음 담당자에게 전달할 때 활용해요.",
      detailStep: 2,
    },
    {
      target: "detail-step-3",
      title: "4. 다음 업무로 이어가세요",
      description:
        "제출 현황과 남은 확인 사항을 살펴본 뒤\n보완 요청 또는 지급 심사 이관을 선택해 주세요.",
      detailStep: 3,
    },
    {
      target: "detail-supplement",
      title: "누락 서류가 있다면 보완 요청해요",
      description:
        "보완 처리 화면에서 안내 문구를 준비할 수 있어요.\n괄호 안에는 요청할 서류 이름이 표시돼요.",
      detailStep: 3,
    },
    {
      target: "detail-submit",
      title: "확인이 끝나면 지급 심사로 넘겨요",
      description:
        "필수 서류와 확인 사항이 정리되어야 사용할 수 있어요.\n지급 확정이 아니라 심사 담당자에게 전달하는 기능이에요.",
      detailStep: 3,
    },
    {
      target: "guide-help",
      title: "언제든 다시 확인하세요",
      description: "궁금할 땐 언제든 ?를 눌러 주세요.",
      detailStep: 3,
    },
  ],
  review: [
    {
      target: "page-title",
      title: "원본과 추출 정보를 함께 확인해요",
      description:
        "서류에서 읽어 온 값과 확인할 사항을 살펴봐요.\n김유정 고객의 가상 서류로 안내해 드릴게요.",
    },
    {
      target: "review-documents",
      title: "확인할 서류를 선택하세요",
      description:
        "서류를 바꾸면 원본과 추출 정보도 함께 바뀌어요.\n누락 서류는 아래 확인 사항에서 보완 요청해 주세요.",
    },
    {
      target: "review-zoom",
      title: "읽기 편한 크기로 조절하세요",
      description:
        "확대·축소 버튼으로 크기를 바꿀 수 있어요.\n원본은 드래그하거나 스크롤해서 움직여 보세요.",
    },
    {
      target: "review-field-headings",
      title: "항목·값·출처·신뢰도를 구분해요",
      description:
        "읽어 온 값과 출처, 실제 추출 점수를 보여드려요.\n점수가 높아도 원문과 다른 값은 확인이 필요해요.",
    },
    {
      target: "review-issues",
      title: "확인 사항을 누르면 원본으로 이동해요",
      description:
        "누락과 불일치, 보상 제외 가능성, 안내를 구분해요.\n원문을 확인한 뒤 확인 버튼으로 기록을 남겨 주세요.",
    },
    {
      target: "review-compare-controls",
      title: "두 서류는 각각 확대하고 움직여요",
      description:
        "한쪽의 배율과 위치를 바꿔도 다른 쪽은 그대로예요.\n필요한 부분을 읽기 편하게 조절해 주세요.",
      stage: "compare",
    },
    {
      target: "review-field-tabs",
      title: "문서별 정보와 비교 항목을 나눠 봐요",
      description:
        "각 문서 탭에서는 그 서류의 정보를 볼 수 있어요.\n비교 항목 탭은 해당 이슈의 값만 모아 보여드려요.",
      stage: "compare",
    },
    {
      target: "guide-help",
      title: "언제든 다시 확인하세요",
      description: "궁금할 땐 언제든 ?를 눌러 주세요.",
      stage: "compare",
    },
  ],
  supplement: [
    {
      target: "supplement-customer",
      title: "먼저 안내할 고객을 확인하세요",
      description:
        "이름과 청구번호가 맞는지 살펴봐 주세요.\n이 안내는 실제로 문자를 보내지 않는 가상 예시예요.",
    },
    {
      target: "supplement-missing",
      title: "누락 서류와 총개수를 확인해요",
      description:
        "아직 제출되지 않은 필수 서류예요.\n김유정 예시에는 수술확인서 1개가 표시돼요.",
    },
    {
      target: "supplement-generate",
      title: "준비된 양식으로 문자를 만들어요",
      description:
        "고객명, 청구번호와 누락 서류를 자동으로 채워요.\n생성한 문구는 오른쪽에서 수정할 수 있어요.",
    },
    {
      target: "supplement-letter",
      title: "보낼 내용을 꼼꼼히 살펴보세요",
      description:
        "고객 정보와 요청 서류, 발급·제출 방법을 확인해 주세요.\n필요한 표현은 직접 다듬어 사용하실 수 있어요.",
    },
    {
      target: "supplement-send",
      title: "저장과 모의 발송은 달라요",
      description:
        "초안 저장은 작성 중인 문구를 보관해요.\n모의 발송은 실제 전송 없이 회신 대기 상태만 남겨요.",
    },
    {
      target: "supplement-history",
      title: "이전 안내와 보완 접수를 확인해요",
      description:
        "보낸 문구와 시각을 이어서 볼 수 있어요.\n보완 서류가 접수되면 관련 기록도 표시돼요.",
      stage: "sent",
    },
    {
      target: "guide-help",
      title: "언제든 다시 확인하세요",
      description: "궁금할 땐 언제든 ?를 눌러 주세요.",
      stage: "sent",
    },
  ],
  history: [
    {
      target: "page-title",
      title: "처리 과정을 시간순으로 살펴봐요",
      description:
        "서류 접수, 분석과 담당자 확인 기록을 보여드려요.\n고객명과 청구번호가 맞는지 먼저 확인해 주세요.",
    },
    {
      target: "history-filters",
      title: "처리 주체별로 기록을 모아 보세요",
      description:
        "전체, 담당자, 시스템·AI 중에서 선택해요.\n필요한 기록만 좁혀서 확인할 수 있어요.",
    },
    {
      target: "history-records",
      title: "언제 누가 무엇을 했는지 확인해요",
      description:
        "최근 기록부터 날짜와 시각, 처리 내용을 보여드려요.\n값 수정이나 보완 요청 경위를 되짚을 때 활용해 주세요.",
    },
    {
      target: "guide-help",
      title: "언제든 다시 확인하세요",
      description: "궁금할 땐 언제든 ?를 눌러 주세요.",
    },
  ],
};
export function tourKey(path: string): string {
  return (
    (
      {
        "/": "home",
        "/chat": "assistant",
        "/workspace": "inbox",
        "/workspace/detail": "detail",
        "/workspace/review": "review",
        "/workspace/supplement": "supplement",
        "/workspace/history": "history",
      } as Record<string, string>
    )[path] ?? ""
  );
}
