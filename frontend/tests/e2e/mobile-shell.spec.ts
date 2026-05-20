import { expect, test } from "@playwright/test";

import { expectNoSeriousAxeViolations } from "./_helpers/axe";

/**
 * Phase UX-1.2 — mobile drawer for the sidebar.
 *
 * On <md (≤767px) the sidebar must be off-canvas. The burger in the
 * TopBar opens it as an overlay; the backdrop and a nav-link tap both
 * dismiss it.
 */
test.describe("Mobile shell drawer (375x667 — iPhone SE)", () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/**", (route) =>
      route.fulfill({
        status: 503,
        body: JSON.stringify({ detail: "backend offline for E2E smoke" }),
      })
    );
  });

  test("nav toggle opens the drawer; backdrop click closes it", async ({ page }) => {
    await page.goto("/");

    const accept = page.getByRole("button", { name: /i understand/i });
    if (await accept.isVisible({ timeout: 1000 }).catch(() => false)) await accept.click();

    const navButton = page.getByRole("button", { name: /open navigation/i });
    await expect(navButton).toBeVisible();
    await expect(navButton).toHaveAttribute("aria-expanded", "false");

    // Drawer is off-canvas — the aside exists but is translated -100%.
    // Asserting via aria-expanded is the cleanest semantic check.
    await navButton.click();
    await expect(
      page.getByRole("button", { name: /close navigation/i })
    ).toHaveAttribute("aria-expanded", "true");

    // The backdrop is the only top-level fixed element with the bg-ink/40
    // class. Click anywhere in its bounds (use a known mid-screen offset).
    await page.mouse.click(300, 400);
    await expect(navButton).toHaveAttribute("aria-expanded", "false");
  });

  test("page renders without serious a11y violations on mobile", async ({ page }) => {
    await page.goto("/");
    const accept = page.getByRole("button", { name: /i understand/i });
    if (await accept.isVisible({ timeout: 1000 }).catch(() => false)) await accept.click();

    await expect(page.locator('[data-disclaimer="true"]')).toBeVisible();
    await expectNoSeriousAxeViolations(page);
  });

  test("context pane toggle wires aria-expanded state both ways", async ({ page }) => {
    await page.goto("/");
    const accept = page.getByRole("button", { name: /i understand/i });
    if (await accept.isVisible({ timeout: 1000 }).catch(() => false)) await accept.click();
    await page.waitForLoadState("networkidle");

    const ctxToggle = page.getByRole("button", { name: /show context pane/i });
    await expect(ctxToggle).toBeVisible();
    await expect(ctxToggle).toHaveAttribute("aria-expanded", "false");

    await ctxToggle.click();
    // The button's accessible name flips on open — same control, opposite label.
    const ctxClose = page.getByRole("button", { name: /hide context pane/i });
    await expect(ctxClose).toBeVisible();
    await expect(ctxClose).toHaveAttribute("aria-expanded", "true");

    await ctxClose.click();
    await expect(page.getByRole("button", { name: /show context pane/i })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });
});
