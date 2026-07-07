import { expect, test } from "@playwright/test";

import { expectNoSeriousAxeViolations } from "./_helpers/axe";

test.describe("News intelligence @ 375x667 (iPhone SE)", () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/**", (route) =>
      route.fulfill({
        status: 503,
        body: JSON.stringify({ detail: "backend offline for E2E smoke" }),
      })
    );
  });

  test("renders without 500 and is axe-clean on mobile", async ({ page }) => {
    const res = await page.goto("/pro/news");
    expect(res?.status()).toBeLessThan(500);

    const accept = page.getByRole("button", { name: /i understand/i });
    if (await accept.isVisible({ timeout: 1000 }).catch(() => false)) await accept.click();

    await expect(page.locator('[data-disclaimer="true"]')).toBeVisible();
    await expectNoSeriousAxeViolations(page);
  });
});
