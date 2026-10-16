/** 서버 시간대와 무관하게 한국 자정과 지난7일 경계가 맞는지 검증한다. */
import fs from "node:fs";
import vm from "node:vm";
import ts from "typescript";
import assert from "node:assert/strict";
const context={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync(new URL("../lib/chat-history.ts",import.meta.url),"utf8"),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,context);
const date=context.exports.conversationDate,now="2026-10-16T16:00:00Z";
assert.equal(date("2026-10-16T15:12:00Z",now).group,"오늘");
assert.match(date("2026-10-16T15:12:00Z",now).label,/오전 12:12/);
assert.equal(date("2026-10-16T14:59:00Z",now).group,"지난 7일");
assert.equal(date("2026-10-09T15:00:00Z",now).group,"지난 7일");
assert.equal(date("2026-10-09T14:59:00Z",now).group,"이전 대화");
assert.equal(date("2026-10-13T00:00:00Z",now).label,"10월 13일");
console.log("PASS: 한국 자정·실제 세션 시간·지난7일 경계·날짜 표시");
