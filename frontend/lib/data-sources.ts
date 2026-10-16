/** 표시할 자료는 명시적인 허용 목록이다. 평가 정답·참고용 실제 회사 약관은 포함하지 않는다. */
export type DataSource = {
  id: string;
  kind: "public" | "fictional" | "demo";
  title: string;
  issuer: string;
  edition: string;
  description: string;
  usage: string;
  file?: string;
  body?: string;
};
export const sourceKinds = {
  public: "공개 표준약관",
  fictional: "가온생명 시연 문서",
  demo: "가상 시연 데이터",
};
const publicSources = [
  [
    "life",
    "생명보험 표준약관",
    "std_life_insurance.txt",
    "생명보험 계약과 보장 기준의 구조를 확인하는 공개 자료입니다.",
  ],
  [
    "illness-injury",
    "질병·상해보험 표준약관",
    "std_illness_injury.txt",
    "질병·상해보험(손해보험 회사용)의 계약 및 보상 기준을 확인합니다.",
  ],
  [
    "silson-basic",
    "기본형 실손의료보험",
    "std_silson_basic.txt",
    "급여 실손의료비의 보장 범위와 공제 등 기준을 확인합니다.",
  ],
  [
    "silson-severe",
    "실손 특별약관1 · 중증 비급여",
    "std_silson_rider1_severe_noncovered.txt",
    "중증 비급여 실손의료비에 관한 약관 조항을 확인합니다.",
  ],
  [
    "silson-nonsevere",
    "실손 특별약관2 · 비중증 비급여",
    "std_silson_rider2_nonsevere_noncovered.txt",
    "비중증 비급여의 보상하지 않는 사항 등 약관 확인 항목에 활용합니다.",
  ],
];
const fictionalSources = [
  [
    "product",
    "가온 건강플러스보험 상품 개요",
    "00_product_summary.md",
    "시연용 상품과 가입 특약 구성을 정리한 문서입니다.",
  ],
  [
    "cancer",
    "암진단특약",
    "01_cancer_rider.md",
    "질병분류기호와 진단확정일을 확인하는 시연용 약관입니다.",
  ],
  [
    "hospitalization",
    "질병입원일당특약",
    "02_hospitalization_rider.md",
    "입원기간과 입원일수의 차이를 대조하는 시연용 약관입니다.",
  ],
  [
    "surgery",
    "질병수술비특약",
    "03_surgery_rider.md",
    "수술확인서 등 필요한 서류를 확인하는 시연용 약관입니다.",
  ],
  [
    "outpatient",
    "질병통원일당특약",
    "04_outpatient_rider.md",
    "통원 관련 보장과 청구 서류를 설명하는 시연용 약관입니다.",
  ],
  [
    "manual",
    "보상 업무 매뉴얼",
    "10_claims_manual.md",
    "필수 서류, 서류 간 교차검증, 실손 비급여 확인 기준을 정리했습니다.",
  ],
  [
    "templates",
    "보완 요청 표준 문구",
    "11_supplement_templates.md",
    "누락 서류를 안내하는 시연용 보완 요청 문구입니다.",
  ],
];
export const dataSources: DataSource[] = [
  ...publicSources.map(([id, title, file, description]) => ({
    id,
    title,
    description,
    kind: "public" as const,
    issuer: "금융감독원 · 보험업감독업무시행세칙 [별표 15]",
    edition: "2026.08.28 개정본 · 프로젝트 보관본",
    file: `data/kb/policy/${file}`,
    usage:
      "답변의 약관 검색과 근거 조항 제시에 사용합니다. HWP 원문에서 추출한 텍스트로, 표·그림·서식 일부가 생략될 수 있습니다.",
  })),
  ...fictionalSources.map(([id, title, file, description]) => ({
    id,
    title,
    description,
    kind: "fictional" as const,
    issuer: "가온생명 · 가상 보험사",
    edition: "시연용 가상 문서",
    file: `data/kb/gaon/${file}`,
    usage:
      "데모의 약관 검색, 서류 검토 기준과 안내 문구에 활용합니다. 실제 보험상품의 약관이나 사내 업무 기준이 아닙니다.",
  })),
  {
    id: "sample-documents",
    kind: "demo",
    title: "가상 고객·청구·의료 서류",
    issuer: "프로젝트 자체 제작",
    edition: "가상 고객 10명 · 청구 13건",
    description:
      "정상 제출, 누락, 불일치 등 업무 상황을 재현하도록 만든 가상 자료입니다.",
    usage:
      "청구 조회와 서류 추출·대조 화면의 시연에 사용합니다. 실제 고객이나 의료기관의 자료가 아닙니다.",
    body: "고객·계약·청구 정보를 가상으로 구성하고, 진단서·조직검사 결과지·입퇴원확인서·진료비 영수증·세부내역서·처방전·약제비 영수증·수술확인서를 시연용으로 제작했습니다.\n\nHTML 서식을 이미지로 만들고 일부 서류에 기울기·직인·촬영 형태를 적용해 검토 상황을 재현합니다. 문서에는 SAMPLE · 가상 데이터 표시가 들어갑니다.\n\n실제 개인정보나 환자의 진료 기록을 사용하지 않습니다. 보완 요청과 지급 심사 이관도 가상 청구를 대상으로 시연합니다.",
  },
  {
    id: "silson24-demo",
    kind: "demo",
    title: "실손24 전자 서류 모의 데이터",
    issuer: "프로젝트 자체 제작 · 연계 방식 모사",
    edition: "실제 실손24 연동 아님",
    description:
      "영수증·진료비 세부내역서·처방전의 전자 데이터 접수 흐름을 가상으로 재현합니다.",
    usage:
      "앱 업로드 원본과 전자 수신 데이터를 구분하는 데 사용합니다. 실손24에서 실제 고객 데이터를 수신하지 않습니다.",
    body: "프로젝트가 직접 만든 가상 전자 데이터를 사용합니다. 보험개발원이나 실손24가 이 데모에 제공한 실제 데이터가 아닙니다.\n\n진료비 영수증, 진료비 세부내역서, 처방전의 접수 흐름을 모사합니다. 정형 데이터는 OCR로 추출한 값이 아니므로 추출 신뢰도 점수를 표시하지 않습니다.\n\n서류 확인을 돕기 위해 대응되는 가상 서식을 함께 보여주며, 실제 전자 원본을 촬영한 이미지로 표시하지 않습니다.",
  },
];
