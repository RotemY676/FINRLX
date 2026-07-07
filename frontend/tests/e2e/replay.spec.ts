import { expect, test } from "@playwright/test";

import { expectNoSeriousAxeViolations } from "./_helpers/axe";

test("replay page renders without a 500", async ({ page }) => {
  await page.route("**/api/v1/**", (route) => route.fulfill({
    status: 503,
    body: JSON.stringify({ detail: "backend offline for E2E smoke" }),
  }));

  const res = await page.goto("/pro/replay");
  expect(res?.status()).toBeLessThan(500);

  const accept = page.getByRole("button", { name: /i understand/i });
  if (await accept.isVisible({ timeout: 1000 }).catch(() => false)) await accept.click();

  await expect(page.locator('[data-disclaimer="true"]')).toBeVisible();
  await expectNoSeriousAxeViolations(page);
});
