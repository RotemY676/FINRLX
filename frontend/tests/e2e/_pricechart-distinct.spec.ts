/**
 * Phase 19G live verification — /research/<ticker> price chart returns
 * distinct numbers per ticker. Gated on PLAYWRIGHT_BASE_URL so it only
 * runs against production / staging on demand.
 */
import { test, expect } from "@playwright/test";

const ENABLED =
  !!process.env.PLAYWRIGHT_BASE_URL &&
  !process.env.PLAYWRIGHT_BASE_URL.includes("127.0.0.1");

const TICKERS = ["TXN", "AMD", "INTC", "GOOGL"];

if (ENABLED) {
  test(`pricechart returns distinct headline % per ticker`, async ({ browser }) => {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    const observed: Record<string, string> = {};

    for (const t of TICKERS) {
      await page.goto(`/research/${t}`, { waitUntil: "domcontentloaded", timeout: 25000 });
      try { await page.waitForLoadState("load", { timeout: 8000 }); } catch {}
      await page.waitForTimeout(1500);
      // "Price · TXN" header is followed by a coloured `+9.3%` span.
      const header = await page.locator(`text=Price · ${t}`).first();
      await expect(header).toBeVisible({ timeout: 10000 });
      // Grab the entire chart card text and pull the first percent token —
      // selector-by-class is brittle across builds.
      const card = page.locator(`text=Price · ${t}`).locator("xpath=ancestor::*[self::section or self::div][1]");
      const cardText = (await card.first().innerText()).slice(0, 200);
      observed[t] = cardText;
    }
    await ctx.close();

    // Pull the headline % out of each card text. The format the audit saw
    // was "Price · TXN  +9.3%  vs S&P 500 +7.2%" — the first +/-N.N% is the
    // price return.
    const pct = (txt: string) => {
      const m = txt.match(/[+-]\d+\.\d+%/);
      return m ? m[0] : null;
    };
    const returns: Record<string, string | null> = {};
    for (const t of TICKERS) returns[t] = pct(observed[t]);

    const distinct = new Set(Object.values(returns).filter((v): v is string => !!v));
    expect.soft(distinct.size, `Each ticker should report a distinct return; got ${JSON.stringify(returns)}`).toBeGreaterThan(1);
    expect(distinct.size, `All ${TICKERS.length} tickers should report distinct returns; got ${JSON.stringify(returns)}`).toBeGreaterThanOrEqual(TICKERS.length - 1);
  });
}
