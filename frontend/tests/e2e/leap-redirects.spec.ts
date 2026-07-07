/**
 * LEAP S7b — legacy manual routes 308 to /pro (gate G5.1 analogue).
 * Runs wherever Playwright browsers are available (env-blocked in the
 * program's build sandbox; part of the F3/C1 sweep run).
 */
import { expect, test } from "@playwright/test";

const MOVED = ["admin","analyze","backtests","comparison","decision","integrations",
  "news","operator","ops","paper","policies","replay","research","risk",
  "templates","universe"];

for (const r of MOVED) {
  test(`/${r} permanently redirects to /pro/${r}`, async ({ request }) => {
    const res = await request.get(`/${r}`, { maxRedirects: 0 });
    expect(res.status()).toBe(308);
    expect(res.headers()["location"]).toBe(`/pro/${r}`);
  });
}
