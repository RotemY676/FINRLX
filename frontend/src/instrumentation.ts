/**
 * Next.js instrumentation hook (Phase MVP-7).
 *
 * Runs ONCE on server startup for both Node and Edge runtimes. We use it to
 * initialize Sentry conditionally: when SENTRY_DSN is unset (local dev, CI,
 * preview deploys without observability), this returns immediately and no
 * Sentry network traffic happens.
 *
 * The client-side Sentry init lives in `instrumentation-client.ts` (also
 * conditional on NEXT_PUBLIC_SENTRY_DSN) so the browser bundle stays small
 * when observability is off.
 */
export async function register() {
  const dsn = process.env.SENTRY_DSN;
  if (!dsn) return;

  const Sentry = await import("@sentry/nextjs");
  Sentry.init({
    dsn,
    environment: process.env.SENTRY_ENV ?? "development",
    tracesSampleRate: 0,
    sendDefaultPii: false,
  });
}
