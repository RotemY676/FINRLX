"use client";

/**
 * Phase W-3 — wizard shell.
 *
 * Owns: progress bar, header (step label + dimension), footer nav
 * (back / next / submit). The active step content is rendered as
 * children.
 *
 * Accessibility:
 *  - progress bar has role="progressbar" with aria-valuenow/min/max
 *  - submit/next buttons have minHeight 44 (UX-1 touch target gate)
 *  - error region is aria-live=polite
 */
import type { CSSProperties, ReactNode } from "react";

import { TOTAL_STEPS } from "./types";

interface Props {
  step: number;
  title: string;
  subtitle: string | null;
  error: string | null;
  isSubmitting: boolean;
  canGoBack: boolean;
  canGoNext: boolean;
  nextLabel: string;
  onBack: () => void;
  onNext: () => void;
  children: ReactNode;
}

export function WizardLayout({
  step,
  title,
  subtitle,
  error,
  isSubmitting,
  canGoBack,
  canGoNext,
  nextLabel,
  onBack,
  onNext,
  children,
}: Props) {
  const pct = Math.round((step / TOTAL_STEPS) * 100);
  return (
    <div style={layoutStyles.wrap}>
      <div
        style={layoutStyles.progressTrack}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={TOTAL_STEPS}
        aria-valuenow={step}
        aria-label="Wizard progress"
      >
        <div style={{ ...layoutStyles.progressBar, width: `${pct}%` }} />
      </div>
      <div style={layoutStyles.progressMeta}>
        Step {step} of {TOTAL_STEPS}
      </div>

      <main style={layoutStyles.card}>
        <header style={layoutStyles.header}>
          <h1 style={layoutStyles.title}>{title}</h1>
          {subtitle ? <p style={layoutStyles.subtitle}>{subtitle}</p> : null}
        </header>

        <div style={layoutStyles.body}>{children}</div>

        {error ? (
          <div role="alert" aria-live="assertive" style={layoutStyles.error}>
            {error}
          </div>
        ) : null}

        <footer style={layoutStyles.footer}>
          <button
            type="button"
            onClick={onBack}
            disabled={!canGoBack || isSubmitting}
            style={
              canGoBack && !isSubmitting
                ? layoutStyles.buttonGhost
                : { ...layoutStyles.buttonGhost, ...layoutStyles.buttonDisabled }
            }
          >
            Back
          </button>
          <button
            type="button"
            onClick={onNext}
            disabled={!canGoNext || isSubmitting}
            style={
              canGoNext && !isSubmitting
                ? layoutStyles.button
                : { ...layoutStyles.button, ...layoutStyles.buttonDisabled }
            }
          >
            {isSubmitting ? "Saving…" : nextLabel}
          </button>
        </footer>
      </main>
    </div>
  );
}

const layoutStyles: Record<string, CSSProperties> = {
  wrap: {
    minHeight: "100dvh",
    background: "var(--bg, #0a0a0a)",
    color: "var(--fg, #e9e9ee)",
    paddingTop: 36,
    paddingBottom: 60,
    paddingLeft: 16,
    paddingRight: 16,
  },
  progressTrack: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    height: 4,
    background: "var(--border, #2a2a30)",
    zIndex: 10,
  },
  progressBar: {
    height: "100%",
    background: "var(--accent, #4f9fff)",
    transition: "width 240ms ease-out",
  },
  progressMeta: {
    position: "fixed",
    top: 12,
    right: 16,
    fontSize: 12,
    opacity: 0.65,
    zIndex: 10,
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
  header: { marginBottom: 24 },
  title: { margin: 0, fontSize: 24, fontWeight: 700, lineHeight: 1.3 },
  subtitle: {
    margin: "8px 0 0",
    fontSize: 14,
    lineHeight: 1.6,
    opacity: 0.7,
  },
  body: { marginBottom: 16 },
  error: {
    marginTop: 12,
    padding: "12px 14px",
    background: "rgba(255, 80, 80, 0.12)",
    border: "1px solid rgba(255, 80, 80, 0.45)",
    color: "#ff8a8a",
    borderRadius: 8,
    fontSize: 13,
    lineHeight: 1.45,
  },
  footer: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    marginTop: 24,
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
  buttonDisabled: { opacity: 0.45, cursor: "not-allowed" },
};
