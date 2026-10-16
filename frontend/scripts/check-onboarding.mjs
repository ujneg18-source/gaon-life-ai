/** 안내와 업무 데이터의 경계가 실제 API/저장소에 닿지 않는지 검증한다. */
import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert/strict";
import ts from "typescript";
const root = new URL("../", import.meta.url);
function load(path, globals = {}, require = () => ({})) {
  const code = ts.transpileModule(fs.readFileSync(new URL(path,root),"utf8"), {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText;
  const context = {exports:{},require,URL,...globals};
  vm.runInNewContext(code,context);return context.exports;
}
let calls = 0;
const window = {location:{pathname:"/guide/detail"}};
const workspace = load("lib/workspace.ts",{window,FormData:class {},fetch:async()=>{calls++;return {ok:true,status:200,json:async()=>({ok:true})};}});
for (const method of ["GET","POST","PATCH","DELETE"]) await assert.rejects(workspace.api("/claims/GA-2610-0482",{method}));
assert.equal(calls,0,"안내 경로에서는 실제 API 읽기와 쓰기 모두 금지");
window.location.pathname="/workspace/detail";
await workspace.api("/claims/GA-2610-0482");assert.equal(calls,1,"원래 업무 화면의 API 동작 유지");
const snapshot=JSON.parse(fs.readFileSync(new URL("lib/guide/snapshot.json",root),"utf8"));
const fixture=load("lib/guide/data.ts",{},()=>snapshot);
assert.equal(fixture.guideClaim.submitted_count,7);
assert.equal(fixture.guideClaim.required_count,8);
assert.equal(fixture.guideResource("/claims?q=김유정","").items[0].customer_name,"김유정");
assert.equal(fixture.guideResource("/supplements","sent")[0].status,"sent_mock");
assert.throws(()=>fixture.guideResource("/unavailable",""),/안내 예시에 없는/);
let effects=[],actualCalls=0;
const local={resolve:url=>fixture.guideResource(url,"")};
const hook=load("components/workspace-ui.tsx",{},name=>name==="react"?{useState:initial=>[initial,()=>{}],useEffect:fn=>effects.push(fn)}:name.includes("guide/context")?{useGuide:()=>local}:name.includes("workspace")?{api:()=>{actualCalls++;return Promise.resolve({});}}:{});
assert.equal(hook.useResource("/claims/GA-2610-0482").data.id,"GA-2610-0482");
effects.forEach(fn=>fn());assert.equal(actualCalls,0,"가이드 제공 시 useResource는 API를 호출하지 않음");
const {tours,tourKey}=load("lib/tours.ts");
assert.equal(Object.keys(tours).length,7);
for(const [key,steps] of Object.entries(tours)) {
  assert.ok(steps.length>=4,key);
  assert.match(steps.at(-1).description,/언제든 \?를/);
}
assert.equal(tourKey("/workspace/supplement"),"supplement");
assert.equal(tourKey("/workspace/history"),"history");
assert.equal(tourKey("/guide/home"),"");
console.log("PASS: 실제 API 차단/정상 화면 유지, 리소스 격리, 7개 독립 안내/종료, 가상 데이터 경계");

// 강조 대상을 가리지 않는 대표 배치와 화면 경계를 검증한다.
const {placeGuide}=load("lib/guide/placement.ts");
for(const target of [{x:16,y:100,w:220,h:300},{x:970,y:100,w:290,h:552},{x:260,y:150,w:1000,h:60},{x:1220,y:650,w:40,h:40}]) {
 const p=placeGuide(target,{w:410,h:250},{w:1280,h:720});
 assert.equal(p.separate,true);
 assert.ok(p.left>=16 && p.top>=16 && p.left+410<=1264 && p.top+250<=704);
 assert.ok(p.left+410<=target.x || p.left>=target.x+target.w || p.top+250<=target.y || p.top>=target.y+target.h);
}
console.log("PASS: 4방향 설명 배치·대상 비중첩");
