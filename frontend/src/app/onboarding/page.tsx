"use client";

/**
 * Phase W-3 — 8-step investor-profile wizard.
 *
 * Replaces the MVP-4 generic 4-step onboarding with a research-backed
 * questionnaire that:
 *   1. Welcome
 *   2-7. Knowledge / Financial / Risk / Objectives / Universe / Operational
 *   8. Review + submit
 *
 * Questions are loaded from GET /api/v1/profile/questions; the submission
 * is computed server-side by POST /api/v1/profile.
 *
 * If the user already has a profile, we route them straight to /decision.
 */
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { QuestionField } from "@/features/wizard/QuestionField";
import { ReviewStep } from "@/features/wizard/ReviewStep";
import { WizardLayout } from "@/features/wizard/WizardLayout";
import { fetchMyProfile, fetchProfileQuestions, submitProfile } from "@/features/wizard/api";
import type { AnswerMap, AnswerValue, ProfileQuestion, ProfileStep } from "@/features/wizard/types";

const TOTAL_STEPS = 8;
const WELCOME_STEP = 1;
const REVIEW_STEP = 8;

interface StepDescriptor {
  step: number;
  title: string;
  subtitle: string | null;
}

const STATIC_STEPS: Record<number, StepDescriptor> = {
  1: {
    step: 1,
    title: "Welcome to FINRLX",
    subtitle:
      "FINRLX is a decision-intelligence platform for medium-term investing. The next 3 minutes calibrate every recommendation to you.",
  },
  8: {
    step: 8,
    title: "Review your profile",
    subtitle: "We will compute your risk profile and store a versioned snapshot.",
  },
};

function isStepComplete(step: ProfileStep | undefined, answers: AnswerMap): boolean {
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

export default function OnboardingPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  const [step, setStep] = useState(WELCOME_STEP);
  const [steps, setSteps] = useState<ProfileStep[]>([]);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [error, setError] = useState<string | null>(null);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  // If the user already has a profile, skip onboarding.
  useEffect(() => {
    let cancelled = false;
    if (!user) return;
    fetchMyProfile()
      .then((me) => {
        if (cancelled) return;
        if (me.has_profile) {
          router.replace("/pro/decision");
        }
      })
      .catch(() => {
        // Non-fatal: continue showing the wizard. The user can still submit.
      });
    return () => {
      cancelled = true;
    };
  }, [user, router]);

  // Load the catalog.
  useEffect(() => {
    let cancelled = false;
    if (!user) return;
    setIsLoadingQuestions(true);
    fetchProfileQuestions()
      .then((data) => {
        if (cancelled) return;
        setSteps(data);
      })
      .catch((err: Error) => {
        if (cancelled) return;
        setError(`Could not load the wizard questions: ${err.message}`);
      })
      .finally(() => {
        if (!cancelled) setIsLoadingQuestions(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  const stepIndex = useMemo(
    () => new Map(steps.map((s) => [s.step, s])),
    [steps],
  );

  const currentServerStep = stepIndex.get(step);

  const stepDescriptor: StepDescriptor = useMemo(() => {
    if (STATIC_STEPS[step]) return STATIC_STEPS[step];
    if (currentServerStep) {
      const dimensionLabel: Record<string, string> = {
        knowledge: "About what you know and have done",
        financial: "About your financial situation (banded — no exact figures)",
        risk: "About your appetite for risk",
        objectives: "About what you want this portfolio to achieve",
        universe: "About which assets you want to consider",
        operational: "About how the system should behave",
      };
      return {
        step,
        title: currentServerStep.label,
        subtitle: dimensionLabel[currentServerStep.dimension_hint] ?? null,
      };
    }
    return { step, title: `Step ${step}`, subtitle: null };
  }, [step, currentServerStep]);

  const stepComplete = useMemo(() => {
    if (step === WELCOME_STEP || step === REVIEW_STEP) return true;
    return isStepComplete(currentServerStep, answers);
  }, [step, currentServerStep, answers]);

  const handleAnswer = useCallback((code: string, value: AnswerValue) => {
    setAnswers((prev) => ({ ...prev, [code]: value }));
  }, []);

  const handleBack = useCallback(() => {
    setError(null);
    setStep((s) => Math.max(WELCOME_STEP, s - 1));
  }, []);

  const handleNext = useCallback(async () => {
    setError(null);
    if (step < REVIEW_STEP) {
      setStep((s) => Math.min(REVIEW_STEP, s + 1));
      return;
    }
    // Final submit
    setIsSubmitting(true);
    try {
      await submitProfile(answers, "wizard initial submit");
      router.replace("/pro/decision");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setIsSubmitting(false);
    }
  }, [step, answers, router]);

  if (isLoading || !user) return null;

  return (
    <WizardLayout
      step={step}
      title={stepDescriptor.title}
      subtitle={stepDescriptor.subtitle}
      error={error}
      isSubmitting={isSubmitting}
      canGoBack={step > WELCOME_STEP}
      canGoNext={stepComplete && !isLoadingQuestions}
      nextLabel={step === REVIEW_STEP ? "Submit profile" : "Continue"}
      onBack={handleBack}
      onNext={handleNext}
    >
      {step === WELCOME_STEP ? (
        <WelcomeContent />
      ) : step === REVIEW_STEP ? (
        <ReviewStep answers={answers} steps={steps} />
      ) : isLoadingQuestions ? (
        <p style={loadingStyle}>Loading…</p>
      ) : currentServerStep ? (
        <QuestionGroup
          step={currentServerStep}
          answers={answers}
          onAnswer={handleAnswer}
        />
      ) : (
        <p style={loadingStyle}>This step has no questions yet.</p>
      )}
    </WizardLayout>
  );
}

function WelcomeContent() {
  return (
    <div>
      <p style={welcomeStyles.intro}>
        FINRLX is <strong>research, not investment advice</strong>. The wizard
        below captures the same suitability dimensions a regulated advisor
        would assess (knowledge, financial situation, objectives, risk
        appetite, sector preferences), so every recommendation can be
        traced back to a saved profile.
      </p>
      <ul style={welcomeStyles.list}>
        <li>Takes about 3 minutes.</li>
        <li>No precise income or net-worth figures — only bands.</li>
        <li>You can revise your profile at any time.</li>
      </ul>
    </div>
  );
}

function QuestionGroup({
  step,
  answers,
  onAnswer,
}: {
  step: ProfileStep;
  answers: AnswerMap;
  onAnswer: (code: string, value: AnswerValue) => void;
}) {
  return (
    <div>
      {step.questions.map((q: ProfileQuestion) => (
        <QuestionField
          key={q.code}
          question={q}
          value={answers[q.code]}
          onChange={(v) => onAnswer(q.code, v)}
        />
      ))}
    </div>
  );
}

const loadingStyle: CSSProperties = {
  textAlign: "center",
  fontSize: 14,
  opacity: 0.6,
  padding: 32,
};

const welcomeStyles: Record<string, CSSProperties> = {
  intro: {
    margin: 0,
    fontSize: 15,
    lineHeight: 1.65,
    color: "var(--fg, #e9e9ee)",
  },
  list: {
    marginTop: 18,
    paddingLeft: 22,
    fontSize: 14,
    lineHeight: 1.7,
    opacity: 0.85,
  },
};
