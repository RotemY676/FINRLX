import { expect, test, type Page } from "@playwright/test";

import { expectNoSeriousAxeViolations } from "./_helpers/axe";

/**
 * Desk v2 exit gate G-1 (SPEC-04 §3).
 *
 * Before this file there were no Desk v2 e2e specs at all — G-1 required "e2e
 * green" over a suite that did not exist, so the gate could never have been
 * evaluated. These cover the v2 surface behind its flag: the lane rail, the
 * reasoning it now expands, the degraded and unavailable states, keyboard
 * reachability, and axe at desktop and phone widths.
 *
 * The API is intercepted per the suite convention (playwright.config.ts): no
 * FastAPI process is started, so every payload here is an explicit fixture and
 * the assertions cannot silently depend on live market data.
 */

const TICKER = "TSTQ";

/** Six lanes in the closed SECTION_IDS order, covering all three DialStates. */
const STATUS_BODY = {
  data: {
    fingerprint: "gate-g1",
    computed_at: "2026-07-23T00:00:00Z",
    alerts_unseen: 0,
    sections: [
      { id: "technical", state: "live" },
      {
        id: "tournament",
        state: "degraded",
        reason: "RL leg queued (E7)",
        detail_code: "E7_GATED",
      },
      { id: "news", state: "live" },
      {
        id: "social",
        state: "unavailable",
        reason: "mentions-only fallback",
        detail_code: "E8_GATED",
        scope: "7d",
        freshness_bar: "2026-07-22",
      },
      { id: "fundamentals", state: "live" },
      { id: "sector", state: "degraded", reason: "benchmark view only" },
    ],
  },
};

const HEADER_BODY = {
  data: {
    ticker: TICKER,
    section: "header",
    generated_at: "2026-07-23T00:00:00Z",
    payload: {
      ticker: TICKER,
      summary: { stance: "hold", latest_close: 101.25 },
      freshness: { latest_bar: "2026-07-22", bars: 260 },
      alerts: [],
    },
  },
};

async function mockDesk(page: Page, opts: { statusStatus?: number } = {}) {
  // ORDER MATTERS: Playwright checks routes most-recently-registered first, so
  // the broadest patterns are registered FIRST and the specific ones last.
  // Registering the catch-all last silently swallowed /flags, which left
  // desk_v2 fail-closed and rendered the legacy desk — the spec then failed
  // against a component it was never meant to test.
  await page.route("**/api/v1/**", (route) =>
    route.fulfill({ status: 503, body: JSON.stringify({ detail: "offline for e2e" }) }),
  );

  // Every non-header section degrades — the desk must assemble anyway. This is
  // the per-section degradation contract, asserted rather than assumed.
  await page.route("**/api/v1/autopilot/desk/*/**", (route) =>
    route.fulfill({ status: 502, body: JSON.stringify({ detail: "section source down" }) }),
  );

  await page.route("**/api/v1/autopilot/desk/*/header*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(HEADER_BODY),
    }),
  );

  await page.route("**/api/v1/autopilot/desk/*/status*", (route) =>
    opts.statusStatus && opts.statusStatus !== 200
      ? route.fulfill({ status: opts.statusStatus, body: JSON.stringify({ error: {} }) })
      : route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(STATUS_BODY),
        }),
  );

  // Flag ON — v2 renders. The page is fail-closed to the legacy desk otherwise,
  // so without this the spec would silently test the wrong component.
  await page.route("**/api/v1/flags*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: { desk_v2: true } }),
    }),
  );
}

/**
 * Pre-accept the first-visit disclaimer.
 *
 * Clicking it after navigation is a race: the modal mounts on an effect, so a
 * visibility probe can run before it appears, leave it up, and then its
 * backdrop intercepts every subsequent click. Seeding the same localStorage
 * key the component writes removes the race entirely. Keys mirror
 * DisclaimerModal.tsx — if they change there, these must follow.
 */
async function preAcceptDisclaimer(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem("finrlx-disclaimer-accepted-v1", "v1");
  });
}

