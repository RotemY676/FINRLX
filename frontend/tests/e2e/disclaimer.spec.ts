import { expect, test } from "@playwright/test";

import { expectNoSeriousAxeViolations } from "./_helpers/axe";

test.describe("Disclaimer modal and footer", () => {
  test("first visit shows the blocking modal and footer banner", async ({ page }) => {
    await page.goto("/pro");

    // Modal is the first interactive element.
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText(/not investment advice/i);

    // Footer banner is always present.
    await expect(page.locator('[data-disclaimer="true"]')).toBeVisible();

    await expectNoSeriousAxeViolations(page);
  });

  test("accepting the modal persists across reloads", async ({ page, context }) => {
    await page.goto("/pro");
    await page.getByRole("button", { name: /i understand/i }).click();
    await expect(page.getByRole("dialog")).toBeHidden();

    // localStorage acceptance must survive a hard reload.
    await page.reload();
    await expect(page.getByRole("dialog")).toBeHidden();

    // The banner stays visible after acceptance.
    await expect(page.locator('[data-disclaimer="true"]')).toBeVisible();
    await context.clearCookies();
  });

  test("the /disclaimer page renders standalone", async ({ page }) => {
    await page.goto("/disclaimer");
    await expect(page.getByRole("heading", { name: /^disclaimer$/i })).toBeVisible();
    await expect(page).toHaveTitle(/disclaimer/i);
    await expectNoSeriousAxeViolations(page);
  });
});
