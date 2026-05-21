/**
 * Help-center screenshot pipeline.
 *
 * Captures annotated-ready screenshots of the top contextual entry-point
 * pages on the live deploy. Each capture waits networkidle + 25 seconds
 * before taking the shot — this is the rule learned from the previous
 * project, where screenshots taken too early missed late-loading charts.
 *
 * Usage (PowerShell):
 *   $env:HELP_SHOT_BASE_URL = "https://frontend-production-7e8b1.up.railway.app"
 *   npx playwright install chromium   # one-time
 *   npx tsx scripts/help-screenshots.ts
 *
 * Output:
 *   frontend/public/help/screenshots/<slug>.png
 *
 * Notes:
 * - Public pages render with seeded demo data; auth-gated pages
 *   (/profile, /templates, /feedback) are skipped.
 * - Screenshots are full-viewport (1440x900) at DPR 2. Annotations are
 *   added in MDX via <Annotated>, not baked into the PNG.
 * - The script will fail loudly if any target returns non-200 or the
 *   page does not reach networkidle within 60s.
 */
import { chromium, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const BASE_URL = process.env.HELP_SHOT_BASE_URL || "https://frontend-production-7e8b1.up.railway.app";
const OUT_DIR = join(process.cwd(), "public", "help", "screenshots");
const VIEWPORT = { width: 1440, height: 900 } as const;
const DPR = 2;
const POST_NETIDLE_WAIT_MS = 25_000;
const NAV_TIMEOUT_MS = 60_000;

interface ShotTarget {
  slug: string;
  path: string;
  /** Optional CSS selector to assert exists before capture. */
  assert?: string;
  /** Optional theme. Defaults to light. */
  theme?: "light" | "dark";
}

const TARGETS: ShotTarget[] = [
  { slug: "home",           path: "/",             assert: "main" },
  { slug: "decision",       path: "/decision",     assert: "main" },
  { slug: "comparison",     path: "/comparison",   assert: "main" },
  { slug: "replay",         path: "/replay",       assert: "main" },
  { slug: "backtests",      path: "/backtests",    assert: "main" },
  { slug: "paper",          path: "/paper",        assert: "main" },
  { slug: "risk",           path: "/risk",         assert: "main" },
  { slug: "policies",       path: "/policies",     assert: "main" },
  { slug: "universe",       path: "/universe",     assert: "main" },
  { slug: "ops",            path: "/ops",          assert: "main" },
  { slug: "integrations",   path: "/integrations", assert: "main" },
  { slug: "news",           path: "/news",         assert: "main" },
  { slug: "admin",          path: "/admin",        assert: "main" },
  { slug: "help",           path: "/help",         assert: "main" },
];

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate((t) => {
    if (t === "dark") document.documentElement.setAttribute("data-theme", "dark");
    else document.documentElement.removeAttribute("data-theme");
  }, theme);
}

async function captureOne(page: Page, target: ShotTarget) {
  const url = new URL(target.path, BASE_URL).toString();
  console.log(`→ ${target.slug.padEnd(14)} navigating to ${url}`);

  const response = await page.goto(url, { waitUntil: "networkidle", timeout: NAV_TIMEOUT_MS });
  if (!response) throw new Error(`No response for ${url}`);
  const status = response.status();
  if (status >= 400) throw new Error(`HTTP ${status} for ${url}`);

  if (target.theme) await setTheme(page, target.theme);

  if (target.assert) {
    await page.waitForSelector(target.assert, { state: "visible", timeout: 10_000 });
  }

  // The hard-learned rule: even after networkidle, charts and animations
  // can still be settling. Wait an explicit 25 seconds before capturing.
  console.log(`  waiting ${POST_NETIDLE_WAIT_MS / 1000}s for late-loading content…`);
  await page.waitForTimeout(POST_NETIDLE_WAIT_MS);

  const outPath = join(OUT_DIR, `${target.slug}.png`);
  await page.screenshot({
    path: outPath,
    fullPage: false,
    clip: { x: 0, y: 0, ...VIEWPORT },
  });
  console.log(`  saved ${outPath}`);
}

async function main() {
  mkdirSync(OUT_DIR, { recursive: true });
  console.log(`Help screenshots — base URL: ${BASE_URL}`);
  console.log(`                   output:   ${OUT_DIR}`);
  console.log(`                   viewport: ${VIEWPORT.width}×${VIEWPORT.height} @${DPR}x`);
  console.log("");

  const browser = await chromium.launch();
  try {
    const context = await browser.newContext({
      viewport: VIEWPORT,
      deviceScaleFactor: DPR,
      reducedMotion: "reduce",
    });
    // Pre-seed localStorage so the disclaimer modal does not block captures.
    // The DisclaimerModal component reads this key (see frontend/src/components/legal/DisclaimerModal.tsx).
    await context.addInitScript(() => {
      try {
        window.localStorage.setItem("finrlx-disclaimer-accepted-v1", "v1");
      } catch {
        // localStorage may be unavailable in some contexts — ignore.
      }
    });
    const page = await context.newPage();
    let ok = 0;
    let failed = 0;
    for (const target of TARGETS) {
      try {
        await captureOne(page, target);
        ok++;
      } catch (err) {
        failed++;
        console.error(`✗ ${target.slug}: ${(err as Error).message}`);
      }
    }
    console.log("");
    console.log(`Done. ${ok} captured, ${failed} failed.`);
    if (failed > 0) process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
