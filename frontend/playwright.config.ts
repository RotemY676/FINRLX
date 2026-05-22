import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config (Phase MVP-6e).
 *
 * The E2E suite runs against a live `next start` server. We do NOT spin up
 * the FastAPI backend here — the tests that need API responses mock them via
 * route interception. Flows that don't touch the backend (disclaimer, static
 * legal pages, signup/login form validation) run unmocked.
 *
 * Chromium-only by default to keep CI cheap. Local devs can override via
 * `npx playwright test --project=firefox` once those projects are uncommented.
 *
 * BASE_URL / PORT are env-driven so an already-running `next dev` (e.g. on
 * port 3001 when 3000 is taken) can be reused without editing this file.
 */
const PORT = process.env.PLAYWRIGHT_PORT ?? "3000";
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? `http://127.0.0.1:${PORT}`;
const DISABLE_WEBSERVER = process.env.PLAYWRIGHT_DISABLE_WEBSERVER === "1";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [["github"], ["list"]] : "list",
  timeout: 30_000,
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: DISABLE_WEBSERVER
    ? undefined
    : {
        command: "npm run start -- --hostname 127.0.0.1",
        url: BASE_URL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
        stdout: "pipe",
        stderr: "pipe",
      },
});