test.describe("Desk v2 — gate G-1", () => {
  test("renders the lane rail with every lane and its state in words", async ({ page }) => {
    await preAcceptDisclaimer(page);
    await mockDesk(page);
    const res = await page.goto(`/pro/desk/${TICKER}`);
    expect(res?.status()).toBeLessThan(500);

    await expect(page.getByTestId("engine-status-rail")).toBeVisible();
    for (const id of ["technical", "tournament", "news", "social", "fundamentals", "sector"]) {
      await expect(page.getByTestId(`dial-${id}`)).toBeVisible();
    }
    // NFR-4: state is never conveyed by colour alone.
    await expect(page.getByTestId("dial-technical")).toContainText("live");
    await expect(page.getByTestId("dial-tournament")).toContainText("degraded");
    await expect(page.getByTestId("dial-social")).toContainText("unavailable");
  });

  test("a lane expands into the reasoning behind its state", async ({ page }) => {
    await preAcceptDisclaimer(page);
    await mockDesk(page);
    await page.goto(`/pro/desk/${TICKER}`);

    await expect(page.getByTestId("dial-detail-tournament")).toHaveCount(0);
    await page.getByTestId("dial-tournament").click();

    const panel = page.getByTestId("dial-detail-tournament");
    await expect(panel).toBeVisible();
    await expect(panel).toContainText("RL leg queued (E7)"); // server reason, verbatim
    await expect(panel).toContainText(/reinforcement-learning/i); // E7_GATED explained
  });

  test("opens one lane at a time so the sticky header cannot bury the desk", async ({ page }) => {
    await preAcceptDisclaimer(page);
    await mockDesk(page);
    await page.goto(`/pro/desk/${TICKER}`);

    await page.getByTestId("dial-tournament").click();
    await expect(page.getByTestId("dial-detail-tournament")).toBeVisible();
    await page.getByTestId("dial-social").click();
    await expect(page.getByTestId("dial-detail-tournament")).toHaveCount(0);
    await expect(page.getByTestId("dial-detail-social")).toBeVisible();
  });

  test("lanes are keyboard reachable and operable (gate G-3)", async ({ page }) => {
    await preAcceptDisclaimer(page);
    await mockDesk(page);
    await page.goto(`/pro/desk/${TICKER}`);

    const lane = page.getByTestId("dial-technical");
    await lane.focus();
    await expect(lane).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("dial-detail-technical")).toBeVisible();
    expect(await lane.getAttribute("aria-expanded")).toBe("true");
  });

  test("hides the dials rather than guessing when status is unavailable", async ({ page }) => {
    await preAcceptDisclaimer(page);
    await mockDesk(page, { statusStatus: 503 });
    await page.goto(`/pro/desk/${TICKER}`);

    await expect(page.getByTestId("dial-row")).toHaveCount(0);
    await expect(page.getByTestId("status-unavailable")).toBeVisible();
  });

  test("a failing section degrades without taking the desk down", async ({ page }) => {
    await preAcceptDisclaimer(page);
    await mockDesk(page);
    await page.goto(`/pro/desk/${TICKER}`);

    // Header resolved; the rest 502'd. The verdict band must still be there.
    await expect(page.getByTestId("verdict-band")).toBeVisible();
  });

  test("is axe-clean at desktop width", async ({ page }) => {
    await preAcceptDisclaimer(page);
    await mockDesk(page);
    await page.goto(`/pro/desk/${TICKER}`);
    await expect(page.getByTestId("engine-status-rail")).toBeVisible();
    await expectNoSeriousAxeViolations(page);
  });

  test("is axe-clean with a lane expanded", async ({ page }) => {
    await preAcceptDisclaimer(page);
    await mockDesk(page);
    await page.goto(`/pro/desk/${TICKER}`);
    await page.getByTestId("dial-social").click();
    await expect(page.getByTestId("dial-detail-social")).toBeVisible();
    await expectNoSeriousAxeViolations(page);
  });
});

test.describe("Desk v2 @ 390x844 (iPhone 14)", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("the rail wraps and stays operable on a phone", async ({ page }) => {
    await preAcceptDisclaimer(page);
    await mockDesk(page);
    await page.goto(`/pro/desk/${TICKER}`);

    await expect(page.getByTestId("engine-status-rail")).toBeVisible();
    const lane = page.getByTestId("dial-technical");
    const box = await lane.boundingBox();
    // Apple HIG / WCAG 2.5.5 floor. The old dial was 30px and untappable.
    expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);

    await lane.click();
    await expect(page.getByTestId("dial-detail-technical")).toBeVisible();
    await expectNoSeriousAxeViolations(page);
  });
});

test.describe("Desk v2 flag OFF", () => {
  test("falls back to the legacy desk (G-7 rollback path)", async ({ page }) => {
    await page.route("**/api/v1/flags*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: { desk_v2: false } }),
      }),
    );
    await page.route("**/api/v1/**", (route) =>
      route.fulfill({ status: 503, body: JSON.stringify({ detail: "offline" }) }),
    );

    await page.goto(`/pro/desk/${TICKER}`);

    // The legacy desk is the fail-closed default; this is the rollback target.
    await expect(page.getByTestId("analyst-desk")).toBeVisible();
    await expect(page.getByTestId("engine-status-rail")).toHaveCount(0);
  });
});
