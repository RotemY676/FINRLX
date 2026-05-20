import { expect, test } from "@playwright/test";

import { expectNoSeriousAxeViolations } from "./_helpers/axe";

/**
 * Decision view smoke. Without a real backend we just confirm the route
 * renders (with a loading or empty state) and that the disclaimer banner
 * is in the render tree (the fintech-disclaimer-and-marketing-guard skill
 * requires every Recommendation surface to include it).
 */
test("decision page renders with disclaimer banner present", async ({ page }) => {
  // Block backend calls so the page falls into its empty/error state quickly.
  await page.route("**/api/v1/**", (route) => route.fulfill({
    status: 503,
    body: JSON.stringify({ detail: "backend offline for E2E smoke" }),
  }));

  const res = await page.goto("/decision");
  expect(res?.status()).toBeLessThan(500);

  const accept = page.getByRole("button", { name: /i understand/i });
  if (await accept.isVisible({ timeout: 1000 }).catch(() => false)) await accept.click();

  // The disclaimer banner MUST be in the tree on any Recommendation surface.
  await expect(page.locator('[data-disclaimer="true"]')).toBeVisible();

  await expectNoSeriousAxeViolations(page);
});
