"use client";

/**
 * Phase BETA-2 — beta-tester feedback form.
 *
 * Auth-required; submits to POST /api/v1/feedback. Shows the tester
 * their own past submissions below the form via GET /feedback/me.
 */
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import type { CSSProperties } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { getAccessToken } from "@/services/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

const CATEGORIES = [
  { value: "general", label: "General" },
  { value: "ux", label: "UX / wording" },
  { value: "bug", label: "Bug" },
  { value: "data", label: "Data accuracy" },
  { value: "feature_request", label: "Feature request" },
];

interface FeedbackRow {
  id: string;
  user_email: string;
  surface: string | null;
  category: string;
  message: string;
  status: string;
  created_at: string;
}

function authHeaders(): Record<string, string> {
  const t = getAccessToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function postFeedback(payload: {
  message: string;
  category: string;
  surface?: string | null;
}): Promise<FeedbackRow> {
  const res = await fetch(`${API_BASE_URL}/api/v1/feedback`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Feedback POST ${res.status}: ${body || res.statusText}`);
  }
  return (await res.json()).data;
}

async function fetchMyFeedback(): Promise<FeedbackRow[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/feedback/me`, {
    headers: { Accept: "application/json", ...authHeaders() },
  });
  if (!res.ok) return [];
  return (await res.json()).data ?? [];
}

export default function FeedbackPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [message, setMessage] = useState("");
  const [category, setCategory] = useState("general");
  const [surface, setSurface] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [mine, setMine] = useState<FeedbackRow[]>([]);

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    fetchMyFeedback().then(setMine).catch(() => undefined);
  }, [user, successMsg]);

  const handleSubmit = useCallback(async () => {
    if (!message.trim()) {
      setError("Message cannot be empty.");
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await postFeedback({
        message,
        category,
        surface: surface.trim() || null,
      });
      setMessage("");
      setSurface("");
      setSuccessMsg("Thanks — your note is in.");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }, [message, category, surface]);

  if (isLoading || !user) return null;

  return (
    <div style={styles.wrap}>
      <main style={styles.card}>
        <h1 style={styles.h1}>Send feedback</h1>
        <p style={styles.intro}>
          The fastest channel to influence what we fix this week. We read
          everything; we prioritize tagged with categories that match the
          most impact.
        </p>

        <label style={styles.label}>
          Surface (optional)
          <input
            type="text"
            value={surface}
            onChange={(e) => setSurface(e.target.value)}
            placeholder="/onboarding, /paper, etc."
            style={styles.input}
          />
        </label>

        <label style={styles.label}>
          Category
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            style={styles.input}
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </label>

        <label style={styles.label}>
          Your note
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={6}
            maxLength={4000}
            placeholder="What did you try, what happened, what did you expect?"
            style={{ ...styles.input, fontFamily: "inherit" }}
          />
        </label>

        {error ? (
          <div role="alert" style={styles.alert}>
            {error}
          </div>
        ) : null}
        {successMsg ? (
          <div role="status" aria-live="polite" style={styles.success}>
            {successMsg}
          </div>
        ) : null}

        <div style={styles.footer}>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || !message.trim()}
            style={
              submitting || !message.trim()
                ? { ...styles.button, opacity: 0.4, cursor: "not-allowed" }
                : styles.button
            }
          >
            {submitting ? "Sending…" : "Send"}
          </button>
        </div>

        {mine.length > 0 ? (
          <section aria-label="Your past feedback" style={styles.history}>
            <h2 style={styles.h2}>Your past notes</h2>
            <ul style={styles.list}>
              {mine.map((row) => (
                <li key={row.id} style={styles.row}>
                  <div style={styles.rowMeta}>
                    <span style={styles.tag}>{row.category}</span>
                    <span style={styles.statusTag(row.status)}>{row.status}</span>
                    {row.surface ? (
                      <span style={styles.muted}>{row.surface}</span>
                    ) : null}
                  </div>
                  <p style={styles.rowMessage}>{row.message}</p>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </main>
    </div>
  );
}

const styles = {
  wrap: {
    minHeight: "100vh",
    background: "var(--bg, #0a0a0a)",
    color: "var(--fg, #e9e9ee)",
    padding: "36px 16px 60px",
  } as CSSProperties,
  card: {
    width: "100%",
    maxWidth: 620,
    margin: "0 auto",
    padding: "32px 28px 28px",
    background: "var(--card, #131316)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 16,
  } as CSSProperties,
  h1: { margin: 0, fontSize: 24, fontWeight: 700 } as CSSProperties,
  h2: { fontSize: 16, marginTop: 24, marginBottom: 12 } as CSSProperties,
  intro: {
    margin: "8px 0 24px",
    fontSize: 14,
    lineHeight: 1.65,
    opacity: 0.75,
  } as CSSProperties,
  label: {
    display: "block",
    marginBottom: 16,
    fontSize: 13,
    fontWeight: 600,
    color: "var(--fg, #e9e9ee)",
  } as CSSProperties,
  input: {
    display: "block",
    width: "100%",
    marginTop: 6,
    padding: "10px 12px",
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 8,
    color: "var(--fg, #e9e9ee)",
    fontSize: 14,
    minHeight: 44,
    boxSizing: "border-box",
  } as CSSProperties,
  alert: {
    marginTop: 8,
    padding: "10px 12px",
    background: "rgba(255, 80, 80, 0.12)",
    border: "1px solid rgba(255, 80, 80, 0.45)",
    color: "#ff8a8a",
    borderRadius: 8,
    fontSize: 13,
  } as CSSProperties,
  success: {
    marginTop: 8,
    padding: "10px 12px",
    background: "rgba(80, 200, 120, 0.08)",
    border: "1px solid rgba(80, 200, 120, 0.4)",
    color: "#a5e6c1",
    borderRadius: 8,
    fontSize: 13,
  } as CSSProperties,
  footer: {
    display: "flex",
    justifyContent: "flex-end",
    marginTop: 16,
  } as CSSProperties,
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
  } as CSSProperties,
  history: {
    marginTop: 28,
    paddingTop: 20,
    borderTop: "1px solid var(--border, #2a2a30)",
  } as CSSProperties,
  list: { listStyle: "none", padding: 0, margin: 0 } as CSSProperties,
  row: {
    padding: "12px 14px",
    background: "var(--input, #1a1a1f)",
    border: "1px solid var(--border, #2a2a30)",
    borderRadius: 8,
    marginBottom: 8,
  } as CSSProperties,
  rowMeta: {
    display: "flex",
    gap: 6,
    marginBottom: 6,
    flexWrap: "wrap",
  } as CSSProperties,
  tag: {
    padding: "2px 8px",
    background: "rgba(79, 159, 255, 0.15)",
    color: "var(--accent, #4f9fff)",
    borderRadius: 999,
    fontSize: 11,
    fontWeight: 600,
  } as CSSProperties,
  muted: { fontSize: 11, opacity: 0.6, alignSelf: "center" } as CSSProperties,
  rowMessage: {
    margin: 0,
    fontSize: 13,
    lineHeight: 1.55,
    color: "var(--fg, #e9e9ee)",
  } as CSSProperties,
  statusTag(status: string): CSSProperties {
    const colorByStatus: Record<string, string> = {
      open: "#a5e6c1",
      triaged: "#f0c780",
      in_progress: "#4f9fff",
      resolved: "#a5e6c1",
      wontfix: "#ff8a8a",
    };
    return {
      padding: "2px 8px",
      background: "rgba(255, 255, 255, 0.05)",
      color: colorByStatus[status] ?? "var(--fg, #e9e9ee)",
      borderRadius: 999,
      fontSize: 11,
      fontWeight: 600,
    } as CSSProperties;
  },
};
