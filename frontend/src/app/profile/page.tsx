"use client";

/**
 * Phase W-7 — investor-profile view + edit page.
 *
 * Two modes:
 *   "view"  → shows the active profile + a "Run a profile-aware
 *              recommendation" trigger + revision count.
 *   "edit"  → reuses the W-3 wizard components, pre-filled from the
 *              saved profile's raw_answers, and PATCH-style upserts on
 *              submit (same POST /api/v1/profile endpoint).
 *
 * If the user has no profile yet, we route them to /onboarding.
 */
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { QuestionField } from "@/features/wizard/QuestionField";
import { ReviewStep } from "@/features/wizard/ReviewStep";
import { WizardLayout } from "@/features/wizard/WizardLayout";
import {
  fetchMyProfile,
  fetchProfileQuestions,
  runProfileAwarePipeline,
  submitProfile,
} from "@/features/wizard/api";
import type {
  AnswerMap,
  AnswerValue,
  InvestorProfile,
  ProfileQuestion,
  ProfileStep,
} from "@/features/wizard/types";

type Mode = "view" | "edit";

const RISK_BUCKET_LABELS: Record<string, string> = {
  conservative: "Conservative",
  moderate_conservative: "Moderate-Conservative",
  moderate: "Moderate",
  moderate_aggressive: "Moderate-Aggressive",
  aggressive: "Aggressive",
};

const TOTAL_STEPS = 8;
const REVIEW_STEP = 8;
const FIRST_QUESTION_STEP = 2;

