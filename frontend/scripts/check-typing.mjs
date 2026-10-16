/** 실제 훅을 가상 시계/모션 설정에서 실행해 속도·건너뛰기·모션 감소를 검증한다. */
import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert/strict";
import ts from "typescript";
const code = ts.transpileModule(
  fs.readFileSync(new URL("../lib/use-typing.ts", import.meta.url), "utf8"),
  {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
    },
  },
).outputText;
function scenario(reduced) {
  let state,
    effect,
    next,
    ran = false;
  const reference = { current: false };
  const react = {
    useRef: () => reference,
    useState: (initial) => {
      state ??= initial;
      return [
        state,
        (value) => {
          state = value;
        },
      ];
    },
    useEffect: (callback) => {
      if (!ran) {
        effect = callback;
        ran = true;
      }
    },
  };
  const context = {
    exports: {},
    require: () => react,
    performance: { now: () => 0 },
    window: { matchMedia: () => ({ matches: reduced }) },
    requestAnimationFrame: (callback) => {
      next = callback;
      return 1;
    },
    cancelAnimationFrame: () => {},
  };
  vm.runInNewContext(code, context);
  const hook = context.exports.useTyping;
  const text = "가".repeat(100);
  hook(text);
  effect();
  next(1000);
  let result = hook(text);
  assert.equal(result.text.length, reduced ? 100 : 50);
  result.skip();
  next(1020);
  result = hook(text);
  assert.equal(result.text, text);
  assert.equal(result.complete, true);
}
scenario(false);
scenario(true);
console.log(
  "typing: 50자/초, 클릭 건너뛰기 유지, reduced-motion 즉시 표시 통과",
);
