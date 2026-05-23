/**
 * Phase 19F — authenticated production sweep.
 *
 * Mirrors `_site-sweep.spec.ts` but exercises the auth-gated routes with a
 * real session. The session is established once per spec run via the
 * `storageState` mechanism so we don't hammer the login API.
 *
 * GATING. The spec is no-op unless all three env vars are set:
 *   SWEEP_AUTH=1
 *   PLAYWRIGHT_BASE_URL=https://frontend-production-7e8b1.up.railway.app
 *   SWEEP_AUTH_EMAIL=qa+sweep@finrlx.local       (or whatever the test user is)
 *   SWEEP_AUTH_PASSWORD=...                      (kept out of the repo)
 *
 * The intentional friction here is so the operator who runs the sweep has
 * to decide deliberately to authenticate against production. There is no
 * test account checked in, and there will not be — see PHASE_19_WORK_PLAN.md
 * §19F for the operator runbook.
 *
 * If you want to extend coverage: add an auth-only route to AUTH_ROUTES.
 * Per-test JSON findings land in
 * DOCS/handoff/_phase19f_auth_sweep_<date>/findings/.
 */
import { test, devices, type ConsoleMessage, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";

const ENABLED =
  process.env.SWEEP_AUTH === "1" &&
  !!process.env.PLAYWRIGHT_BASE_URL &&
  !!process.env.SWEEP_AUTH_EMAIL &&
  !!process.env.SWEEP_AUTH_PASSWORD;

const OUTPUT_DIR = path.resolve(
  __dirname,
  `../../../DOCS/handoff/_phase19f_auth_sweep_${new Date().toISOString().slice(0, 10)}`
);
const SCREENSHOT_DIR = path.join(OUTPUT_DIR, "screenshots");
const FINDINGS_DIR = path.join(OUTPUT_DIR, "findings");

// Routes that show meaningfully different content when authenticated. The
// public sweep already covers their logged-out shape — this spec catches
// regressions in the authed render (data fetches, ContextPane variants,
// per-user controls).
const AUTH_ROUTES = [
  "/",
  "/decision",
  "/research",
  "/backtests",
  "/paper",
  "/risk",
  "/replay",
  "/comparison",
  "/policies",
  "/universe",
  "/news",
  "/integrations",
  "/templates",
  "/profile",
  "/feedback",
  "/ops",
  "/operator",
];

const VIEWPORTS = [
  { name: "desktop-1920", config: { viewport: { width: 1920, height: 1080 }, isMobile: false } },
  {
    name: "iphone-15",
    config: devices["iPhone 15 Pro"] ?? devices["iPhone 13"] ?? { viewport: { width: 393, height: 852 }, isMobile: true, hasTouch: true },
  },
] as const;

async function loginAndCaptureStorage(): Promise<string> {
  // Returns a path to a storageState JSON. The path is unique per spec run
  // so concurrent local sweeps don't trample each other.
  const stateDir = path.resolve(__dirname, "../../.playwright-state");
  fs.mkdirSync(stateDir, { recursive: true });
  const statePath = path.join(stateDir, `auth-sweep-${process.pid}.json`);

  const { chromium } = await import("@playwright/test");
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto(`${process.env.PLAYWRIGHT_BASE_URL}/login`, { waitUntil: "domcontentloaded" });
  // Login form selectors mirror the canonical signup spec in tests/e2e/signup.spec.ts
  await page.getByLabel(/email/i).fill(process.env.SWEEP_AUTH_EMAIL!);
  await page.getByLabel(/password/i).fill(process.env.SWEEP_AUTH_PASSWORD!);
  await page.getByRole("button", { name: /sign in|log in/i }).click();
  // After login, AuthContext fetches /api/v1/me — wait for navigation off /login.
  await page.waitForURL((url) => !url.pathname.startsWith("/login"), { timeout: 15000 });
  await ctx.storageState({ path: statePath });
  await browser.close();
  return statePath;
}

type Finding = {
  route: string;
  viewport: string;
  status: "ok" | "fail";
  httpStatus?: number;
  consoleErrors: string[];
  pageErrors: string[];
  axe: {
    critical: number;
    serious: number;
    moderate: number;
    minor: number;
    rules: { id: string; impact: string; nodes: number }[];
  };
  screenshot: string;
  durationMs: number;
};

async function sweepRoute(page: Page, route: string, viewportName: string) {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const onConsole = (msg: ConsoleMessage) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  };
  const onPageError = (err: Error) => pageErrors.push(err.message);
  page.on("console", onConsole);
  page.on("pageerror", onPageError);

  const start = Date.now();
  let httpStatus: number | undefined;
  let status: "ok" | "fail" = "ok";
  const axeResults = {
    critical: 0, serious: 0, moderate: 0, minor: 0,
    rules: [] as { id: string; impact: string; nodes: number }[],
  };
  const safeName = route === "/" ? "_root" : route.replace(/^\//, "").replace(/[\/?]/g, "_");
  const screenshotPath = path.join(SCREENSHOT_DIR, viewportName, `${safeName}.png`);

  try {
    const response = await page.goto(route, { waitUntil: "domcontentloaded", timeout: 25000 });
    httpStatus = response?.status();
    try { await page.waitForLoadState("load", { timeout: 8000 }); } catch {}
    await page.waitForTimeout(1500);
    fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
    await page.screenshot({ path: screenshotPath, fullPage: true, animations: "disabled" });

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    for (const v of results.violations) {
      const impact = (v.impact ?? "minor") as "critical" | "serious" | "moderate" | "minor";
      if (impact === "critical") axeResults.critical++;
      else if (impact === "serious") axeResults.serious++;
      else if (impact === "moderate") axeResults.moderate++;
      else axeResults.minor++;
      axeResults.rules.push({ id: v.id, impact: v.impact ?? "minor", nodes: v.nodes.length });
    }
  } catch (err) {
    status = "fail";
    pageErrors.push(`navigation: ${(err as Error).message}`);
  } finally {
    page.off("console", onConsole);
    page.off("pageerror", onPageError);
  }

  fs.mkdirSync(FINDINGS_DIR, { recursive: true });
  fs.writeFileSync(
    path.join(FINDINGS_DIR, `${viewportName}__${safeName}.json`),
    JSON.stringify({
      route, viewport: viewportName, status, httpStatus,
      consoleErrors: consoleErrors.slice(0, 20),
      pageErrors: pageErrors.slice(0, 20),
      axe: axeResults,
      screenshot: path.relative(OUTPUT_DIR, screenshotPath),
      durationMs: Date.now() - start,
    } satisfies Finding, null, 2)
  );
}

if (ENABLED) {
  // One login per spec run; reused across all tests via storageState.
  let storageStatePath: string | null = null;
  test.beforeAll(async () => {
    storageStatePath = await loginAndCaptureStorage();
  });

  for (const vp of VIEWPORTS) {
    for (const route of AUTH_ROUTES) {
      test(`auth-sweep @ ${vp.name} :: ${route}`, async ({ browser }) => {
        const ctx = await browser.newContext({
          ...vp.config,
          storageState: storageStatePath ?? undefined,
        });
        const page = await ctx.newPage();
        try {
          await sweepRoute(page, route, vp.name);
        } finally {
          await ctx.close();
        }
      });
    }
  }
}
