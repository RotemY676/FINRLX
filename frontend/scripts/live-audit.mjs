// Live end-to-end audit of the production site. Visits each route in a real
// Chromium, records the visible <h1>/<h2> text, any console errors, and any
// failed network requests (status >= 400). Optionally signs in first when
// AUDIT_TOKEN is provided (a bearer obtained from the live auth API).
import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "node:fs";

const BASE = process.env.AUDIT_BASE || "https://frontend-production-7e8b1.up.railway.app";
const TOKEN = process.env.AUDIT_TOKEN || "";
const TAG = process.env.AUDIT_TAG || (TOKEN ? "authed" : "anon");
const OUT = `audit-out/${TAG}`;
mkdirSync(OUT, { recursive: true });

const ROUTES = [
  "/", "/simple", "/compare",
  "/pro", "/pro/desk/NVDA", "/pro/models", "/pro/analyze",
  "/pro/backtests", "/pro/comparison", "/pro/decision", "/pro/replay",
  "/pro/research", "/pro/risk", "/pro/news", "/pro/paper",
  "/pro/universe", "/pro/templates", "/pro/ops", "/pro/operator",
  "/pro/policies", "/pro/integrations",
];

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 } });

// Inject the bearer the way the app stores it, before any app code runs.
if (TOKEN) {
  await ctx.addInitScript((t) => {
    localStorage.setItem("finrlx_access_token", t);
  }, TOKEN);
}

const report = [];
for (const route of ROUTES) {
  const page = await ctx.newPage();
  const consoleErrors = [];
  const netErrors = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text().slice(0, 200));
  });
  page.on("response", (r) => {
    const s = r.status();
    if (s >= 400) netErrors.push(`${s} ${r.url().replace(/^https?:\/\/[^/]+/, "")}`);
  });

  let ok = true;
  let err = null;
  try {
    await page.goto(BASE + route, { waitUntil: "networkidle", timeout: 45000 });
    await page.waitForTimeout(1500); // let client fetches settle
  } catch (e) {
    ok = false;
    err = String(e).slice(0, 160);
  }

  // Visible headings + a sample of the main text, to judge "did anything render".
  const headings = await page
    .$$eval("h1,h2", (els) =>
      els.map((e) => e.textContent.trim()).filter(Boolean).slice(0, 8),
    )
    .catch(() => []);
  const bodyText = await page
    .$eval("body", (b) => (b.innerText || "").replace(/\s+/g, " ").trim())
    .catch(() => "");
  const slug = route.replace(/[^\w]+/g, "_") || "root";
  await page.screenshot({ path: `${OUT}/${slug}.png`, fullPage: false }).catch(() => {});

  report.push({
    route,
    ok,
    err,
    textLen: bodyText.length,
    headings,
    sample: bodyText.slice(0, 180),
    consoleErrors: [...new Set(consoleErrors)].slice(0, 4),
    netErrors: [...new Set(netErrors)].slice(0, 6),
  });
  await page.close();
}

await browser.close();
writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 2));

// Console summary
for (const r of report) {
  const flag = !r.ok ? "LOAD-FAIL" : r.textLen < 400 ? "NEAR-EMPTY" : "ok";
  console.log(`\n[${flag}] ${r.route}  (text=${r.textLen})`);
  if (r.headings.length) console.log("  h: " + r.headings.join(" | "));
  else console.log("  h: (none)");
  if (r.netErrors.length) console.log("  net: " + r.netErrors.join(", "));
  if (r.consoleErrors.length) console.log("  err: " + r.consoleErrors.join(" ;; "));
}
console.log(`\nTAG=${TAG}  wrote ${OUT}/report.json + screenshots`);
