"use client";

/**
 * Phase TPL-3 — pre-made recommendation templates.
 *
 * Lists active templates (seeds first), each as a card with its
 * allocation split, expected metrics, and an "Apply to my profile"
 * button.
 *
 * Routing:
 *   - if user is not logged in → /login
 *   - if user has no profile → /onboarding (apply needs an existing
 *     profile; we don't pretend to know your risk tolerance from a
 *     template)
 *   - on successful apply → redirect to /profile so the user sees the
 *     updated active profile
 */
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import type { CSSProperties } from "react";

import { useAuth } from "@/contexts/AuthContext";
import {
  applyTemplateToProfile,
  fetchMyProfile,
  fetchTemplates,
  type RecommendationTemplateView,
} from "@/features/wizard/api";

export default function TemplatesPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [templates, setTemplates] = useState<RecommendationTemplateView[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [applyingKey, setApplyingKey] = useState<string | null>(null);
  const [statusNote, setStatusNote] = useState<string | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [hasProfile, setHasProfile] = useState<boolean | null>(null);

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    let cancelled = false;
    if (!user) return;
    fetchMyProfile().then((me) => {
      if (!cancelled) setHasProfile(me.has_profile);
    });
    return () => {
      cancelled = true;
    };
  }, [user]);

  useEffect(() => {
    let cancelled = false;
    if (!user) return;
    setIsLoadingList(true);
    fetchTemplates()
      .then((data) => {
        if (!cancelled) setTemplates(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(`Could not load templates: ${err.message}`);
      })
      .finally(() => {
        if (!cancelled) setIsLoadingList(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  const handleApply = useCallback(
    async (key: string) => {
      setError(null);
      setStatusNote(null);
      setApplyingKey(key);
      try {
        const updated = await applyTemplateToProfile(key);
        setStatusNote(
          `Template applied — your profile is now version ${updated.version} (${updated.risk_bucket}, ${updated.horizon_band}).`,
        );
        setTimeout(() => router.push("/profile"), 1200);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        if (message.includes("no_profile")) {
          setError("Complete the wizard first — then apply a template.");
          setTimeout(() => router.push("/onboarding"), 1500);
        } else {
          setError(message);
        }
      } finally {
        setApplyingKey(null);
      }
    },
    [router],
  );

  if (isLoading || !user) return null;

  return (
    <div style={styles.wrap}>
      <main style={styles.container}>
        <header style={styles.header}>
          <h1 style={styles.h1}>Templates</h1>
          <p style={styles.intro}>
            Five pre-made profile presets derived from published model
            portfolios (Vanguard / Fidelity allocations + sector tilts).
            Apply one to overwrite your current preferences — your personal
            risk-tolerance answers and financial bands are preserved.
          </p>
        </header>

        {hasProfile === false ? (
          <div role="alert" style={styles.alert}>
            Complete the <a href="/onboarding" style={styles.link}>wizard</a>{" "}
            first — then apply a template.
          </div>
        ) : null}

        {error ? (
          <div role="alert" style={styles.alert}>
            {error}
          </div>
        ) : null}
        {statusNote ? (
          <div role="status" style={styles.success}>
            {statusNote}
          </div>
        ) : null}

        {isLoadingList ? (
          <p style={styles.loading}>Loading templates…</p>
        ) : (
          <ul style={styles.list}>
            {templates.map((t) => (
              <li key={t.id} style={styles.card}>
                <header style={styles.cardHeader}>
                  <div>
                    <h2 style={styles.cardTitle}>{t.name}</h2>
                    <p style={styles.cardDesc}>{t.description}</p>
                  </div>
                  <span style={styles.badge}>{t.badge}</span>
                </header>

                <section style={styles.metricsGrid} aria-label="Expected metrics">
                  <Metric label="Equity / defensive" value={t.allocation_summary ?? "—"} />
                  <Metric
                    label="Expected return (yr)"
                    value={`${t.metrics.expected_annual_return_pct.toFixed(1)}%`}
                  />
                  <Metric
                    label="Max drawdown cap"
                    value={`${t.metrics.expected_max_drawdown_pct.toFixed(0)}%`}
                  />
                  <Metric
                    label="Sharpe estimate"
                    value={t.metrics.sharpe_estimate.toFixed(2)}
                  />
                </section>

                <section style={styles.tags} aria-label="Profile tags">
                  <Tag>{t.horizon_band.replace("_", " ")}</Tag>
                  <Tag>{t.trading_frequency}</Tag>
                  <Tag>{t.base_currency}</Tag>
                  {t.sector_whitelist.map((s) => (
                    <Tag key={`w-${s}`}>+{s}</Tag>
                  ))}
                  {t.sector_blacklist.map((s) => (
                    <Tag key={`b-${s}`}>−{s}</Tag>
                  ))}
                </section>

                <p style={styles.methodology}>
                  <strong>Confidence: {t.metrics.confidence_label}.</strong>{" "}
                  {t.metrics.methodology_note}
                </p>

                <footer style={styles.cardFooter}>
                  <button
                    type="button"
                    onClick={() => handleApply(t.key)}
                    disabled={applyingKey !== null || hasProfile === false}
                    style={
                      applyingKey === t.key
                        ? { ...styles.button, opacity: 0.5, cursor: "wait" }
                        : applyingKey !== null || hasProfile === false
                        ? { ...styles.button, opacity: 0.4, cursor: "not-allowed" }
                        : styles.button
                    }
                  >
                    {applyingKey === t.key ? "Applying…" : "Apply to my profile"}
                  </button>
                </footer>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={styles.metric}>
      <div style={styles.metricLabel}>{label}</div>
      <div style={styles.metricValue}>{value}</div>
    </div>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return <span style={styles.tag}>{children}</span>;
}

const styles: Record<string, CSSProperties> = {
  wrap: {
    minHeight: "100vh",
    background: "var(--bg, #0a0a0a)",
    color: "var(--fg, #e9e9ee)",
    padding: "36px 16px 60px",
  },
  container: { width: "100%", maxWidth: 920, margin: "0 auto" },
  header: { marginBottom: 24 },
  h1: { margin: 0, fontSize: 28, fontWeight: 700 },
  intro: {
    margin: "8px 0 0",
    fontSize: 14,
    lineHeight: 1.6,
    opacity: 0.75,
    maxWidth: 720,
  },
  loading: { textAlign: "center", fontSize: 14, opacity: 0.6, padding: 40 },
  alert: {
    margin: "12px 0",
    padding: "12px 14px",
    background: "rgba(255, 80, 80, 0.12)",
    border: "1px solid rgba(255, 80, 80, 0.45)",
    color: "#ff8a8a",
    borderRadius: 8,
    fontSize: 13,
  },
  success: {
    margin: "12px 0",
    padding: "12px 14px",
    background: "rgba(80, 200, 120, 0.08)",
    border: "1px solid rgba(80, 200, 120, 0.4)",
    color: "#a5e6c1",
    borderRadius: 8,
    fontSize: 13,
  },
  list: {
    display: "grid",
    gap: 16,
    padding: 0,
    margin: 0,
    listStyle: "none",
  },
  card: {
    padding: 20,
    background: "var(--card, #131316)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 14,
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 12,
    marginBottom: 16,
  },
  cardTitle: { margin: 0, fontSize: 18, fontWeight: 700 },
  cardDesc: {
    margin: "6px 0 0",
    fontSize: 13,
    lineHeight: 1.55,
    opacity: 0.78,
    maxWidth: 540,
  },
  badge: {
    padding: "4px 10px",
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--accent, #4f9fff)",
    color: "var(--accent, #4f9fff)",
    borderRadius: 999,
    fontSize: 11,
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: 0.4,
    whiteSpace: "nowrap",
  },
  metricsGrid: {
    display: "grid",
    gap: 8,
    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
    marginBottom: 12,
  },
  metric: {
    padding: "10px 12px",
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 8,
  },
  metricLabel: {
    fontSize: 11,
    textTransform: "uppercase",
    letterSpacing: 0.4,
    opacity: 0.6,
    marginBottom: 4,
  },
  metricValue: { fontSize: 18, fontWeight: 700 },
  tags: {
    display: "flex",
    flexWrap: "wrap",
    gap: 6,
    marginBottom: 12,
  },
  tag: {
    padding: "4px 9px",
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 999,
    fontSize: 12,
    opacity: 0.85,
  },
  methodology: {
    margin: "0 0 16px",
    padding: "10px 12px",
    background: "rgba(255, 255, 255, 0.03)",
    border: "1px dashed var(--border, #2a2a30)",
    borderRadius: 8,
    fontSize: 12,
    lineHeight: 1.55,
    opacity: 0.75,
  },
  cardFooter: { display: "flex", justifyContent: "flex-end" },
  button: {
    padding: "12px 20px",
    background: "var(--accent, #4f9fff)",
    color: "#fff",
    border: 0,
    borderRadius: 8,
    fontWeight: 600,
    cursor: "pointer",
    minHeight: 44,
    fontSize: 14,
  },
  link: { color: "var(--accent, #4f9fff)", textDecoration: "underline" },
};
