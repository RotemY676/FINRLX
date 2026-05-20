"use client";

import { useEffect } from "react";

/**
 * Client-side Sentry initializer (Phase MVP-7).
 *
 * Mounted once in the root layout. No-op when NEXT_PUBLIC_SENTRY_DSN is empty,
 * so the @sentry/nextjs runtime is dynamically imported only when the user
 * has actually configured observability.
 */
export function SentryClientInit() {
  useEffect(() => {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (!dsn) return;

    void import("@sentry/nextjs").then((Sentry) => {
      Sentry.init({
        dsn,
        environment: process.env.NEXT_PUBLIC_SENTRY_ENV ?? "development",
        tracesSampleRate: 0,
        sendDefaultPii: false,
      });
    });
  }, []);

  return null;
}