function isStepComplete(
  step: ProfileStep | undefined,
  answers: AnswerMap,
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

export default function ProfilePage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [mode, setMode] = useState<Mode>("view");
  const [profile, setProfile] = useState<InvestorProfile | null>(null);
  const [steps, setSteps] = useState<ProfileStep[]>([]);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [step, setStep] = useState(FIRST_QUESTION_STEP);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRunningPipeline, setIsRunningPipeline] = useState(false);
  const [pipelineNote, setPipelineNote] = useState<string | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  // Load active profile.
  useEffect(() => {
    let cancelled = false;
    if (!user) return;
    setIsLoadingProfile(true);
    fetchMyProfile()
      .then((me) => {
        if (cancelled) return;
        if (!me.has_profile || !me.profile) {
          router.replace("/onboarding");
          return;
        }
        setProfile(me.profile);
        setAnswers((me.profile.raw_answers ?? {}) as AnswerMap);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(`Could not load your profile: ${err.message}`);
      })
      .finally(() => {
        if (!cancelled) setIsLoadingProfile(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user, router]);

  // Load wizard catalog on demand (only when entering edit mode).
  useEffect(() => {
    let cancelled = false;
    if (mode !== "edit" || steps.length > 0) return;
    fetchProfileQuestions()
      .then((data) => {
        if (!cancelled) setSteps(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(`Could not load wizard questions: ${err.message}`);
      });
    return () => {
      cancelled = true;
    };
  }, [mode, steps.length]);

  const stepIndex = useMemo(
    () => new Map(steps.map((s) => [s.step, s])),
    [steps],
  );

  const currentServerStep = stepIndex.get(step);

  const stepComplete = useMemo(() => {
    if (step === REVIEW_STEP) return true;
    return isStepComplete(currentServerStep, answers);
  }, [step, currentServerStep, answers]);

  const handleAnswer = useCallback((code: string, value: AnswerValue) => {
    setAnswers((prev) => ({ ...prev, [code]: value }));
  }, []);

  const handleBack = useCallback(() => {
    setError(null);
    if (step > FIRST_QUESTION_STEP) {
      setStep((s) => s - 1);
    } else {
      setMode("view");
    }
  }, [step]);

  const handleNext = useCallback(async () => {
    setError(null);
    if (step < REVIEW_STEP) {
      setStep((s) => s + 1);
      return;
    }
    setIsSubmitting(true);
    try {
      const updated = await submitProfile(answers, "edit via /profile");
      setProfile(updated);
      setMode("view");
      setStep(FIRST_QUESTION_STEP);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }, [step, answers]);

  const handleRunPipeline = useCallback(async () => {
    setError(null);
    setPipelineNote(null);
    setIsRunningPipeline(true);
    try {
      const result = await runProfileAwarePipeline();
      const summary =
        result.recommendation_id
          ? `Recommendation ${result.recommendation_id.slice(0, 8)}… (${result.status})`
          : `Run finished: ${result.status}`;
      setPipelineNote(summary + (result.message ? ` — ${result.message}` : ""));
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(`Profile-aware run failed: ${message}`);
    } finally {
      setIsRunningPipeline(false);
    }
  }, []);

  if (isLoading || !user || isLoadingProfile) return null;

  if (mode === "edit") {
    return (
      <WizardLayout
        step={step}
        title={currentServerStep?.label ?? `Step ${step}`}
        subtitle={currentServerStep?.dimension_hint ?? null}
        error={error}
        isSubmitting={isSubmitting}
        canGoBack={true}
        canGoNext={stepComplete}
        nextLabel={step === REVIEW_STEP ? "Save changes" : "Continue"}
        onBack={handleBack}
        onNext={handleNext}
      >
        {step === REVIEW_STEP ? (
          <ReviewStep answers={answers} steps={steps} />
        ) : currentServerStep ? (
          <div>
            {currentServerStep.questions.map((q: ProfileQuestion) => (
              <QuestionField
                key={q.code}
                question={q}
                value={answers[q.code]}
                onChange={(v) => handleAnswer(q.code, v)}
              />
            ))}
          </div>
        ) : (
          <p style={loadingStyle}>Loading…</p>
        )}
      </WizardLayout>
    );
  }

  if (!profile) return null;

  return (
    <div style={viewStyles.wrap}>
      <main style={viewStyles.card}>
        <header style={viewStyles.header}>
          <h1 style={viewStyles.h1}>Investor profile</h1>
          <span style={viewStyles.versionPill}>v{profile.version}</span>
        </header>

        <section
          style={viewStyles.bucket}
          aria-label="Active risk profile summary"
        >
          <div style={viewStyles.bucketEyebrow}>Risk profile</div>
          <div style={viewStyles.bucketName}>
            {RISK_BUCKET_LABELS[profile.risk_bucket] ?? profile.risk_bucket}
          </div>
          <div style={viewStyles.bucketScore}>
            Score {profile.risk_score} / 32 · max drawdown {profile.max_drawdown_pct}%
            · horizon {profile.horizon_band.replace("_", " ")}
          </div>
        </section>

        <section style={viewStyles.kvs} aria-label="Saved profile preferences">
          <Row label="Primary goal" value={profile.primary_goal.replace("_", " ")} />
          <Row label="Region preference" value={profile.region_preference} />
          <Row label="Base currency" value={profile.base_currency} />
          <Row label="Cadence" value={profile.trading_frequency} />
          <Row label="Leverage" value={profile.exclude_leverage ? "Excluded" : "Allowed"} />
          <Row
            label="Favored sectors"
            value={profile.sector_whitelist.length ? profile.sector_whitelist.join(", ") : "(none)"}
          />
          <Row
            label="Excluded sectors"
            value={profile.sector_blacklist.length ? profile.sector_blacklist.join(", ") : "(none)"}
          />
          <Row label="Knowledge level" value={profile.knowledge_level} />
          <Row label="Years investing" value={String(profile.years_investing)} />
        </section>

        {error ? (
          <div role="alert" aria-live="assertive" style={viewStyles.error}>
            {error}
          </div>
        ) : null}
        {pipelineNote ? (
          <div role="status" aria-live="polite" style={viewStyles.note}>
            {pipelineNote}
          </div>
        ) : null}

        <p style={viewStyles.rerunHint}>
          Run the wizard again any time to update your knowledge level,
          financial situation, risk appetite, objectives, or sector
          preferences. A new revision is saved each time.
        </p>
        <footer style={viewStyles.footer}>
          <button
            type="button"
            onClick={handleRunPipeline}
            disabled={isRunningPipeline}
            style={
              isRunningPipeline
                ? { ...viewStyles.buttonGhost, opacity: 0.5, cursor: "wait" }
                : viewStyles.buttonGhost
            }
          >
            {isRunningPipeline ? "Running…" : "Run a profile-aware recommendation"}
          </button>
          <button
            type="button"
            data-testid="rerun-wizard"
            onClick={() => {
              setMode("edit");
              setStep(FIRST_QUESTION_STEP);
              setError(null);
              setPipelineNote(null);
            }}
            style={viewStyles.button}
          >
            Re-run the wizard
          </button>
        </footer>
      </main>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={viewStyles.row}>
      <dt style={viewStyles.dt}>{label}</dt>
      <dd style={viewStyles.dd}>{value}</dd>
    </div>
  );
}

const loadingStyle: CSSProperties = {
  textAlign: "center",
  fontSize: 14,
  opacity: 0.6,
  padding: 32,
};

const viewStyles: Record<string, CSSProperties> = {
  wrap: {
    minHeight: "100dvh",
    background: "var(--bg, #0a0a0a)",
    color: "var(--fg, #e9e9ee)",
    padding: "36px 16px 60px",
  },
  card: {
    width: "100%",
    maxWidth: 620,
    margin: "0 auto",
    padding: "32px 28px 28px",
    background: "var(--card, #131316)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 16,
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 20,
  },
  h1: { margin: 0, fontSize: 24, fontWeight: 700 },
  versionPill: {
    padding: "4px 10px",
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 999,
    fontSize: 12,
    fontFamily: "ui-monospace, monospace",
    opacity: 0.75,
  },
  bucket: {
    padding: 20,
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--accent, #4f9fff)",
    borderRadius: 12,
    marginBottom: 20,
  },
  bucketEyebrow: {
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    opacity: 0.7,
    marginBottom: 6,
  },
  bucketName: { fontSize: 22, fontWeight: 700, color: "var(--accent, #4f9fff)" },
  bucketScore: { fontSize: 13, opacity: 0.75, marginTop: 6 },
  kvs: {
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
  error: {
    marginTop: 16,
    padding: "12px 14px",
    background: "rgba(255, 80, 80, 0.12)",
    border: "1px solid rgba(255, 80, 80, 0.45)",
    color: "#ff8a8a",
    borderRadius: 8,
    fontSize: 13,
  },
  note: {
    marginTop: 16,
    padding: "12px 14px",
    background: "rgba(80, 200, 120, 0.08)",
    border: "1px solid rgba(80, 200, 120, 0.4)",
    color: "#a5e6c1",
    borderRadius: 8,
    fontSize: 13,
    lineHeight: 1.5,
  },
  rerunHint: {
    marginTop: 24,
    padding: "10px 14px",
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 8,
    color: "var(--fg, #e9e9ee)",
    opacity: 0.85,
    fontSize: 12.5,
    lineHeight: 1.5,
  },
  footer: {
    display: "flex",
    flexWrap: "wrap",
    gap: 12,
    marginTop: 12,
    paddingTop: 16,
    borderTop: "1px solid var(--border, #2a2a30)",
  },
  button: {
    padding: "12px 22px",
    background: "var(--accent, #4f9fff)",
    color: "#fff",
    border: 0,
    borderRadius: 8,
    fontWeight: 600,
    cursor: "pointer",
    minHeight: 44,
    fontSize: 14,
  },
  buttonGhost: {
    padding: "12px 22px",
    background: "transparent",
    color: "inherit",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 8,
    fontWeight: 500,
    cursor: "pointer",
    minHeight: 44,
    fontSize: 14,
  },
};
