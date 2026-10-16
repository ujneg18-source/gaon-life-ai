/** 출처 공개 범위를 실제 파일과 대조한다. 정답/참고용 약관/임의 경로는 공개하지 않는다. */
import fs from "node:fs";
import assert from "node:assert/strict";
import vm from "node:vm";
import ts from "typescript";
const root = new URL("../../", import.meta.url);
const code=ts.transpileModule(fs.readFileSync(new URL("frontend/lib/data-sources.ts",root),"utf8"),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const context={exports:{}};
vm.runInNewContext(code,context);
const {dataSources}=context.exports;
assert.equal(new Set(dataSources.map(s=>s.id)).size,dataSources.length);
assert.equal(dataSources.filter(s=>s.kind==="public").length,5);
assert.equal(dataSources.filter(s=>s.kind==="fictional").length,7);
assert.equal(dataSources.filter(s=>s.kind==="demo").length,2);
for(const source of dataSources){
 assert.match(source.id,/^[a-z0-9-]+$/);
 if(source.file){
  assert.match(source.file,/^data\/kb\/(?:policy\/std_[a-z0-9_]+\.txt|gaon\/[a-z0-9_]+\.md)$/);
  assert.ok(fs.readFileSync(new URL(source.file,root),"utf8").trim().length>0);
 }else assert.ok(source.body);
}
assert.equal(dataSources.find(s=>s.id==="reference"),undefined);
assert.equal(dataSources.find(s=>s.id==="../../.env"),undefined);
const sample=JSON.parse(fs.readFileSync(new URL("data/samples/customers.json",root),"utf8"));
assert.equal(sample.customers.length,10);assert.equal(sample.claims.length,13);
console.log("PASS: 12개 허용 문서 실파일·공개/가상 분류·모의 데이터 2종·고객/청구 건수·임의 경로 제외");
