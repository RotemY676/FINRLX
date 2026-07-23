/**
 * US-P0-05 — the frontend must actually send security headers.
 *
 * This exists because the *documented* control did not match reality: the
 * backend module claimed the frontend set its own CSP, while the live site
 * was measured serving none. A comment is not a control; this test is.
 *
 * It reads next.config.js the way Next does, so a regression (someone drops
 * `headers()`, or widens the policy) fails here rather than silently in prod.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it, vi } from "vitest";

import nextConfig from "../../next.config.js";

async function headerMap(): Promise<Record<string, string>> {
  const rules = await nextConfig.headers();
  const all = rules.flatMap((r: { headers: { key: string; value: string }[] }) => r.headers);
  return Object.fromEntries(all.map((h: { key: string; value: string }) => [h.key, h.value]));
}

function csp(directives: string): Record<string, string> {
  return Object.fromEntries(
    directives
      .split(";")
      .map((d) => d.trim())
      .filter(Boolean)
      .map((d) => {
        const [name, ...rest] = d.split(/\s+/);
        return [name, rest.join(" ")];
      }),
  );
}

describe("frontend security headers", () => {
  it("applies to every path", async () => {
    const rules = await nextConfig.headers();
    expect(rules.some((r: { source: string }) => r.source === "/:path*")).toBe(true);
  });

  it("sends the defense-in-depth headers the backend already sends", async () => {
    const h = await headerMap();
    expect(h["X-Frame-Options"]).toBe("DENY");
    expect(h["X-Content-Type-Options"]).toBe("nosniff");
    expect(h["Referrer-Policy"]).toBe("no-referrer");
    expect(h["Strict-Transport-Security"]).toContain("max-age=");
    expect(h["Permissions-Policy"]).toContain("camera=()");
    expect(h["Cross-Origin-Opener-Policy"]).toBe("same-origin");
  });

  it("sends a CSP at all", async () => {
    expect((await headerMap())["Content-Security-Policy"]).toBeTruthy();
  });

  it("locks down the directives that cost nothing to enforce", async () => {
    const d = csp((await headerMap())["Content-Security-Policy"]);
    expect(d["frame-ancestors"]).toBe("'none'"); // clickjacking
    expect(d["object-src"]).toBe("'none'"); // legacy plugin execution
    expect(d["base-uri"]).toBe("'self'"); // <base> hijacking of relative URLs
    expect(d["form-action"]).toBe("'self'"); // form exfiltration to a foreign origin
    expect(d["default-src"]).toBe("'self'");
  });

  it("does not allow connect-src to reach arbitrary origins", async () => {
    const d = csp((await headerMap())["Content-Security-Policy"]);
    expect(d["connect-src"]).toContain("'self'");
    // A bare scheme or wildcard would make the directive meaningless.
    expect(d["connect-src"]).not.toMatch(/(^|\s)(\*|https:|http:)(\s|$)/);
  });

  it("always allows the backend origin, even with no build-time env", async () => {
    // Regression guard for a near-miss: headers() is baked into
    // routes-manifest.json at BUILD time, so a build without
    // NEXT_PUBLIC_API_BASE_URL used to emit `connect-src 'self'` — which would
    // have blocked every API call and taken the app down. The origin must
    // survive a missing env var.
    const saved = process.env.NEXT_PUBLIC_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    vi.resetModules();
    try {
      const fresh = await import("../../next.config.js");
      const rules = await fresh.default.headers();
      const value = rules
        .flatMap((r: { headers: { key: string; value: string }[] }) => r.headers)
        .find((h: { key: string }) => h.key === "Content-Security-Policy").value;
      expect(csp(value)["connect-src"]).toContain("backend-production-aab8");
    } finally {
      if (saved !== undefined) process.env.NEXT_PUBLIC_API_BASE_URL = saved;
      vi.resetModules();
    }
  });

  it("allows the font origins globals.css actually depends on", async () => {
    // Regression guard: the first CSP omitted these and silently broke every
    // custom font in production. The page still returned 200 in fallback
    // fonts, so only a font-specific assertion catches it. If globals.css
    // stops importing Google Fonts (e.g. moves to next/font), delete this.
    const globals = readFileSync(join(__dirname, "..", "app", "globals.css"), "utf8");
    const d = csp((await headerMap())["Content-Security-Policy"]);
    if (globals.includes("fonts.googleapis.com")) {
      expect(d["style-src"]).toContain("https://fonts.googleapis.com");
      expect(d["font-src"]).toContain("https://fonts.gstatic.com");
    }
  });

  it("never allows a wildcard default-src", async () => {
    const d = csp((await headerMap())["Content-Security-Policy"]);
    expect(d["default-src"]).not.toContain("*");
  });

  it("documents the known script-src weakening rather than hiding it", async () => {
    // Intentional today (inline theme script + Next runtime eval). Pinned so
    // that tightening it later is a deliberate, visible change.
    const d = csp((await headerMap())["Content-Security-Policy"]);
    expect(d["script-src"]).toContain("'self'");
    expect(d["script-src"]).toContain("'unsafe-inline'");
  });
});
