/** 페이지마다 독립 실행하며 설명과 강조 영역은 짧고 명확한 단위로 묶는다. */
export type TourStep = {
  target: string;
  title: string;
  description: string;
  placement?: "below-left" | "below-right" | "left" | "right";
  details?: { label: string; text: string }[];
  stage?: string;
  detailStep?: number;
};
export const tours: Record<string, TourStep[]> = {
  home: [
    {
      target: "home-overview",
      title: "안녕하세요. 가온생명 AI입니다",
      description: "보상담당자의 청구업무를 돕는 가온 Ai입니다.",
      details: [
        {
          label: "주요기능",
          text: "제출 서류를 분석해 누락 서류, 서류 간 불일치, 약관 확인 항목을 우선 표시합니다. 모든 검토 결과에는 근거 약관 조항을 함께 제공합니다.",
        },
        {
          label: "도입 배경",
          text: "실손24로 데이터가 전송되는 서류는 영수증, 세부내역서, 처방전 3종뿐입니다. 진단서, 수술확인서 등 나머지 서류는 담당자가 직접 읽고 대조해야 합니다. 이 반복 업무를 AI가 먼저 처리해 담당자가 판단이 필요한 항목에 집중하도록 합니다.",
        },
        {
          label: "데모 범위",
          text: "가상 보험사(가온생명), 가상 고객 10명, 시연용 약관으로 구성한 PoC입니다. 실제 도입에는 사내 약관, 업무 기준, 고객 데이터 연동이 필요합니다. 보험금 지급 여부와 지급 금액은 판단하지 않으며, 지급 심사 담당자가 결정합니다",
        },
      ],
    },
    {
      target: "home-assistant",
      placement: "left",
      title: "궁금한 업무는 대화로 물어보세요",
      description: "찾고 싶은 내용을 평소 말하듯 입력해 보세요.",
      details: [
        {
          label: "기준 찾기",
          text: "약관 조항과 업무 절차를 근거와 함께 확인합니다.",
        },
        {
          label: "고객 업무",
          text: "청구 현황과 확인할 일을 정리하고 안내 문구를 준비해요.",
        },
      ],
    },
    {
      target: "home-workspace",
      placement: "right",
      title: "청구 서류를 한곳에서 검토하세요",
      description: "서류 접수 이후의 검토 업무를 이어가는 공간입니다.",
      details: [
        {
          label: "서류 확인",
          text: "필수 서류의 제출 여부와 추출된 정보를 살펴봐요.",
        },
        {
          label: "대조·처리",
          text: "서류 간 차이를 확인하고 보완 요청이나 지급 심사로 연결합니다.",
        },
      ],
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
      description: "약관 검색부터 고객별 청구 검토까지 대화로 도와드려요.",
      details: [
        {
          label: "업무 질문",
          text: "약관과 업무 절차를 물으면 관련 근거를 함께 보여드립니다.",
        },
        {
          label: "고객 조회",
          text: "이름이나 청구번호로 제출 현황과 확인할 일을 찾을 수 있어요.",
        },
        {
          label: "지금은 예시",
          text: "김유정 고객의 저장된 대화로 사용 흐름을 살펴봅니다.",
        },
      ],
    },
    {
      target: "assistant-new-chat",
      title: "다른 업무는 새 채팅에서 시작해요",
      description: "새로운 주제는 새 채팅으로 나눠 시작해 보세요.",
      details: [
        {
          label: "새 대화",
          text: "다른 고객이나 업무를 이전 질문과 구분해 확인합니다.",
        },
        {
          label: "대화 목록",
          text: "대화 제목과 시작 시각을 표시해요. 선택하면 다시 볼 수 있습니다.",
        },
        {
          label: "보관 범위",
          text: "현재 화면에서만 유지돼요. 새로고침·재로그인하면 비워집니다.",
        },
      ],
    },
    {
      target: "assistant-input",
      title: "평소 말하듯 질문해 주세요",
      description: "업무에 필요한 내용을 문장으로 입력해 주세요.",
      details: [
        {
          label: "질문 방법",
          text: "고객명·청구번호와 확인할 내용을 함께 적으면 좋아요.",
        },
        {
          label: "보내기",
          text: "Enter 또는 화살표 버튼으로 전송합니다. Shift+Enter는 줄바꿈이에요.",
        },
      ],
    },
    {
      target: "assistant-question",
      title: "고객의 업무 리스트를 물어볼게요",
      description: "실제 업무에서는 이렇게 질문할 수 있습니다.",
      details: [
        {
          label: "예시 질문",
          text: "김유정 고객님 관련해서 해야 하는 업무 리스트 좀 뽑아줘",
        },
        {
          label: "확인 범위",
          text: "고객의 제출 서류와 남은 검토 사항을 함께 정리해 드려요.",
        },
      ],
      stage: "question",
    },
    {
      target: "assistant-answer-summary",
      title: "제출 현황과 확인할 일을 정리해요",
      description: "답변에서 먼저 처리할 일과 확인할 이유를 살펴보세요.",
      details: [
        {
          label: "누락 서류",
          text: "김유정 예시에는 수술확인서 1개가 부족합니다.",
        },
        {
          label: "확인 사항",
          text: "서류 간 값 차이와 추가로 살펴볼 내용을 설명해요.",
        },
        {
          label: "업무 연결",
          text: "항목 링크를 누르면 해당 청구의 검토 화면으로 이동합니다.",
        },
      ],
      stage: "answer",
    },
    {
      target: "assistant-sources",
      title: "답변의 근거를 함께 확인하세요",
      description: "답변이 어떤 문서에 근거했는지 확인하는 영역입니다.",
      details: [
        {
          label: "문서·조항",
          text: "약관 이름과 인용 조항을 보고 적용할 기준을 확인해요.",
        },
        {
          label: "원문 확인",
          text: "인용 내용을 직접 읽고 답변과 맞는지 대조할 수 있습니다.",
        },
        {
          label: "자료 구분",
          text: "공개 문서와 가상 문서 표시도 함께 확인해 주세요.",
        },
      ],
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
      description: "왼쪽 메뉴에서 필요한 업무 화면으로 이동할 수 있어요.",
      details: [
        {
          label: "청구 확인",
          text: "검토함에서 청구를 찾고 상세에서 전체 진행 상황을 확인합니다.",
        },
        {
          label: "서류 검토",
          text: "문서 분석·검토에서 원본과 추출값을 비교해요.",
        },
        {
          label: "후속 업무",
          text: "보완 처리로 누락 서류를 안내하고 검토 이력에서 경위를 봅니다.",
        },
      ],
    },
    {
      target: "workspace-menu-1",
      title: "1. 검토할 청구를 찾아보세요",
      description: "배정된 청구를 찾아 검토를 시작하는 화면입니다.",
      details: [
        {
          label: "고객 찾기",
          text: "이름·고객 ID·청구번호로 검색할 수 있어요.",
        },
        {
          label: "목록 읽기",
          text: "청구 유형, 접수 시각, 처리 상태와 AI 검토 결과를 함께 봅니다.",
        },
      ],
    },
    {
      target: "workspace-menu-2",
      title: "2. 청구의 전체 흐름을 확인해요",
      description: "한 청구 건의 서류와 처리 단계를 모아 보여드립니다.",
      details: [
        {
          label: "서류·정보",
          text: "필수 서류 제출 여부와 서류 간 정보 차이를 확인해요.",
        },
        {
          label: "업무 정리",
          text: "검토 결과와 담당자 메모를 정리한 뒤 다음 업무로 이어갑니다.",
        },
      ],
    },
    {
      target: "workspace-menu-3",
      title: "3. 원본과 추출 정보를 대조해요",
      description: "서류 원본을 보면서 추출된 값이 맞는지 확인해요.",
      details: [
        {
          label: "원문 대조",
          text: "날짜나 질병분류기호 등 중요한 항목을 원본과 비교합니다.",
        },
        {
          label: "두 서류",
          text: "비교가 필요한 문서는 나란히 열고 각각 확대·이동할 수 있어요.",
        },
      ],
    },
    {
      target: "workspace-menu-4",
      title: "4. 누락 서류를 안내해요",
      description: "추가로 필요한 서류를 고객에게 안내하는 화면입니다.",
      details: [
        {
          label: "문구 준비",
          text: "고객과 누락 서류를 확인하고 준비된 양식으로 초안을 만들어요.",
        },
        {
          label: "모의 발송",
          text: "데모에서는 실제 문자를 보내지 않고 발송 기록만 남깁니다.",
        },
      ],
    },
    {
      target: "workspace-menu-5",
      title: "5. 처리한 내용을 되짚어 봐요",
      description: "누가 언제 어떤 처리를 했는지 되짚어 보는 화면이에요.",
      details: [
        {
          label: "처리 기록",
          text: "접수·분석·값 수정·보완 요청 등 업무 경위를 확인합니다.",
        },
        {
          label: "주체별 조회",
          text: "담당자와 시스템·AI 기록을 나눠 볼 수 있어요.",
        },
      ],
    },
    {
      target: "workspace-search",
      title: "고객 이름이나 번호로 검색하세요",
      description: "고객이나 청구를 식별할 정보를 입력해 주세요.",
      details: [
        {
          label: "검색 기준",
          text: "고객 이름, 고객 ID 또는 청구번호로 조회합니다.",
        },
        {
          label: "동명이인",
          text: "이름이 같으면 생년월일과 청구번호를 함께 확인해요.",
        },
      ],
    },
    {
      target: "inbox-filters",
      title: "필요한 상태만 모아 보세요",
      description: "상태를 선택하면 필요한 청구만 모아 볼 수 있어요.",
      details: [
        {
          label: "상태별 조회",
          text: "처리 전·검토 필요·보완 요청 등 업무에 맞춰 선택합니다.",
        },
        {
          label: "건수 읽기",
          text: "옆 숫자는 현재 조회 범위의 청구 건수예요. 전체로 돌아가면 모두 봅니다.",
        },
      ],
    },
    {
      target: "inbox-heading-person",
      title: "청구번호와 고객을 함께 확인하세요",
      description: "청구번호와 고객 정보를 짝지어 확인해 주세요.",
      details: [
        {
          label: "청구번호",
          text: "GA-2610-0482처럼 한 청구 건을 구분하는 번호입니다.",
        },
        {
          label: "고객·생년월일",
          text: "이름 옆 생년월일을 함께 봐요. 목록의 김서연 고객들은 동명이인입니다.",
        },
        {
          label: "상세 열기",
          text: "대상 고객과 청구번호가 맞으면 해당 행을 눌러 업무를 시작해요.",
        },
      ],
    },
    {
      target: "inbox-heading-receipt",
      title: "청구 유형과 접수 시각을 살펴봐요",
      description: "청구한 보장과 접수 시점을 함께 살펴보세요.",
      details: [
        {
          label: "청구 유형",
          text: "암 진단금·입원일당 등 요청한 보장을 보여줘요. 필요한 서류가 달라집니다.",
        },
        {
          label: "접수",
          text: "서류가 접수된 날짜와 시각입니다. 업무 순서를 살필 때 참고해요.",
        },
      ],
    },
    {
      target: "inbox-heading-status",
      title: "처리 상태와 확인할 일을 구분해요",
      description: "상태는 처리 단계, AI 검토 결과는 확인할 일을 보여줍니다.",
      details: [
        {
          label: "보완 요청",
          text: "필수 서류가 부족한 건이에요. 필요한 서류를 고객에게 요청합니다.",
        },
        {
          label: "검토 필요",
          text: "값 차이나 낮은 신뢰도 등 담당자의 확인이 남아 있습니다.",
        },
        {
          label: "AI 검토 결과",
          text: "확인할 사항의 건수를 보고 상세 화면에서 내용을 살펴봐요.",
        },
      ],
    },
    {
      target: "inbox-heading-status",
      title: "자동 통과는 지급 확정이 아니에요",
      description: "현재 확인 규칙에서 문제가 발견되지 않은 상태입니다.",
      details: [
        {
          label: "자동 통과",
          text: "서류 검토 규칙을 통과했다는 의미예요. 보상 확정과는 다릅니다.",
        },
        {
          label: "다음 확인",
          text: "필요한 검토를 마친 뒤 지급 심사로 넘겨 주세요. 지급 여부와 금액은 담당자가 결정합니다.",
        },
      ],
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
      description: "검색된 김유정 고객의 청구를 확인하고 선택해 볼게요.",
      details: [
        {
          label: "고객 확인",
          text: "동명이인이 있을 수 있어요. 이름만으로 선택하지 말고 생년월일을 봅니다.",
        },
        {
          label: "청구 확인",
          text: "같은 고객도 여러 청구가 있을 수 있어요. 청구번호까지 대조해 주세요.",
        },
      ],
      stage: "search",
    },
    {
      target: "detail-stepper",
      title: "네 단계로 차례대로 검토해요",
      description: "청구 검토는 네 단계로 진행합니다.",
      details: [
        {
          label: "서류 확인",
          text: "필수 서류의 제출 여부와 주요 청구 정보를 확인해요.",
        },
        {
          label: "정보 대조",
          text: "여러 서류에서 읽어 온 값이 서로 맞는지 비교합니다.",
        },
        {
          label: "검토·완료",
          text: "확인 사항과 메모를 정리하고 보완 요청 또는 지급 심사로 이어가요.",
        },
      ],
      detailStep: 0,
    },
    {
      target: "detail-step-0",
      title: "1. 필요한 서류부터 살펴보세요",
      description: "먼저 이 청구에 필요한 서류가 모두 왔는지 확인해요.",
      details: [
        {
          label: "제출 목록",
          text: "서류별 제출 여부와 접수 경로를 살펴봅니다.",
        },
        {
          label: "청구 요약",
          text: "오른쪽의 주요 추출 정보와 가입 특약을 함께 확인해 주세요.",
        },
      ],
      detailStep: 0,
    },
    {
      target: "detail-documents",
      title: "제출 서류와 누락 서류를 확인해요",
      description: "들어온 서류와 추가로 받아야 할 서류를 구분합니다.",
      details: [
        {
          label: "제출 서류",
          text: "서류 이름과 접수 경로를 보고 검토할 자료를 확인해요.",
        },
        {
          label: "미제출 서류",
          text: "김유정 예시에는 수술확인서 1개가 빠져 있어 보완 요청이 필요합니다.",
        },
      ],
      detailStep: 0,
    },
    {
      target: "detail-extracted",
      title: "주요 청구 정보를 요약해 드려요",
      description: "여러 서류에서 읽어 온 주요 청구 정보를 모았습니다.",
      details: [
        {
          label: "핵심 정보",
          text: "질병분류기호와 날짜 등 청구 내용을 빠르게 파악해요.",
        },
        {
          label: "확인 방법",
          text: "가입 특약·접수 경로도 함께 보고 중요한 값은 서류 원문과 대조합니다.",
        },
      ],
      detailStep: 0,
    },
    {
      target: "detail-step-1",
      title: "2. 서로 다른 서류의 값을 비교해요",
      description: "서로 다른 서류에 적힌 내용이 맞는지 비교하는 단계입니다.",
      details: [
        {
          label: "비교 내용",
          text: "환자 정보, 날짜, 입원일수 등 함께 확인할 항목을 살펴봐요.",
        },
        {
          label: "표 읽기",
          text: "대조 항목 → 서류 A·B의 값 → 결과 순서로 확인합니다.",
        },
      ],
      detailStep: 1,
    },
    {
      target: "compare-key",
      title: "무엇을 비교했는지 먼저 읽어 주세요",
      description: "이 열은 두 서류에서 무엇을 비교했는지 알려줍니다.",
      details: [
        {
          label: "항목 이름",
          text: "진단일·병리 보고일, 입원일수처럼 비교 기준을 표시해요.",
        },
        {
          label: "읽는 순서",
          text: "항목을 확인한 뒤 오른쪽 서류 A와 B의 값을 함께 봅니다.",
        },
      ],
      detailStep: 1,
    },
    {
      target: "compare-a",
      title: "첫 번째 서류와 값을 보여드려요",
      description: "비교에 사용한 첫 번째 서류의 이름과 값입니다.",
      details: [
        { label: "출처", text: "어느 서류에서 읽어 온 정보인지 확인해요." },
        {
          label: "추출값",
          text: "오른쪽 서류 B와 비교하고 차이가 있으면 원문을 살펴봅니다.",
        },
      ],
      detailStep: 1,
    },
    {
      target: "compare-b",
      title: "함께 대조할 서류를 보여드려요",
      description: "첫 번째 서류와 짝지어 확인할 두 번째 자료입니다.",
      details: [
        {
          label: "서류 짝",
          text: "서류 A와 B가 어떤 내용을 기준으로 연결됐는지 봅니다.",
        },
        {
          label: "값 비교",
          text: "날짜나 내용이 다르면 결과 열의 설명까지 함께 읽어 주세요.",
        },
      ],
      detailStep: 1,
    },
    {
      target: "compare-result",
      title: "일치·불일치·안내를 구분해요",
      description: "결과에 따라 다음에 확인할 일이 달라집니다.",
      details: [
        { label: "일치", text: "비교한 정보가 서로 맞습니다." },
        {
          label: "불일치",
          text: "서로 다른 값이 있어 원문이나 추가 자료 확인이 필요해요.",
        },
        {
          label: "안내",
          text: "참고할 차이입니다. 입원일수 1일 차이는 산정 방식 때문일 수 있어요.",
        },
      ],
      detailStep: 1,
    },
    {
      target: "detail-step-2",
      title: "3. 남은 업무를 정리하세요",
      description: "검토 중 발견한 사항을 정리하고 다음 담당자에게 전달해요.",
      details: [
        {
          label: "검토 요약",
          text: "아직 확인하지 않은 사항과 누락 서류를 살펴봅니다.",
        },
        {
          label: "담당자 메모",
          text: "판단 근거와 추가 확인 내용, 전달할 사항을 남겨 주세요.",
        },
      ],
      detailStep: 2,
    },
    {
      target: "detail-summary",
      title: "남은 확인 사항을 한눈에 봐요",
      description: "청구 건에서 남아 있는 업무를 모아 보여드립니다.",
      details: [
        {
          label: "확인할 사항",
          text: "확인 건수와 누락 서류, 보상 제외 가능성을 살펴봐요.",
        },
        {
          label: "자세히 보기",
          text: "요약 항목을 누르면 관련 검토 화면으로 이동할 수 있습니다.",
        },
      ],
      detailStep: 2,
    },
    {
      target: "detail-note",
      title: "확인한 내용과 전달 사항을 남겨요",
      description: "다음 담당자가 이해할 수 있도록 확인한 내용을 적어 주세요.",
      details: [
        {
          label: "작성 내용",
          text: "원문과 대조한 결과, 추가 확인 경위, 전달 사항을 기록합니다.",
        },
        {
          label: "메모 저장",
          text: "입력한 뒤 저장 버튼을 눌러 반영해요. 안내 예시는 빈칸으로 시작합니다.",
        },
      ],
      detailStep: 2,
    },
    {
      target: "detail-step-3",
      title: "4. 다음 업무로 이어가세요",
      description: "지금까지의 검토를 확인하고 다음 업무를 선택합니다.",
      details: [
        {
          label: "보완 필요",
          text: "필수 서류가 빠져 있으면 고객에게 보완을 요청해요.",
        },
        {
          label: "이관 준비",
          text: "서류와 확인 사항이 정리되면 지급 심사 담당자에게 전달합니다.",
        },
      ],
      detailStep: 3,
    },
    {
      target: "detail-supplement",
      title: "누락 서류가 있다면 보완 요청해요",
      description: "부족한 서류가 있다면 보완 처리 화면으로 이어가요.",
      details: [
        {
          label: "요청 서류",
          text: "버튼의 괄호 안에서 추가로 받아야 할 서류를 확인합니다.",
        },
        {
          label: "안내 준비",
          text: "고객 정보와 제출 방법이 담긴 문자 초안을 만들고 검토할 수 있어요.",
        },
      ],
      detailStep: 3,
    },
    {
      target: "detail-submit",
      title: "확인이 끝나면 지급 심사로 넘겨요",
      description: "검토를 마친 청구를 지급 심사 담당자에게 전달합니다.",
      details: [
        {
          label: "사용 조건",
          text: "필수 서류와 남은 확인 사항이 정리돼야 사용할 수 있어요.",
        },
        {
          label: "처리 의미",
          text: "지급 확정이 아닙니다. 지급 여부와 금액은 지급 심사에서 결정합니다.",
        },
      ],
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
      title: "원본을 보며 추출 정보를 검토해요",
      description:
        "문서 분석·검토는 제출 서류의 원본과 추출값을 대조하고, 확인할 사항을 정리하는 기능을 제공합니다.",
      details: [
        {
          label: "원본·정보",
          text: "왼쪽 원본과 오른쪽 추출 정보를 함께 확인해요.",
        },
        {
          label: "확인·안내",
          text: "누락·불일치 등 확인할 이유를 살펴보고 처리 기록을 남깁니다.",
        },
      ],
    },
    {
      target: "review-overview",
      title: "상단에서 고객과 서류 현황을 확인해요",
      description:
        "해당 고객에게 필요한 서류 수와 현재 제출된 서류를 확인할 수 있습니다.",
      details: [
        {
          label: "고객·건수",
          text: "김유정 · GA-2610-0482의 제출 7 / 필요 8을 보여줘요.",
        },
        {
          label: "서류 목록",
          text: "제출된 서류를 누르면 원본과 추출 정보가 바뀝니다. 누락 서류는 아래 확인 사항에서 안내해요.",
        },
      ],
    },
    {
      target: "review-original",
      title: "왼쪽은 제출된 원본 서류입니다",
      description: "추출된 값이 원본의 내용과 같은지 직접 대조해 주세요.",
      details: [
        {
          label: "원문 확인",
          text: "선택한 서류와 추출 위치를 보여드립니다. 중요한 날짜와 질병분류기호를 함께 봐요.",
        },
        {
          label: "확대·이동",
          text: "상단 버튼으로 확대·축소하고, 드래그나 스크롤로 필요한 부분을 살펴보세요.",
        },
      ],
    },
    {
      target: "review-normalized",
      title: "오른쪽 상단은 추출된 서류 정보예요",
      description: "선택한 원본에서 읽어 온 정보를 항목별로 모아 보여드립니다.",
      details: [
        {
          label: "값 대조",
          text: "환자 성명, 발행일, 진단명 등을 왼쪽 원본과 비교해 주세요.",
        },
        {
          label: "표 구성",
          text: "항목·값은 추출 내용, 출처·신뢰도는 어디서 어떻게 읽었는지 보여줍니다.",
        },
      ],
    },
    {
      target: "review-field-values",
      title: "항목과 값을 짝지어 읽어 주세요",
      description: "무슨 정보인지와 어떤 값으로 읽었는지를 함께 확인합니다.",
      details: [
        {
          label: "항목",
          text: "환자 성명·발행일·질병분류기호처럼 정보의 이름이에요.",
        },
        {
          label: "값",
          text: "서류에서 추출한 내용입니다. 원문과 다르면 연필 버튼으로 수정할 수 있어요.",
        },
      ],
    },
    {
      target: "review-field-sources",
      title: "출처와 신뢰도를 함께 확인해요",
      description: "값을 가져온 서류와 실제 추출 점수를 보여드립니다.",
      details: [
        {
          label: "출처",
          text: "진단서 (Parse)처럼 원본 서류와 추출 경로를 표시해요.",
        },
        {
          label: "신뢰도",
          text: "99.8%처럼 숫자로 표시합니다. 높아도 원문과 다를 수 있어요. 실손24 정형 데이터는 점수 대상이 아닙니다.",
        },
      ],
    },
    {
      target: "review-issues",
      title: "오른쪽 하단은 확인 사항과 안내입니다",
      description:
        "서류가 부족하거나 내용이 달라 확인이 필요한 상황을 정리해 드려요.",
      details: [
        {
          label: "상황 읽기",
          text: "누락 서류, 서류 간 불일치, 보상 제외 가능성, 참고 안내를 구분합니다.",
        },
        {
          label: "원문 확인",
          text: "항목이나 원본 비교를 눌러 해당 내용을 살펴봐 주세요.",
        },
        {
          label: "후속 처리",
          text: "확인한 사항은 기록하고, 누락 서류는 보완 요청으로 이어갑니다.",
        },
      ],
    },
    {
      target: "review-compare-controls",
      title: "두 서류는 각각 확대하고 움직여요",
      description: "비교가 필요한 경우 두 원본을 나란히 열 수 있습니다.",
      details: [
        {
          label: "독립 확대",
          text: "한쪽 문서를 확대해도 다른 쪽 배율은 바뀌지 않아요.",
        },
        {
          label: "독립 이동",
          text: "각 원본을 드래그하거나 스크롤해 비교할 부분을 맞춰 보세요.",
        },
      ],
      stage: "compare",
    },
    {
      target: "review-field-tabs",
      title: "문서별 정보와 비교 항목을 나눠 봐요",
      description: "한 번에 하나의 표를 보며 필요한 정보에 집중할 수 있습니다.",
      details: [
        {
          label: "문서 탭",
          text: "선택한 서류에서 추출한 항목만 보여드립니다.",
        },
        {
          label: "비교 항목",
          text: "현재 확인 중인 이슈와 관련된 값만 모아서 볼 수 있어요.",
        },
      ],
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
      description: "문자를 준비하기 전에 안내할 대상을 확인합니다.",
      details: [
        {
          label: "고객·청구",
          text: "이름과 청구번호가 맞는지 함께 살펴봐 주세요.",
        },
        {
          label: "가상 시연",
          text: "이 안내에서는 실제 고객에게 문자를 보내지 않습니다.",
        },
      ],
    },
    {
      target: "supplement-missing",
      title: "누락 서류와 총개수를 확인해요",
      description: "아직 제출되지 않은 필수 서류를 보여드립니다.",
      details: [
        { label: "서류 이름", text: "김유정 예시에는 수술확인서가 필요해요." },
        {
          label: "총개수",
          text: "요청할 서류 수를 함께 확인하고 빠짐없이 안내합니다.",
        },
      ],
    },
    {
      target: "supplement-generate",
      title: "준비된 양식으로 문자를 만들어요",
      description: "준비된 안내 양식에 청구 정보를 채워 초안을 만듭니다.",
      details: [
        {
          label: "자동 입력",
          text: "고객명·청구번호·상품·접수일·누락 서류를 반영해요.",
        },
        {
          label: "문구 검토",
          text: "생성 후 오른쪽 편집기에서 내용을 읽고 수정할 수 있습니다.",
        },
      ],
    },
    {
      target: "supplement-letter",
      title: "보낼 내용을 꼼꼼히 살펴보세요",
      description: "고객에게 안내할 내용이 정확한지 꼼꼼히 확인해요.",
      details: [
        {
          label: "청구 정보",
          text: "고객 이름과 청구번호, 보험 상품과 접수일을 대조합니다.",
        },
        {
          label: "요청 내용",
          text: "필요한 서류와 발급·제출 방법을 읽고 표현을 다듬어 주세요.",
        },
      ],
    },
    {
      target: "supplement-send",
      title: "저장과 모의 발송은 달라요",
      description: "초안 저장과 모의 발송은 처리 목적이 다릅니다.",
      details: [
        {
          label: "초안 저장",
          text: "수정 중인 문구를 보관합니다. 발송 이력은 생기지 않아요.",
        },
        {
          label: "모의 발송",
          text: "실제 전송 없이 발송 기록과 회신 대기 상태를 남깁니다.",
        },
      ],
    },
    {
      target: "supplement-history",
      title: "이전 안내와 보완 접수를 확인해요",
      description: "고객에게 안내한 내용과 이후 접수 경위를 함께 봅니다.",
      details: [
        {
          label: "안내 기록",
          text: "보낸 문구와 발송 시각을 확인할 수 있어요.",
        },
        {
          label: "보완 접수",
          text: "추가 서류가 들어오면 관련 접수 기록도 이어서 표시합니다.",
        },
      ],
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
        "서류 접수부터 검토와 보완 요청까지 처리 과정을 시간순으로 보여드립니다.",
      details: [
        {
          label: "고객 확인",
          text: "이름과 청구번호가 맞는지 먼저 확인해 주세요.",
        },
        {
          label: "가상 예시",
          text: "안내에서는 김유정 고객의 저장된 자료를 사용합니다.",
        },
      ],
    },
    {
      target: "history-filters",
      title: "처리 주체별로 기록을 모아 보세요",
      description: "처리 주체를 선택해 필요한 기록만 좁혀 볼 수 있어요.",
      details: [
        {
          label: "담당자",
          text: "사람이 확인하거나 수정한 업무 내역을 봅니다.",
        },
        {
          label: "시스템·AI",
          text: "자동 분석과 시스템 처리 내역을 모아 확인해요.",
        },
        {
          label: "전체",
          text: "처리 주체와 관계없이 모든 기록을 함께 보여드립니다.",
        },
      ],
    },
    {
      target: "history-records",
      title: "언제 누가 무엇을 했는지 확인해요",
      description: "최근 기록부터 언제 누가 무엇을 했는지 확인합니다.",
      details: [
        {
          label: "일시·주체",
          text: "처리 날짜와 시각, 담당자 또는 시스템 표시를 봐요.",
        },
        {
          label: "처리 내용",
          text: "값 수정이나 보완 요청 등 업무 경위를 되짚을 수 있습니다.",
        },
      ],
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
