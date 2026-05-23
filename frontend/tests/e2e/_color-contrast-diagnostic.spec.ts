/**
 * Phase 19B diagnostic — capture the actual failing fg/bg pairs (with element
 * selectors) from axe-core's color-contrast rule. The main sweep only captures
 * counts; this one dumps the full node detail so we can reason about which
 * tokens to adjust.
 *
 * Gate: requires RUN_COLOR_DIAG=1 + PLAYWRIGHT_BASE_URL.
 */
import { test, devices, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";

const ENABLED = process.env.RUN_COLOR_DIAG === "1" && !!process.env.PLAYWRIGHT_BASE_URL;

// Use the routes with the most color-contrast violations from PHASE_18J sweep.
const SAMPLE_ROUTES = ["/", "/decision", "/ops", "/research", "/help", "/backtests", "/policies", "/universe"];
const OUT = path.resolve(__dirname, "../../../DOCS/handoff/_phase19b_diag");

async function captureForRoute(page: Page, route: string, viewport: string) {
  await page.goto(route, { waitUntil: "domcontentloaded", timeout: 25000 });
  try {
    await page.waitForLoadState("load", { timeout: 8000 });
  } catch {}
  await page.waitForTimeout(1500);

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();

  const ccViolations = results.violations.filter((v) => v.id === "color-contrast");
  const detail = ccViolations.flatMap((v) =>
    v.nodes.map((n) => ({
      target: n.target.join(" "),
      html: n.html.slice(0, 200),
      failureSummary: n.failureSummary?.split("\n").map((l) => l.trim()).filter(Boolean),
      // axe enriches each node with `any[0].data` carrying the fg/bg pair
      // and the computed contrast ratio.
      data: n.any?.[0]?.data ?? null,
    }))
  );

  fs.mkdirSync(OUT, { recursive: true });
  const slug = route === "/" ? "_root" : route.replace(/^\//, "").replace(/\//g, "_");
  fs.writeFileSync(
    path.join(OUT, `${viewport}__${slug}.json`),
    JSON.stringify({ route, viewport, count: detail.length, nodes: detail }, null, 2)
  );
}

if (ENABLED) {
  for (const vp of [
    { name: "desktop-1920", config: { viewport: { width: 1920, height: 1080 } } },
    { name: "iphone-15", config: devices["iPhone 15 Pro"] ?? devices["iPhone 13"] },
  ]) {
    for (const route of SAMPLE_ROUTES) {
      test(`cc-diag @ ${vp.name} :: ${route}`, async ({ browser }) => {
        const ctx = await browser.newContext({ ...vp.config });
        const page = await ctx.newPage();
        try {
          await captureForRoute(page, route, vp.name);
        } finally {
          await ctx.close();
        }
      });
    }
  }
}
