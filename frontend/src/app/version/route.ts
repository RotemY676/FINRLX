/**
 * GET /version — what is actually deployed right now.
 *
 * Added 2026-07-22 after the GitHub-account migration (Rule 12). Until this
 * existed there was no way to ask the live site which commit it was serving:
 * `GET /` returning 200 only proves *a* build is up, not that the newest push
 * reached it. During the migration Railway kept serving a healthy old build
 * while pushes silently deployed nothing (the repo had no deployment trigger),
 * and 200s hid it. This endpoint makes that failure mode observable.
 *
 * Values come from the RAILWAY_GIT_* runtime variables the platform injects
 * into git-backed services, so it reports the true provenance of the running
 * build — repo owner included, which is what proves deploys come from
 * RotemY676/FINRLX and not the retired repo.
 *
 * Deliberately NOT under /api/*: next.config.js rewrites that prefix to the
 * backend, which would shadow this route.
 */
import { NextResponse } from "next/server";

// Never cache — a cached answer would defeat the point of the endpoint.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export function GET() {
  const owner = process.env.RAILWAY_GIT_REPO_OWNER ?? null;
  const name = process.env.RAILWAY_GIT_REPO_NAME ?? null;

  return NextResponse.json(
    {
      commit: process.env.RAILWAY_GIT_COMMIT_SHA ?? null,
      branch: process.env.RAILWAY_GIT_BRANCH ?? null,
      repo: owner && name ? `${owner}/${name}` : null,
      deploymentId: process.env.RAILWAY_DEPLOYMENT_ID ?? null,
      service: process.env.RAILWAY_SERVICE_NAME ?? null,
      environment: process.env.RAILWAY_ENVIRONMENT_NAME ?? null,
      servedAt: new Date().toISOString(),
    },
    { headers: { "cache-control": "no-store, max-age=0" } },
  );
}
