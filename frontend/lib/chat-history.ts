/** 대화 제목은 실제 첫 질문을 사용하고 시각·날짜 구분은 한국 시간을 기준으로 한다. */
const zone = "Asia/Seoul";
function day(value: string) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: zone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(value));
  const get = (key: string) => parts.find((p) => p.type === key)!.value;
  return Date.UTC(
    Number(get("year")),
    Number(get("month")) - 1,
    Number(get("day")),
  );
}
export function conversationDate(value: string, now: string) {
  const age = Math.floor((day(now) - day(value)) / 86400000);
  return {
    group: age <= 0 ? "오늘" : age <= 7 ? "지난 7일" : "이전 대화",
    label: new Intl.DateTimeFormat(
      "ko-KR",
      age <= 0
        ? { timeZone: zone, hour: "numeric", minute: "2-digit", hour12: true }
        : { timeZone: zone, month: "long", day: "numeric" },
    ).format(new Date(value)),
  };
}
