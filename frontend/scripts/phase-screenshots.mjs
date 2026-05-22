// Phase screenshot capture script.
//
// Usage:
//   PHASE=3 BASE_URL=http://localhost:3000 node scripts/phase-screenshots.mjs
//
// Writes PNGs to ../DOCS/handoff/screenshots/phase{N}/.
// Captures each route at four viewports in both light and dark themes.
// Failure of one route does not abort the run.

import { chromium } from "playwright-core";
import { mkdirSync } from "node:fs";
import { join, resolve } from "node:path";

const PHASE = process.env.PHASE || "3";
const BASE_URL = process.env.BASE_URL || "http://localhost:3000";
const OUT_DIR = resolve(
  process.cwd(),
  "..",
  "DOCS",
  "handoff",
  "screenshots",
  `phase${PHASE}`,
);

const VIEWPORTS = [
  { name: "390", width: 390, height: 844 },
  { name: "768", width: 768, height: 1024 },
  { name: "1024", width: 1024, height: 768 },
  { name: "1440", width: 1440, height: 900 },
];

// Phase 3 captures a representative sample: home, decision (will likely
// show error state if backend is unreachable — that itself exercises the
// updated PageError typography), and a static legal page.
const ROUTES = [
  { path: "/", slug: "home" },
  { path: "/decision", slug: "decision" },
  { path: "/disclaimer", slug: "disclaimer" },
  { path: "/onboarding", slug: "onboarding" },
];

const THEMES = ["light", "dark"];

mkdirSync(OUT_DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const results = [];

for (const route of ROUTES) {
  for (const viewport of VIEWPORTS) {
    for (const theme of THEMES) {
      // Light / dark on the 768 and 1024 boards is overkill; cap them to one theme.
      if (theme === "dark" && (viewport.name === "768" || viewport.name === "1024")) {
        continue;
      }
      const filename = `phase${PHASE}_${route.slug}_${viewport.name}_${theme}.png`;
      const filepath = join(OUT_DIR, filename);
      const context = await browser.newContext({
        viewport: { width: viewport.width, height: viewport.height },
      });
      const page = await context.newPage();
      try {
        // Seed theme on the document before any client script runs.
        await context.addInitScript(
          ({ theme }) => {
            try {
              window.localStorage.setItem("finrlx-theme", theme);
            } catch {}
          },
          { theme },
        );
        await page.goto(`${BASE_URL}${route.path}`, {
          waitUntil: "domcontentloaded",
          timeout: 15000,
        });
        // Brief settle for client-side fetches to land their loading/error state.
        await page.waitForTimeout(1500);
        await page.screenshot({ path: filepath, fullPage: false });
        results.push({ filename, ok: true });
      } catch (err) {
        results.push({
          filename,
          ok: false,
          error: err instanceof Error ? err.message : String(err),
        });
      } finally {
        await context.close();
      }
    }
  }
}

await browser.close();

const ok = results.filter((r) => r.ok).length;
const fail = results.length - ok;
console.log(`Captured ${ok} / ${results.length} screenshots to ${OUT_DIR}`);
if (fail > 0) {
  console.log("Failures:");
  for (const r of results.filter((r) => !r.ok)) {
    console.log(`  ${r.filename}: ${r.error}`);
  }
}
