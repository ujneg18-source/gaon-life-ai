/** 메뉴 정의를 한 곳에 두어 메뉴·경로·역할 표시가 서로 달라지지 않게 한다. */
export const workspacePages = [
  {
    slug: "",
    title: "청구 검토함",
    description: "접수된 청구 서류를 한곳에서 확인합니다.",
  },
  {
    slug: "detail",
    title: "청구건 상세",
    description: "청구 한 건의 서류와 검토 단계를 확인합니다.",
  },
  {
    slug: "review",
    title: "문서 분석 · 검토",
    description: "원본 근거와 추출된 정보를 나란히 살펴봅니다.",
  },
  {
    slug: "supplement",
    title: "보완 처리",
    description: "추가로 필요한 서류와 보완 내역을 관리합니다.",
  },
  {
    slug: "history",
    title: "검토 이력",
    description: "담당자의 확인과 변경 내역을 살펴봅니다.",
  },
  {
    slug: "operations",
    title: "운영 관리",
    description: "검토 기준과 운영 설정을 관리합니다.",
    adminOnly: true,
  },
] as const;
