import test from "node:test";
import assert from "node:assert/strict";
import { formatDate, formatDateTime, formatDatesInText } from "../lib/dates.ts";

test("날짜와 날짜+시각을 같은 표기로 표시하고 접수/이력 시차를 구분한다", () => {
  assert.equal(formatDate("1988-05-20"), "1988.05.20");
  assert.equal(formatDateTime("2026-10-15T09:12:00", "Asia/Seoul"), "2026.10.15 09:12");
  assert.equal(formatDateTime("2026-10-15T09:12:00+09:00"), "2026.10.15 09:12");
  assert.equal(formatDateTime("2026-10-15T15:12:00"), "2026.10.16 00:12");
  assert.equal(formatDatesInText("진단일 2026-09-18 · 보고일 2026-09-21"), "진단일 2026.09.18 · 보고일 2026.09.21");
});
