"use client";

/**
 * Phase W-3 — review step (step 8 of 8).
 *
 * Shows the computed-on-the-client risk_score + bucket preview so the
 * user can sanity-check before submitting. The backend recomputes from
 * scratch in POST /profile — this preview is informational only.
 */
import type { CSSProperties } from "react";

import type { AnswerMap, ProfileStep } from "./types";

interface Props {
  answers: AnswerMap;
  steps: ProfileStep[];
}

const RISK_BUCKET_LABELS: Record<string, string> = {
  conservative: "Conservative",
  moderate_conservative: "Moderate-Conservative",
  moderate: "Moderate",
  moderate_aggressive: "Moderate-Aggressive",
  aggressive: "Aggressive",
};

function computeRiskScore(answers: AnswerMap, steps: ProfileStep[]): number {
  const riskStep = steps.find((s) => s.step === 4);
  if (!riskStep) return 0;
  let total = 0;
  for (const q of riskStep.questions) {
    const chosen = answers[q.code];
    if (typeof chosen !== "string") continue;
    const match = q.choices.find((c) => c.value === chosen);
    if (match && typeof match.score === "number") {
      total += match.score;
    }
  }
  return total;
}

function bucketFromScore(score: number): string {
  if (score <= 12) return "conservative";
  if (score <= 17) return "moderate_conservative";
  if (score <= 22) return "moderate";
  if (score <= 27) return "moderate_aggressive";
  return "aggressive";
}

function summary(answers: AnswerMap): { code: string; label: string; value: string }[] {
  const single = (code: string): string => {
    const v = answers[code];
    return typeof v === "string" ? v : "—";
  };
  const multi = (code: string): string => {
    const v = answers[code];
    if (!Array.isArray(v) || v.length === 0) return "(none)";
    return v.join(", ");
  };
  return [
    { code: "K_01_LEVEL", label: "Knowledge", value: single("K_01_LEVEL") },
    { code: "K_02_YEARS", label: "Years investing", value: single("K_02_YEARS") },
    { code: "K_03_INSTRUMENTS", label: "Instruments", value: multi("K_03_INSTRUMENTS") },
    { code: "F_01_INVESTABLE", label: "Investable", value: single("F_01_INVESTABLE") },
    { code: "F_02_INCOME", label: "Income band", value: single("F_02_INCOME") },
    { code: "F_03_NET_WORTH", label: "Net worth", value: single("F_03_NET_WORTH") },
    { code: "O_01_HORIZON", label: "Horizon", value: single("O_01_HORIZON") },
    { code: "O_02_PRIMARY_GOAL", label: "Primary goal", value: single("O_02_PRIMARY_GOAL") },
    { code: "O_03_MAX_DD", label: "Max drawdown", value: `${single("O_03_MAX_DD")}%` },
    { code: "U_01_REGION", label: "Region", value: single("U_01_REGION") },
    { code: "U_02_SECTOR_WHITELIST", label: "Favored sectors", value: multi("U_02_SECTOR_WHITELIST") },
    { code: "U_03_SECTOR_BLACKLIST", label: "Excluded sectors", value: multi("U_03_SECTOR_BLACKLIST") },
    { code: "U_04_LEVERAGE", label: "Leverage", value: single("U_04_LEVERAGE") === "no" ? "Excluded" : "Allowed" },
    { code: "P_01_CURRENCY", label: "Base currency", value: single("P_01_CURRENCY") },
    { code: "P_02_FREQUENCY", label: "Cadence", value: single("P_02_FREQUENCY") },
  ];
}

export function ReviewStep({ answers, steps }: Props) {
  const riskScore = computeRiskScore(answers, steps);
  const bucket = bucketFromScore(riskScore);
  const bucketLabel = RISK_BUCKET_LABELS[bucket] ?? bucket;
  const rows = summary(answers);

  return (
    <div>
      <h2 style={reviewStyles.h2}>Review your profile</h2>
      <p style={reviewStyles.intro}>
        Confirm the answers below. We will compute your risk profile and store
        a versioned snapshot you can revise at any time.
      </p>

      <div style={reviewStyles.bucketCard} aria-live="polite">
        <div style={reviewStyles.bucketEyebrow}>Estimated risk profile</div>
        <div style={reviewStyles.bucketName}>{bucketLabel}</div>
        <div style={reviewStyles.bucketScore}>
          Score {riskScore} / 32 — final value will be confirmed server-side.
        </div>
      </div>

      <dl style={reviewStyles.list}>
        {rows.map((row) => (
          <div key={row.code} style={reviewStyles.row}>
            <dt style={reviewStyles.dt}>{row.label}</dt>
            <dd style={reviewStyles.dd}>{row.value || "—"}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

const reviewStyles: Record<string, CSSProperties> = {
  h2: { margin: "0 0 12px", fontSize: 22, fontWeight: 600 },
  intro: { margin: "0 0 20px", fontSize: 14, lineHeight: 1.6, opacity: 0.85 },
  bucketCard: {
    padding: 20,
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--accent, #4f9fff)",
    borderRadius: 12,
    marginBottom: 24,
  },
  bucketEyebrow: {
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    opacity: 0.7,
    marginBottom: 6,
  },
  bucketName: { fontSize: 24, fontWeight: 700, color: "var(--accent, #4f9fff)" },
  bucketScore: { fontSize: 13, opacity: 0.7, marginTop: 6 },
  list: {
    margin: 0,
    display: "grid",
    gap: 4,
  },
  row: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    padding: "10px 14px",
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 8,
    fontSize: 13,
    lineHeight: 1.5,
    gap: 12,
  },
  dt: { fontWeight: 600, opacity: 0.85 },
  dd: { margin: 0, textAlign: "right", color: "var(--fg, #e9e9ee)" },
};
