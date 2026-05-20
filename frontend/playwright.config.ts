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
 */
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [["github"], ["list"]] : "list",
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: {
    command: "npm run start -- --hostname 127.0.0.1",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
