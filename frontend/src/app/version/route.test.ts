/**
 * /version is the deploy-verification probe (Rule 12). If it ever silently
 * starts reporting nulls or gets cached, "is the newest commit live?" becomes
 * unanswerable again — which is exactly how a dead deploy trigger hid behind
 * healthy 200s during the RotemY676 migration. These tests pin the contract.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { GET } from "./route";

const GIT_ENV = [
  "RAILWAY_GIT_COMMIT_SHA",
  "RAILWAY_GIT_BRANCH",
  "RAILWAY_GIT_REPO_OWNER",
  "RAILWAY_GIT_REPO_NAME",
  "RAILWAY_DEPLOYMENT_ID",
  "RAILWAY_SERVICE_NAME",
  "RAILWAY_ENVIRONMENT_NAME",
] as const;

const saved: Record<string, string | undefined> = {};

beforeEach(() => {
  for (const key of GIT_ENV) {
    saved[key] = process.env[key];
    delete process.env[key];
  }
});

afterEach(() => {
  for (const key of GIT_ENV) {
    if (saved[key] === undefined) delete process.env[key];
    else process.env[key] = saved[key];
  }
});

describe("GET /version", () => {
  it("reports the deployed commit, branch and repo from Railway env", async () => {
    process.env.RAILWAY_GIT_COMMIT_SHA = "abc123def456";
    process.env.RAILWAY_GIT_BRANCH = "main";
    process.env.RAILWAY_GIT_REPO_OWNER = "RotemY676";
    process.env.RAILWAY_GIT_REPO_NAME = "FINRLX";

    const body = await GET().json();

    expect(body.commit).toBe("abc123def456");
    expect(body.branch).toBe("main");
    expect(body.repo).toBe("RotemY676/FINRLX");
    expect(typeof body.servedAt).toBe("string");
  });

  it("never caches — a cached answer would defeat the probe", () => {
    expect(GET().headers.get("cache-control")).toContain("no-store");
  });

  it("reports null rather than guessing when the env is absent", async () => {
    const body = await GET().json();

    expect(body.commit).toBeNull();
    expect(body.branch).toBeNull();
    expect(body.repo).toBeNull();
  });

  it("does not synthesise a repo from a half-populated env", async () => {
    process.env.RAILWAY_GIT_REPO_OWNER = "RotemY676";
    // name deliberately missing

    expect((await GET().json()).repo).toBeNull();
  });
});
