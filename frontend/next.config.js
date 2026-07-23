/**
 * US-P0-05 — web hardening.
 *
 * Audit finding (2026-07-22): the backend sends seven security headers, and
 * `app/core/security_headers.py` states that "the frontend (Next.js) sets its
 * own CSP via next.config.js / meta tags". It did not. The live browser-facing
 * app was measured serving *zero* security headers — no CSP, no
 * X-Frame-Options, no HSTS. The documented control did not exist.
 *
 * Known limitation, deliberate: script-src keeps 'unsafe-inline'/'unsafe-eval'.
 * The root layout injects an inline theme script and Next's runtime needs eval,
 * so a nonce-based policy requires middleware plumbing. Removing them is the
 * follow-up; shipping the structural directives now already blocks framing,
 * base-tag hijacking, plugin content, form exfiltration to foreign origins, and
 * script/connect traffic to origins we never talk to.
 */
/*
 * `headers()` is evaluated at BUILD time and baked into routes-manifest.json —
 * `next start` never re-reads it. Verified: building without
 * NEXT_PUBLIC_API_BASE_URL and then starting *with* it still emitted
 * `connect-src 'self'`, which would have blocked every browser call to the
 * API and taken the app down. So this must not depend on the variable being
 * present at build time. The fallback is the same literal `src/services/api.ts`
 * already uses for exactly this reason; the two must stay in sync.
 */
const API_FALLBACK = "https://backend-production-aab8.up.railway.app";

const API_ORIGIN = (() => {
  try {
    return new URL(process.env.NEXT_PUBLIC_API_BASE_URL || API_FALLBACK).origin;
  } catch {
    return API_FALLBACK;
  }
})();

const SENTRY_ORIGIN = (() => {
  try {
    return new URL(process.env.NEXT_PUBLIC_SENTRY_DSN).origin;
  } catch {
    return "";
  }
})();

const CONNECT_SRC = ["'self'", API_ORIGIN, SENTRY_ORIGIN].filter(Boolean).join(" ");

const CSP = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "img-src 'self' data: blob:",
  /*
   * globals.css line 1 does `@import url("https://fonts.googleapis.com/...")`
   * for Inter Tight / Fraunces / JetBrains Mono, and that stylesheet then
   * pulls the actual woff2 files from fonts.gstatic.com. The first CSP shipped
   * without these two origins and silently killed every custom font in
   * production — the page still returned 200 and still rendered, just in
   * fallback system fonts, so a status-code check did not catch it.
   * Self-hosting via next/font would remove the dependency entirely; until
   * then these two origins are load-bearing. Keep in sync with globals.css.
   */
  "font-src 'self' data: https://fonts.gstatic.com",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  `connect-src ${CONNECT_SRC}`,
  "manifest-src 'self'",
  "worker-src 'self' blob:",
  "upgrade-insecure-requests",
].join("; ");

const SECURITY_HEADERS = [
  { key: "Content-Security-Policy", value: CSP },
  // frame-ancestors covers modern browsers; this covers the rest.
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "no-referrer" },
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
  {
    key: "Permissions-Policy",
    value: "geolocation=(), microphone=(), camera=(), payment=()",
  },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
  // LEAP S7b (D33): manual surfaces live under /pro; legacy URLs redirect
  // permanently so bookmarks and old links keep working.
  async redirects() {
    return [
      { source: "/admin", destination: "/pro/admin", permanent: true },
      { source: "/admin/:path*", destination: "/pro/admin/:path*", permanent: true },
      { source: "/analyze", destination: "/pro/analyze", permanent: true },
      { source: "/analyze/:path*", destination: "/pro/analyze/:path*", permanent: true },
      { source: "/backtests", destination: "/pro/backtests", permanent: true },
      { source: "/backtests/:path*", destination: "/pro/backtests/:path*", permanent: true },
      { source: "/comparison", destination: "/pro/comparison", permanent: true },
      { source: "/comparison/:path*", destination: "/pro/comparison/:path*", permanent: true },
      { source: "/decision", destination: "/pro/decision", permanent: true },
      { source: "/decision/:path*", destination: "/pro/decision/:path*", permanent: true },
      { source: "/integrations", destination: "/pro/integrations", permanent: true },
      { source: "/integrations/:path*", destination: "/pro/integrations/:path*", permanent: true },
      { source: "/news", destination: "/pro/news", permanent: true },
      { source: "/news/:path*", destination: "/pro/news/:path*", permanent: true },
      { source: "/operator", destination: "/pro/operator", permanent: true },
      { source: "/operator/:path*", destination: "/pro/operator/:path*", permanent: true },
      { source: "/ops", destination: "/pro/ops", permanent: true },
      { source: "/ops/:path*", destination: "/pro/ops/:path*", permanent: true },
      { source: "/paper", destination: "/pro/paper", permanent: true },
      { source: "/paper/:path*", destination: "/pro/paper/:path*", permanent: true },
      { source: "/policies", destination: "/pro/policies", permanent: true },
      { source: "/policies/:path*", destination: "/pro/policies/:path*", permanent: true },
      { source: "/replay", destination: "/pro/replay", permanent: true },
      { source: "/replay/:path*", destination: "/pro/replay/:path*", permanent: true },
      { source: "/research", destination: "/pro/research", permanent: true },
      { source: "/research/:path*", destination: "/pro/research/:path*", permanent: true },
      { source: "/risk", destination: "/pro/risk", permanent: true },
      { source: "/risk/:path*", destination: "/pro/risk/:path*", permanent: true },
      { source: "/templates", destination: "/pro/templates", permanent: true },
      { source: "/templates/:path*", destination: "/pro/templates/:path*", permanent: true },
      { source: "/universe", destination: "/pro/universe", permanent: true },
      { source: "/universe/:path*", destination: "/pro/universe/:path*", permanent: true },
    ];
  },
  experimental: {
    // Phase MVP-7: enables `src/instrumentation.ts` (Sentry init at server
    // startup). Stable as of Next 15; opt-in flag on 14.x.
    instrumentationHook: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
