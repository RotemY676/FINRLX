/**
 * Regime honesty — the workspace strip must never assert a risk reading it
 * doesn't have. The dot colour is driven by the rule-based label, and an unknown
 * regime (logged out, or the price source down) paints neutral grey, not a
 * confident green/red. This pins the fix for the logged-out desk that used to
 * show a hardcoded "Risk-on" pill after /regime 401'd.
 */
import { describe, expect, it } from "vitest";

import { regimeDotClass } from "@/contexts/ScopeContext";

describe("regimeDotClass", () => {
  it("maps each known label to its own cue", () => {
    expect(regimeDotClass("uptrend", true)).toBe("bg-pos");
    expect(regimeDotClass("risk-off", true)).toBe("bg-breach");
    expect(regimeDotClass("downtrend", true)).toBe("bg-caution");
    expect(regimeDotClass("neutral", true)).toBe("bg-ink-3");
  });

  it("paints neutral grey when the regime is unknown, never a confident colour", () => {
    // known=false is the logged-out / source-down state.
    expect(regimeDotClass("—", false)).toBe("bg-ink-3");
    expect(regimeDotClass("uptrend", false)).toBe("bg-ink-3");
  });

  it("never invents a risk-on/off reading for an unrecognised label", () => {
    // The backend emits uptrend/downtrend/risk-off/neutral — nothing else. An
    // unexpected string must fall back to neutral, not a green/red assertion.
    expect(regimeDotClass("Risk-on", true)).toBe("bg-ink-3");
  });
});
