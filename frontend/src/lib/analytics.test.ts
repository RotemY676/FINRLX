import { describe, expect, it, vi, beforeEach } from "vitest";

import { track } from "./analytics";

describe("analytics.track", () => {
  beforeEach(() => {
    vi.resetModules();
    // ensure NEXT_PUBLIC_POSTHOG_KEY is absent
    delete (process.env as Record<string, string | undefined>).NEXT_PUBLIC_POSTHOG_KEY;
  });

  it("is a no-op when NEXT_PUBLIC_POSTHOG_KEY is unset", async () => {
    // Should NOT throw, NOT contact network, NOT call posthog.
    await expect(track("disclaimer_accept")).resolves.toBeUndefined();
  });

  it("accepts event names from the typed union without complaint", async () => {
    // The TS compiler is the gate here; this just checks runtime tolerance.
    await track("signup");
    await track("first_rec_view", { recommendation_id: "abc" });
    await track("paper_trade");
    await track("replay_open");
    await track("disclaimer_accept", { version: "v1" });
  });
});
