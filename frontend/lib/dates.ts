/** 날짜 전용 값은 시차 없이, 시각은 한국 시간으로 표시한다. DB의 ISO 값은 바꾸지 않는다. */
export function formatDate(value: string | null | undefined): string {
  return value ? formatDatesInText(value) : "—";
}
export function formatDatesInText(value: string): string {
  return value.replace(/\b(\d{4})-(\d{2})-(\d{2})\b/g, "$1.$2.$3");
}
export function formatDateTime(
  value: string,
  naiveTimeZone: "UTC" | "Asia/Seoul" = "UTC",
): string {
  // 기존 접수 시각은 SQLite에 한국 현지시각으로, 감사 이력은 UTC로 저장돼 출처를 명시한다.
  const date = new Date(
    /(?:Z|[+-]\d{2}:\d{2})$/.test(value)
      ? value
      : value + (naiveTimeZone === "Asia/Seoul" ? "+09:00" : "Z"),
  );
  if (Number.isNaN(date.getTime())) return "—";
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const values = Object.fromEntries(parts.map((p) => [p.type, p.value]));
  return `${values.year}.${values.month}.${values.day} ${values.hour}:${values.minute}`;
}
