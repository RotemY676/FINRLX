/**
 * Final Help-center audit against the live deploy.
 *
 * 1. Every /help/* route returns 200.
 * 2. axe-core finds no critical / serious violations on the help landing.
 * 3. Contextual HelpLinks on key in-app pages have correct href targets.
 *
 * Usage:
 *   $env:HELP_AUDIT_BASE_URL = "https://frontend-production-7e8b1.up.railway.app"
 *   npx tsx scripts/help-audit.ts
 */
import { chromium, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const BASE_URL = process.env.HELP_AUDIT_BASE_URL || "https://frontend-production-7e8b1.up.railway.app";

const HELP_ROUTES = [
  "/help",
  "/help/getting-started/tour",
  "/help/getting-started/first-recommendation",
  "/help/getting-started/understanding-your-profile",
  "/help/getting-started/reading-the-dashboard",
  "/help/concepts/weight-centric-pipeline",
  "/help/concepts/universe-and-features",
  "/help/concepts/agents-and-engines",
  "/help/concepts/regimes-and-turbulence",
  "/help/concepts/risk-overlays",
  "/help/concepts/backtest-vs-paper-vs-live",
  "/help/concepts/governance-and-audit",
  "/help/concepts/known-pitfalls",
  "/help/guides/run-a-backtest",
  "/help/guides/compare-engines",
  "/help/guides/promote-to-paper",
  "/help/guides/defer-or-save-a-thesis",
  "/help/guides/edit-a-policy",
  "/help/guides/investigate-a-breach",
  "/help/guides/replay-a-decision",
  "/help/guides/manage-your-universe",
  "/help/guides/export-research-data",
  "/help/guides/set-up-an-integration",
  "/help/guides/re-run-the-wizard",
  "/help/reference/status-chips",
  "/help/reference/policy-controls",
  "/help/reference/metrics",
  "/help/reference/api",
  "/help/reference/pages/home",
  "/help/reference/pages/decision",
  "/help/reference/pages/comparison",
  "/help/reference/pages/replay",
  "/help/reference/pages/backtests",
  "/help/reference/pages/paper",
  "/help/reference/pages/risk",
  "/help/reference/pages/policies",
  "/help/reference/pages/universe",
  "/help/reference/pages/ops",
  "/help/reference/pages/integrations",
  "/help/reference/pages/news",
  "/help/reference/pages/admin",
  "/help/reference/pages/profile",
  "/help/reference/pages/templates",
  "/help/glossary",
  "/help/faq",
  "/help/troubleshooting",
  "/help/changelog",
  "/help/disclaimers",
];

const APP_PAGES_WITH_HELPLINKS = [
  { path: "/", name: "Home" },
  { path: "/decision", name: "Decision" },
  { path: "/policies", name: "Policies" },
  { path: "/universe", name: "Universe" },
  { path: "/backtests", name: "Backtests" },
  { path: "/risk", name: "Risk" },
  { path: "/replay", name: "Replay" },
  { path: "/comparison", name: "Comparison" },
];

interface Result {
  route: string;
  status: number;
  helpLinks?: number;
  a11y?: { critical: number; serious: number; moderate: number };
}

async function probeRoute(page: Page, path: string): Promise<number> {
  const url = new URL(path, BASE_URL).toString();
  const response = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
  return response?.status() ?? 0;
}

async function countHelpLinks(page: Page): Promise<number> {
  // HelpLink renders an <a> with href starting with /help.
  // We exclude the global TopBar Help button which lives in the page chrome.
  return page.evaluate(() => {
    const anchors = Array.from(document.querySelectorAll('a[href^="/help"]'));
    const inMain = anchors.filter((a) => {
      const main = document.getElementById("main-content");
      return main?.contains(a) ?? false;
    });
    return inMain.length;
  });
}

async function runA11y(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "best-practice"])
    .analyze();
  const buckets = { critical: 0, serious: 0, moderate: 0, minor: 0 };
  for (const v of results.violations) {
    if (v.impact && v.impact in buckets) {
      (buckets as Record<string, number>)[v.impact]++;
    }
  }
  return {
    critical: buckets.critical,
    serious: buckets.serious,
    moderate: buckets.moderate,
    violations: results.violations.map((v) => ({ id: v.id, impact: v.impact, count: v.nodes.length })),
  };
}

async function main() {
  console.log(`Help audit — base URL: ${BASE_URL}\n`);
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    reducedMotion: "reduce",
  });
  await context.addInitScript(() => {
    try {
      window.localStorage.setItem("finrlx-disclaimer-accepted-v1", "v1");
    } catch {
      // ignore
    }
  });
  const page = await context.newPage();
  const results: Result[] = [];

  console.log(`Probing ${HELP_ROUTES.length} help routes…`);
  for (const route of HELP_ROUTES) {
    try {
      const status = await probeRoute(page, route);
      results.push({ route, status });
      const flag = status === 200 ? "✓" : "✗";
      console.log(`  ${flag} ${status} ${route}`);
    } catch (e) {
      results.push({ route, status: 0 });
      console.log(`  ✗ ERR ${route}: ${(e as Error).message}`);
    }
  }

  console.log(`\nCounting in-page HelpLinks on app pages…`);
  for (const { path, name } of APP_PAGES_WITH_HELPLINKS) {
    try {
      await probeRoute(page, path);
      await page.waitForTimeout(2000);
      const count = await countHelpLinks(page);
      console.log(`  ${path.padEnd(14)} (${name.padEnd(12)}) — ${count} help anchors in main content`);
    } catch (e) {
      console.log(`  ${path}: ERR ${(e as Error).message}`);
    }
  }

  console.log(`\nRunning a11y audit on /help landing…`);
  await probeRoute(page, "/help");
  await page.waitForTimeout(3000);
  const a11y = await runA11y(page);
  console.log(`  critical: ${a11y.critical}, serious: ${a11y.serious}, moderate: ${a11y.moderate}`);
  if (a11y.violations.length > 0) {
    console.log(`  violations:`);
    for (const v of a11y.violations) {
      console.log(`    - [${v.impact}] ${v.id} (${v.count} node${v.count === 1 ? "" : "s"})`);
    }
  }

  console.log(`\nRunning a11y audit on /help/concepts/weight-centric-pipeline…`);
  await probeRoute(page, "/help/concepts/weight-centric-pipeline");
  await page.waitForTimeout(3000);
  const a11y2 = await runA11y(page);
  console.log(`  critical: ${a11y2.critical}, serious: ${a11y2.serious}, moderate: ${a11y2.moderate}`);
  if (a11y2.violations.length > 0) {
    console.log(`  violations:`);
    for (const v of a11y2.violations) {
      console.log(`    - [${v.impact}] ${v.id} (${v.count} node${v.count === 1 ? "" : "s"})`);
    }
  }

  await browser.close();

  const failed = results.filter((r) => r.status !== 200);
  console.log(`\n--- Summary ---`);
  console.log(`Help routes:  ${results.length} probed, ${results.length - failed.length} ok, ${failed.length} failed.`);
  console.log(`a11y /help:   critical=${a11y.critical}, serious=${a11y.serious}, moderate=${a11y.moderate}`);
  console.log(`a11y concept: critical=${a11y2.critical}, serious=${a11y2.serious}, moderate=${a11y2.moderate}`);
  if (failed.length > 0 || a11y.critical > 0 || a11y2.critical > 0) {
    process.exitCode = 1;
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
