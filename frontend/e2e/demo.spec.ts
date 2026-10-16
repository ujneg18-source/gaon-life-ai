import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const root = path.resolve(__dirname, "../..");
const output = path.join(root, "artifacts/demo");
const questions = [
  "이 청구 건 서류 다 왔는지 검토해줘",
  "이 건 영수증에 보상 제외될 항목 있어?",
  "누락 서류 보완 요청 문자 써줘",
  "이 건 지급 심사로 넘겨도 돼?",
];
function reset() {
  return JSON.parse(
    execFileSync("uv", ["run", "python", "-m", "app.scripts.demo_reset"], {
      cwd: path.join(root, "backend"),
      encoding: "utf8",
      timeout: 30_000,
    }),
  );
}

test("촬영 동선 전체 리허설", async ({ page }) => {
  mkdirSync(output, { recursive: true });
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  const timings: Record<string, number> = {};
  const screenshots: string[] = [];
  const answers: unknown[] = [];
  let finalReset: unknown;
  const initialReset = reset();
  const segment = async (name: string, action: () => Promise<void>) => {
    const start = performance.now();
    await action();
    timings[name] = Math.round(performance.now() - start);
    const filename = `${String(screenshots.length + 1).padStart(2, "0")}-${name}.png`;
    await page.screenshot({
      path: path.join(output, filename),
      fullPage: true,
    });
    screenshots.push(filename);
  };
  try {
    await segment("login", async () => {
      await page.goto("/login");
      await page.getByRole("button", { name: /심사 담당자로 시작/ }).click();
      await expect(
        page.getByRole("heading", { name: /오늘은 어떤 업무/ }),
      ).toBeVisible();
    });
    await segment("main-onboarding", async () => {
      await page.getByRole("button", { name: "도움말 메뉴 열기" }).click();
      await page.getByRole("button", { name: /가이드라인/ }).click();
      const guide = page.frameLocator('iframe[title="독립된 화면 사용 안내"]');
      await expect(
        page.locator('.guide-frame[data-ready="true"]'),
      ).toBeVisible();
      for (let i = 0; i < 5; i++) {
        await guide
          .locator('[role="dialog"]')
          .screenshot({ path: path.join(output, `onboarding-${i + 1}.png`) });
        screenshots.push(`onboarding-${i + 1}.png`);
        await guide
          .getByRole("button", {
            name: i === 4 ? "안내 마침" : "다음 안내",
            exact: true,
          })
          .click();
      }
      await expect(page.locator(".guide-frame")).toHaveCount(0);
    });
    await segment("inbox", async () => {
      await page.getByRole("link", { name: /워크스페이스 열기/ }).click();
      await expect(
        page.getByRole("heading", { name: "청구 검토함" }),
      ).toBeVisible();
      await expect(
        page.getByRole("link", { name: "GA-2610-0482" }),
      ).toBeVisible();
    });
    await segment("detail-1", async () => {
      await page.getByRole("link", { name: "GA-2610-0482" }).click();
      await expect(
        page.getByRole("heading", { name: "김유정 고객 · 청구 상세" }),
      ).toBeVisible();
      await expect(page.locator('[data-tour="detail-step-0"]')).toHaveAttribute(
        "aria-current",
        "step",
      );
    });
    await segment("detail-2-comparison", async () => {
      await page.locator('[data-tour="detail-step-1"]').click();
      await expect(
        page.locator(".comparison-table tbody tr").first(),
      ).toBeVisible();
    });
    await segment("original-comparison", async () => {
      await page
        .getByRole("link", { name: /문서 분석·검토에서 원본으로 확인/ })
        .click();
      const compare = page.getByRole("button", { name: /원본 비교/ }).first();
      await expect(compare).toBeVisible();
      await compare.click();
      await expect(
        page.getByRole("heading", { name: "원본 비교", exact: true }),
      ).toBeVisible();
    });
    await segment("detail-3", async () => {
      await page.goto("/workspace/detail?claim=GA-2610-0482");
      await page.locator('[data-tour="detail-step-2"]').click();
      await expect(page.locator('[data-tour="detail-summary"]')).toBeVisible();
    });
    await segment("assistant", async () => {
      // 기존 화면의 버튼 문구를 그대로 사용한다.
      await page.getByRole("link", { name: "가온 AI에게 묻기" }).click();
      await expect(page).toHaveURL(/\/chat\?claim=GA-2610-0482/);
      await expect(
        page.getByRole("textbox", { name: "메시지", exact: true }),
      ).toBeVisible();
    });
    for (const [index, question] of questions.entries()) {
      await segment(`question-${index + 1}`, async () => {
        const responsePromise = page.waitForResponse(
          (r) =>
            r.url().endsWith("/api/chat") && r.request().method() === "POST",
          { timeout: 120_000 },
        );
        await page
          .getByRole("textbox", { name: "메시지", exact: true })
          .fill(question);
        await page
          .getByRole("textbox", { name: "메시지", exact: true })
          .press("Enter");
        const response = await responsePromise;
        expect(response.status()).toBe(200);
        const answer = await response.json();
        expect(answer.answer.length).toBeGreaterThan(0);
        answers.push({ question, ...answer });
        const body = page.getByTestId("answer-body").last();
        await expect(body).toBeVisible();
        await body.click();
        await expect(body).toHaveAttribute("aria-busy", "false");
      });
    }
    expect(errors).toEqual([]);
  } finally {
    finalReset = reset();
    // CLI의 초기화 버전을 프론트가 받아 채팅 메모리를 버리는 동작도 확인한다.
    writeFileSync(
      path.join(output, "report.json"),
      JSON.stringify(
        {
          viewport: { width: 1440, height: 900 },
          timings_ms: timings,
          screenshots,
          console_errors: errors,
          initial_reset: initialReset,
          final_reset: finalReset,
        },
        null,
        2,
      ),
    );
    await expect(page).toHaveURL(/\/$/, { timeout: 10_000 });
    await page.goto("/chat?claim=GA-2610-0482");
    await expect(
      page.getByRole("textbox", { name: "메시지", exact: true }),
    ).toBeVisible();
    await expect(page.getByTestId("answer-body")).toHaveCount(0);
    expect(errors).toEqual([]);
    await page.goto("/");
    writeFileSync(
      path.join(output, "answers.json"),
      JSON.stringify(answers, null, 2),
    );
  }
});
