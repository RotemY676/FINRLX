import { expect, test } from "@playwright/test";

import { expectNoSeriousAxeViolations } from "./_helpers/axe";

/**
 * Onboarding is gated by auth. Without a real backend in CI, we just verify
 * the route returns SOMETHING (either the onboarding flow if the user is
 * authenticated, or a redirect to /login). Either is acceptable; what we're
 * smoke-testing is that the route compiles and renders without a server-side
 * crash.
 */
test.describe("Onboarding route", () => {
  test("loads without a server error", async ({ page }) => {
    const res = await page.goto("/onboarding");
    expect(res?.status()).toBeLessThan(500);

    // Dismiss disclaimer modal if present.
    const accept = page.getByRole("button", { name: /i understand/i });
    if (await accept.isVisible({ timeout: 1000 }).catch(() => false)) await accept.click();

    // Either onboarding renders or we got bounced to login/signup.
    const url = page.url();
    expect(url).toMatch(/\/(onboarding|login|signup|$)/);

    await expectNoSeriousAxeViolations(page);
  });
});
