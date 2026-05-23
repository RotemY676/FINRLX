import { test, devices, type ConsoleMessage, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";

const OUTPUT_DIR = path.resolve(__dirname, "../../../DOCS/handoff/_phase18sweep_2026-05-23");
const SCREENSHOT_DIR = path.join(OUTPUT_DIR, "screenshots");
const FINDINGS_DIR = path.join(OUTPUT_DIR, "findings");

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

const VIEWPORTS = [
  { name: "desktop-1920", config: { viewport: { width: 1920, height: 1080 }, isMobile: false } },
  { name: "desktop-1280", config: { viewport: { width: 1280, height: 800 }, isMobile: false } },
  {
    name: "iphone-15",
    config: devices["iPhone 15 Pro"] ?? devices["iPhone 13"] ?? { viewport: { width: 393, height: 852 }, isMobile: true, hasTouch: true },
  },
  {
    name: "pixel-8",
    config: devices["Pixel 7"] ?? { viewport: { width: 412, height: 915 }, isMobile: true, hasTouch: true },
  },
] as const;

const PUBLIC_ROUTES = [
  "/",
  "/login",
  "/signup",
  "/disclaimer",
  "/privacy",
  "/terms",
  "/help",
];

const AUTH_ROUTES = [
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
  "/admin",
  "/onboarding",
];

const ALL_ROUTES = [...PUBLIC_ROUTES, ...AUTH_ROUTES];

async function sweepRoute(page: Page, route: string, viewportName: string) {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];

  const onConsole = (msg: ConsoleMessage) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  };
  const onPageError = (err: Error) => {
    pageErrors.push(err.message);
  };
  page.on("console", onConsole);
  page.on("pageerror", onPageError);

  const start = Date.now();
  let httpStatus: number | undefined;
  let status: "ok" | "fail" = "ok";
  const axeResults = {
    critical: 0,
    serious: 0,
    moderate: 0,
    minor: 0,
    rules: [] as { id: string; impact: string; nodes: number }[],
  };
  const safeName = route === "/" ? "_root" : route.replace(/^\//, "").replace(/[\/?]/g, "_");
  const screenshotPath = path.join(SCREENSHOT_DIR, viewportName, `${safeName}.png`);

  try {
    const response = await page.goto(route, { waitUntil: "domcontentloaded", timeout: 25000 });
    httpStatus = response?.status();
    // Production has analytics + posthog + sentry — networkidle rarely fires.
    // Wait for any in-flight load, then a brief settle window.
    try {
      await page.waitForLoadState("load", { timeout: 8000 });
    } catch {}
    await page.waitForTimeout(1500);

    fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
    await page.screenshot({ path: screenshotPath, fullPage: true, animations: "disabled" });

    try {
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
    } catch (axeErr) {
      pageErrors.push(`axe error: ${(axeErr as Error).message}`);
    }
  } catch (err) {
    status = "fail";
    pageErrors.push(`navigation error: ${(err as Error).message}`);
  } finally {
    page.off("console", onConsole);
    page.off("pageerror", onPageError);
  }

  const finding: Finding = {
    route,
    viewport: viewportName,
    status,
    httpStatus,
    consoleErrors: consoleErrors.slice(0, 20),
    pageErrors: pageErrors.slice(0, 20),
    axe: axeResults,
    screenshot: path.relative(OUTPUT_DIR, screenshotPath),
    durationMs: Date.now() - start,
  };
  // Worker-safe: each test writes its own JSON file. afterAll-style aggregation
  // happens out-of-band in aggregate.py.
  fs.mkdirSync(FINDINGS_DIR, { recursive: true });
  const findingPath = path.join(FINDINGS_DIR, `${viewportName}__${safeName}.json`);
  fs.writeFileSync(findingPath, JSON.stringify(finding, null, 2));
}

// Gate: only register tests when the operator opted in (set RUN_SITE_SWEEP=1
// or PLAYWRIGHT_BASE_URL to a non-default URL). In CI we want this file to be
// a no-op so the build isn't dragged by 100 unmocked navigations against the
// CI-spawned localhost server. Phase 19.0.
const SWEEP_ENABLED =
  process.env.RUN_SITE_SWEEP === "1" ||
  (!!process.env.PLAYWRIGHT_BASE_URL &&
    !process.env.PLAYWRIGHT_BASE_URL.includes("127.0.0.1"));

if (SWEEP_ENABLED) {
  for (const vp of VIEWPORTS) {
    for (const route of ALL_ROUTES) {
      test(`sweep @ ${vp.name} :: ${route}`, async ({ browser }) => {
        const ctx = await browser.newContext({ ...vp.config });
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

