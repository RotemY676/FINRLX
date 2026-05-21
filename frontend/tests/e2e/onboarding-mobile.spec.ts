import { expect, test } from "@playwright/test";

import { expectNoSeriousAxeViolations } from "./_helpers/axe";

/**
 * Phase W-6 — investor-profile wizard mobile + a11y smoke.
 *
 * Stubs every backend call to 503 so the wizard renders its "loading"
 * fallback or its login redirect — both render the same chrome. We only
 * smoke-test that the wizard route compiles, renders without a 500, and
 * produces zero serious / critical axe violations at three viewports.
 *
 * The full happy-path (signup → questions → submit) lives in W-8.
 */
const SCENARIOS = [
  { name: "375x667 (iPhone SE)", viewport: { width: 375, height: 667 } },
  { name: "768x1024 (iPad portrait)", viewport: { width: 768, height: 1024 } },
  { name: "1280x720 (desktop)", viewport: { width: 1280, height: 720 } },
];

for (const scenario of SCENARIOS) {
  test.describe(`Investor-profile wizard @ ${scenario.name}`, () => {
    test.use({ viewport: scenario.viewport });

    test.beforeEach(async ({ page }) => {
      await page.route("**/api/v1/**", (route) =>
        route.fulfill({
          status: 503,
          body: JSON.stringify({ detail: "backend offline for E2E smoke" }),
        })
      );
    });

    test("loads /onboarding without a 500 and is axe-clean", async ({ page }) => {
      const res = await page.goto("/onboarding");
      expect(res?.status()).toBeLessThan(500);

      // Dismiss disclaimer if present.
      const accept = page.getByRole("button", { name: /i understand/i });
      if (await accept.isVisible({ timeout: 1000 }).catch(() => false)) await accept.click();

      // The page may either render the wizard chrome (progressbar) or
      // bounce to /login (no auth, no API). Both are acceptable for the
      // a11y smoke. We assert axe-cleanness regardless.
      const onLogin = page.url().endsWith("/login");
      if (!onLogin) {
        // Wizard rendered — verify progressbar is exposed.
        const progressbar = page.getByRole("progressbar").first();
        await expect(progressbar).toBeVisible();
      }

      await expectNoSeriousAxeViolations(page);
    });
  });
}
