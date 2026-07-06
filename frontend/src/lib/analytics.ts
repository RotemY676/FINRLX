/**
 * PostHog analytics wrapper (Phase MVP-7).
 *
 * The wrapper is a no-op when `NEXT_PUBLIC_POSTHOG_KEY` is missing — local
 * dev, CI, and any deploy without observability never touch PostHog. When
 * the key is set, `posthog-js` is dynamically imported on the first call,
 * so the bundle is unchanged for users / deploys that don't have it
 * configured.
 *
 * The five tracked events match the MVP plan:
 *   signup, first_rec_view, paper_trade, replay_open, disclaimer_accept
 *
 * Each event takes an optional payload object. PII is opt-in: by default
 * PostHog's autocapture is off and we only send what we explicitly pass.
 */

export type AnalyticsEvent =
  | "signup"
  | "first_rec_view"
  | "paper_trade"
  | "replay_open"
  | "disclaimer_accept"
  // LEAP D25 — Simple Mode events (no PII in properties)
  | "leap.simple_ticker_submitted"
  | "leap.dossier_rendered"
  | "leap.evidence_expanded"
  | "leap.scoreboard_opened"
  | "leap.compare_started";

type Posthog = {
  init: (key: string, config: Record<string, unknown>) => void;
  capture: (event: string, properties?: Record<string, unknown>) => void;
};

let posthogInstance: Posthog | null = null;
let initPromise: Promise<Posthog | null> | null = null;

async function getPosthog(): Promise<Posthog | null> {
  if (posthogInstance) return posthogInstance;
  if (initPromise) return initPromise;

  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!key || typeof window === "undefined") return null;

  initPromise = (async () => {
    const mod = await import("posthog-js");
    const posthog = mod.default;
    posthog.init(key, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com",
      // Autocapture off — we send explicit events only.
      autocapture: false,
      // Person profiles tied to identified users (we don't identify in MVP).
      person_profiles: "identified_only",
      // No session recording in MVP.
      disable_session_recording: true,
      capture_pageview: true,
    });
    posthogInstance = posthog as Posthog;
    return posthogInstance;
  })();

  return initPromise;
}

export async function track(
  event: AnalyticsEvent,
  properties?: Record<string, unknown>,
): Promise<void> {
  const ph = await getPosthog();
  if (!ph) return;
  ph.capture(event, properties);
}
