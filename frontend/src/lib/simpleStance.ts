/**
 * LEAP S5 — Simple Mode stance mapping (binding, SIMPLE_MODE_SPEC §2/J2).
 *
 * The backend payload's `summary.stance` uses engine vocabulary
 * (`buy` / `hold` / `sell`, occasionally `trim`) consumed by Pro surfaces.
 * Simple Mode NEVER renders those words: this module is the single UI
 * boundary where they become research language. The wording test asserts
 * the raw words never appear in Simple Mode component sources.
 */

export type SimpleStance = "constructive" | "neutral" | "cautious";

const STANCE_MAP: Record<string, SimpleStance> = {
  buy: "constructive",
  hold: "neutral",
  sell: "cautious",
  trim: "cautious",
};

export function toSimpleStance(payloadStance: string | null | undefined): SimpleStance {
  if (!payloadStance) return "neutral";
  return STANCE_MAP[payloadStance.toLowerCase()] ?? "neutral";
}

/** Token families per stance (D14: existing globals.css tokens only). */
export function stanceTone(stance: SimpleStance): "pos" | "neutral" | "caution" {
  if (stance === "constructive") return "pos";
  if (stance === "cautious") return "caution";
  return "neutral";
}

export const STANCE_HOVER_LABEL =
  "Research stance from the engine ensemble — not advice.";

/**
 * Strings that must never appear in Simple Mode UI source (copy-deck ban
 * list + the payload's raw stance vocabulary). The wording test scans
 * component files for these as standalone words.
 */
export const SIMPLE_MODE_BANNED_WORDS = [
  "buy",
  "sell",
  "should",
  "must",
  "guaranteed",
  "outperform",
  "opportunity",
  "act now",
] as const;
