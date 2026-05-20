import { expect, test } from "@playwright/test";

test.describe("Admin page @ 375x667 (iPhone SE)", () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/**", (route) =>
      route.fulfill({
        status: 503,
        body: JSON.stringify({ detail: "backend offline for E2E smoke" }),
      })
    );
  });

  test("shows the desktop-only notice; 'Continue anyway' loads the full shell", async ({ page }) => {
    await page.goto("/admin");

    const accept = page.getByRole("button", { name: /i understand/i });
    if (await accept.isVisible({ timeout: 1000 }).catch(() => false)) await accept.click();

    // Notice copy is visible on mobile.
    await expect(page.getByRole("heading", { name: /desktop only/i })).toBeVisible();
    const continueBtn = page.getByRole("button", { name: /continue anyway/i });
    await expect(continueBtn).toBeVisible();

    // Opt-in path mounts the heavy AdminShell.
    await continueBtn.click();
    await expect(page.getByRole("heading", { name: /desktop only/i })).toBeHidden();
  });
});

test.describe("Admin page @ 1280x720 (desktop)", () => {
  test.use({ viewport: { width: 1280, height: 720 } });

  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/**", (route) =>
      route.fulfill({
        status: 503,
        body: JSON.stringify({ detail: "backend offline for E2E smoke" }),
      })
    );
  });

  test("desktop renders the full AdminShell — no notice", async ({ page }) => {
    await page.goto("/admin");
    const accept = page.getByRole("button", { name: /i understand/i });
    if (await accept.isVisible({ timeout: 1000 }).catch(() => false)) await accept.click();

    await expect(page.getByRole("heading", { name: /desktop only/i })).toHaveCount(0);
  });
});
