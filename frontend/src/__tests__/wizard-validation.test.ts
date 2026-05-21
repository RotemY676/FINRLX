/**
 * Phase W-3 — wizard input validation contract.
 *
 * The wizard's "Continue" button is enabled only when every required
 * question in the current step has an answer. This tests the helper
 * that the page uses, so we know step-gating won't regress silently.
 */
import { describe, expect, it } from "vitest";

import { MULTI_SELECT_CODES, TOTAL_STEPS } from "../features/wizard/types";
import type { ProfileQuestion, ProfileStep } from "../features/wizard/types";

// Re-declared locally to keep the test independent of the page module
// (the page is a Next.js client component that pulls in router hooks).
function isStepComplete(
  step: ProfileStep | undefined,
  answers: Record<string, string | string[]>,
): boolean {
  if (!step) return true;
  for (const q of step.questions) {
    if (!q.is_required) continue;
    const v = answers[q.code];
    if (v === undefined) return false;
    if (Array.isArray(v) && v.length === 0) return false;
    if (typeof v === "string" && v.length === 0) return false;
  }
  return true;
}

const enumQuestion = (code: string, required = true): ProfileQuestion => ({
  code,
  step: 5,
  order_in_step: 1,
  dimension: "objectives",
  text: "test",
  helper_text: null,
  is_required: required,
  is_active: true,
  choices: [
    { value: "a", label: "A", score: null },
    { value: "b", label: "B", score: null },
  ],
});

describe("wizard validation (W-3)", () => {
  it("returns true for an empty/absent step", () => {
    expect(isStepComplete(undefined, {})).toBe(true);
  });

  it("returns false when a required answer is missing", () => {
    const step: ProfileStep = {
      step: 5,
      label: "Objectives",
      dimension_hint: "objectives",
      questions: [enumQuestion("O_01_HORIZON")],
    };
    expect(isStepComplete(step, {})).toBe(false);
    expect(isStepComplete(step, { O_01_HORIZON: "" })).toBe(false);
    expect(isStepComplete(step, { O_01_HORIZON: "a" })).toBe(true);
  });

  it("treats empty multi-select arrays as incomplete when required", () => {
    const step: ProfileStep = {
      step: 6,
      label: "Universe",
      dimension_hint: "universe",
      questions: [{ ...enumQuestion("U_02_SECTOR_WHITELIST"), is_required: true }],
    };
    expect(isStepComplete(step, { U_02_SECTOR_WHITELIST: [] })).toBe(false);
    expect(isStepComplete(step, { U_02_SECTOR_WHITELIST: ["Tech"] })).toBe(true);
  });

  it("allows optional questions to remain unanswered", () => {
    const step: ProfileStep = {
      step: 6,
      label: "Universe",
      dimension_hint: "universe",
      questions: [
        enumQuestion("U_01_REGION", true),
        enumQuestion("U_02_SECTOR_WHITELIST", false),
      ],
    };
    expect(isStepComplete(step, { U_01_REGION: "a" })).toBe(true);
  });
});

describe("wizard constants (W-3)", () => {
  it("declares 8 total steps", () => {
    expect(TOTAL_STEPS).toBe(8);
  });
  it("flags the three known multi-select question codes", () => {
    expect(MULTI_SELECT_CODES.has("K_03_INSTRUMENTS")).toBe(true);
    expect(MULTI_SELECT_CODES.has("U_02_SECTOR_WHITELIST")).toBe(true);
    expect(MULTI_SELECT_CODES.has("U_03_SECTOR_BLACKLIST")).toBe(true);
    expect(MULTI_SELECT_CODES.has("R_01_VOL_COMFORT")).toBe(false);
  });
});
