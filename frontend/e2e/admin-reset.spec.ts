import { test, expect } from "@playwright/test";

test("관리자 초기화 버튼 확인·취소·실행", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: /관리자로 시작/ }).click();
  await page.goto("/workspace/operations");
  const reset = page.getByRole("button", { name: "시연 초기화", exact: true });
  await expect(reset).toBeVisible();
  page.once("dialog", (dialog) => dialog.dismiss());
  await reset.click();
  await expect(reset).toBeEnabled();
  page.once("dialog", (dialog) => dialog.accept());
  const response = page.waitForResponse((r) =>
    r.url().endsWith("/api/demo/reset"),
  );
  await reset.click();
  expect((await response).status()).toBe(200);
  await expect(page).toHaveURL(/\/login/);
  await expect(
    page.getByRole("button", { name: /심사 담당자로 시작/ }),
  ).toBeVisible();
});
