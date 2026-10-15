/** 화면은 이 API 타입만 소비한다. 건수·서류 목록·이슈는 서버에서 계산한다. */
export type FieldRow = {
  id: number;
  document_id: number;
  key: string;
  value: string;
  display_value: string;
  raw_value: string;
  extract_conf: "high" | "low" | null;
  source_found: boolean;
  review_reasons: string[];
  method: "parse" | "ocr" | "data";
  page: number;
  bbox: { x: number; y: number }[] | null;
  confirmed_by: number | null;
  confirmed_value: string | null;
  doc_type: string;
  kcd_name: string | null;
  parse_evidence: { text: string; basis: string } | null;
};
export type Doc = {
  id: number;
  doc_type: string;
  source: string;
  status: string;
  page_size: { width?: number; height?: number };
};
export type Issue = {
  id: number;
  kind: string;
  rule_id: string;
  title: string;
  detail: string;
  doc_ids: number[];
  field_keys: string[];
  status: string;
};
export type Claim = {
  id: string;
  customer_name: string;
  policy_no: string;
  claim_types: string[];
  status: string;
  received_at: string;
  step: number;
  review_note: string;
  channel: string[];
  customer: {
    id: string;
    name: string;
    birth_date: string;
    contact: string;
  } | null;
  policy: {
    product_name: string;
    riders: string[];
    coverage_start: string;
    coverage_end: string;
  } | null;
  submitted_count: number;
  required_count: number;
  required: string[];
  documents: Doc[];
  issues: Issue[];
  fields: FieldRow[];
  open_issue_count: number;
};
export type ClaimList = { items: Claim[]; counts: Record<string, number> };
export const docLabels: Record<string, string> = {
  diagnosis: "진단서",
  pathology: "조직검사 결과지",
  admission: "입퇴원확인서",
  surgery_cert: "수술확인서",
  medical_receipt: "진료비 영수증",
  medical_detail: "진료비 세부내역서",
  prescription: "처방전",
  pharmacy_receipt: "약제비 영수증",
  outpatient: "통원확인서",
  disability: "후유장해 진단서",
  death_cert: "사망진단서",
  family_cert: "가족관계증명서",
  basic_cert: "기본증명서",
  claim_form: "보험금 청구서",
  id_copy: "신분증 사본",
  poa: "위임장",
  seal_cert: "인감증명서",
  bankbook: "통장 사본",
  consent: "개인정보 동의서",
  imaging_report: "영상 판독지",
  accident_report: "사고 사실확인원",
  accident_statement: "사고 경위서",
  medical_record: "진료기록 사본",
  other: "분류 대기",
};
export const typeLabels: Record<string, string> = {
  cancer_diagnosis: "암 진단금",
  hospitalization: "입원일당",
  medical_expense: "실손",
  surgery: "수술비",
  outpatient: "통원일당",
  disability: "후유장해",
  death: "사망보험금",
};
export const fieldLabels: Record<string, string> = {
  patient_name: "환자 성명",
  issuer: "발행 기관",
  issued_date: "발행일",
  diagnosis_code: "질병분류기호",
  diagnosis_name: "진단명",
  diagnosis_date: "진단일",
  onset_date: "발병일",
  report_date: "병리 보고일",
  pathology_result: "병리 진단",
  specimen: "검체",
  admit_date: "입원일",
  discharge_date: "퇴원일",
  stay_days: "입원 일수",
  period_start: "진료 시작일",
  period_end: "진료 종료일",
  inpatient_days: "입원 일수",
  covered_copay: "급여 본인부담",
  non_covered: "비급여",
  total: "합계",
  patient_total: "환자부담 합계",
};
export function label(key: string) {
  return (
    fieldLabels[key] ??
    key.replace(
      /items\[(\d+)\]\.(.+)/,
      (_, i, k) =>
        `항목 ${Number(i) + 1} · ${({ drug_name: "품명", amount: "금액", days: "일수", covered: "급여 구분", per_day: "일일 횟수", name: "항목명", category: "분류", code: "코드", date: "진료일" } as Record<string, string>)[k] ?? k}`,
    )
  );
}
export function reason(text: string) {
  return (
    (
      {
        low_conf: "모델 신뢰도 낮음",
        not_in_source: "원문 불일치",
        format: "형식 확인",
        cross_check: "서류 간 대조 필요",
      } as Record<string, string>
    )[text] ?? text
  );
}
export function display(field: FieldRow) {
  return field.key.endsWith(".covered")
    ? field.display_value === "true"
      ? "급여"
      : field.display_value === "false"
        ? "비급여"
        : field.display_value
    : field.display_value;
}
export async function api<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch("/api" + url, {
    cache: "no-store",
    ...init,
    headers: {
      ...(init?.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : `요청을 처리하지 못했어요 (${response.status})`,
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
