"use client";

/**
 * Desk W1 — v2 core primitives (SPEC-03 CMP-3/7/13 + API-4 hook).
 * Exhaustive on the closed enums from SPEC-02: an unknown state is a
 * compile-time error (assertNever), never a runtime guess (R3-T1).
 */
import { useEffect, useState } from "react";

import { DetailCode, DialState, tokens } from "@/design/deskTokens";
import { deskCopy } from "@/lib/deskCopy";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

// ── API-4 types (closed) ────────────────────────────────────────────────────

export interface SectionStatus {
  id: string;
  state: DialState;
  reason?: string;
  detail_code?: DetailCode;
  scope?: string;
  freshness_bar?: string;
}
export interface DeskStatus {
  fingerprint: string;
  sections: SectionStatus[];
  alerts_unseen: number;
  computed_at: string;
}

export type StatusFetch =
  | { kind: "loading" }
  | { kind: "ready"; status: DeskStatus }
  | { kind: "no_dossier" }
  | { kind: "unavailable" }; // dials hidden, never guessed (SPEC-02 \u00A73)

export function useDeskStatus(ticker: string, revision = 0): StatusFetch {
  const [state, setState] = useState<StatusFetch>({ kind: "loading" });
  useEffect(() => {
    let cancelled = false;
    setState({ kind: "loading" });
    void (async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/v1/autopilot/desk/${encodeURIComponent(ticker)}/status`,
        );
        if (res.status === 404) {
          if (!cancelled) setState({ kind: "no_dossier" });
          return;
        }
        if (!res.ok) {
          if (!cancelled) setState({ kind: "unavailable" });
          return;
        }
        const body = (await res.json()) as { data: DeskStatus };
        if (!cancelled) setState({ kind: "ready", status: body.data });
      } catch {
        if (!cancelled) setState({ kind: "unavailable" });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ticker, revision]);
  return state;
}

// ── exhaustiveness helper ───────────────────────────────────────────────────

export function assertNever(x: never): never {
  throw new Error(`unreachable state: ${String(x)}`);
}

// ── CMP-3 EngineDial ────────────────────────────────────────────────────────

/** Quarter-arc dial. State is conveyed by fill + tick + text label —
 *  never color alone (NFR-4). */
export function EngineDial({ status }: { status: SectionStatus }) {
  const label = deskCopy.engines[status.id] ?? status.id;
  const { state } = status;
  let arc: React.ReactNode;
  let stateText: string;
  switch (state) {
    case "live":
      arc = (
        <path d="M -12 0 A 12 12 0 1 1 12 0" fill={tokens.color.accent} />
      );
      stateText = "live";
      break;
    case "degraded":
      arc = (
        <path
          d="M -12 0 A 12 12 0 0 1 0 -12"
          fill={tokens.color.semantic.cautious}
        />
      );
      stateText = "degraded";
      break;
    case "unavailable":
      arc = null; // hollow
      stateText = "unavailable";
      break;
    default:
      return assertNever(state);
  }
  return (
    <div
      role="img"
      aria-label={deskCopy.dialAria(label, stateText, status.reason)}
      data-testid={`dial-${status.id}`}
      data-state={state}
      title={status.reason}
      style={{ display: "inline-flex", flexDirection: "column",
               alignItems: "center", gap: "2px" }}
    >
      <svg width="30" height="30" viewBox="-15 -15 30 30" aria-hidden="true">
        <circle
          r="12"
          fill="none"
          stroke={state === "unavailable"
            ? tokens.color.neutral.n400 : tokens.color.accent}
          strokeWidth="3"
        />
        {arc}
        {state === "degraded" && (
          <line x1="0" y1="-15" x2="0" y2="-9"
                stroke={tokens.color.semantic.cautious} strokeWidth="3" />
        )}
      </svg>
      <span style={{ fontSize: tokens.type.scale.xs,
                     color: tokens.color.neutral.n600 }}>
        {label}
      </span>
      <span className="sr-only">{stateText}{status.reason ? ` \u2014 ${status.reason}` : ""}</span>
    </div>
  );
}

// ── CMP-13 StateCards — three distinct grammars (R4-U1) ────────────────────

const cardBase: React.CSSProperties = {
  borderRadius: tokens.radius.card,
  padding: tokens.space(2),
  fontSize: tokens.type.scale.sm,
  lineHeight: tokens.type.lineHeight,
};

/** neutral grammar: data is MISSING (honest limitation) */
export function CollapseCard({ nulls, source, onRetry, healthHref }: {
  nulls: number; source: string; onRetry?: () => void; healthHref?: string;
}) {
  return (
    <div data-testid="collapse-card" data-grammar="missing"
         style={{ ...cardBase, border: tokens.border.hairline,
                  background: tokens.color.neutral.n100 }}>
      <strong>{deskCopy.signals.collapseTitle}</strong>
      <p style={{ margin: "6px 0" }}>
        {deskCopy.signals.collapseBody(nulls, source)}
      </p>
      {onRetry && (
        <button onClick={onRetry}>{deskCopy.signals.retry}</button>
      )}{" "}
      {healthHref && <a href={healthHref}>{deskCopy.signals.healthLink}</a>}
    </div>
  );
}

/** dashed-cautious grammar: capability is LOCKED (operator-gated) */
export function GatedCard({ title, body }: { title: string; body: string }) {
  return (
    <div data-testid="gated-card" data-grammar="gated"
         style={{ ...cardBase, border: tokens.border.gated,
                  background: "rgba(184,134,11,0.06)" }}>
      <strong style={{ color: tokens.color.semantic.cautious }}>{title}</strong>
      <p style={{ margin: "6px 0 0" }}>{body}</p>
    </div>
  );
}

/** bordered-risk grammar: something is BROKEN (source failure) */
export function ErrorCard({ source, onRetry, healthHref }: {
  source: string; onRetry?: () => void; healthHref?: string;
}) {
  return (
    <div data-testid="error-card" data-grammar="broken"
         style={{ ...cardBase, border: tokens.border.error }}>
      <strong style={{ color: tokens.color.semantic.risk }}>
        {deskCopy.errors.sectionTitle}
      </strong>
      <p style={{ margin: "6px 0" }}>{deskCopy.errors.sectionBody(source)}</p>
      {onRetry && <button onClick={onRetry}>{deskCopy.signals.retry}</button>}{" "}
      {healthHref && <a href={healthHref}>{deskCopy.signals.healthLink}</a>}
    </div>
  );
}

// ── CMP-7 ForensicDrawer ───────────────────────────────────────────────────

export interface MethodBlock {
  summary: string;
  factors: { name: string; role: string; value_ref?: string }[];
  detail_md: string;
  sources: { name: string; as_of?: string | null; coverage?: string }[];
}

export function ForensicDrawer({ panel, method, fingerprint, computedAt, onClose }: {
  panel: string;
  method: MethodBlock | null;
  fingerprint?: string;
  computedAt?: string;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div data-testid="drawer" role="dialog" aria-modal="true"
         aria-label={deskCopy.drawer.title(panel)}
         style={{ position: "fixed", top: 0, right: 0, bottom: 0, width: 420,
                  background: tokens.color.neutral.n050,
                  borderLeft: tokens.border.hairline, padding: tokens.space(3),
                  overflowY: "auto", zIndex: 60 }}>
      <button onClick={onClose} aria-label="Close" style={{ float: "right" }}>
        \u00D7
      </button>
      <h2 style={{ fontSize: tokens.type.scale.md, marginTop: 0 }}>
        {deskCopy.drawer.title(panel)}
      </h2>
      {method ? (
        <>
          <p data-testid="drawer-summary">{method.summary}</p>
          <h3 style={{ fontSize: tokens.type.scale.sm }}>
            {deskCopy.drawer.factors}
          </h3>
          <ul data-testid="drawer-factors">
            {method.factors.map((f) => (
              <li key={f.name}>
                {f.name} <em>({f.role})</em>
              </li>
            ))}
          </ul>
          <h3 style={{ fontSize: tokens.type.scale.sm }}>
            {deskCopy.drawer.detail}
          </h3>
          <p data-testid="drawer-detail" style={{ whiteSpace: "pre-wrap" }}>
            {method.detail_md}
          </p>
        </>
      ) : (
        <p>{deskCopy.drawer.methodMissing}</p>
      )}
      <footer data-testid="drawer-provenance"
              style={{ borderTop: tokens.border.hairline,
                       marginTop: tokens.space(2), paddingTop: tokens.space(1),
                       fontSize: tokens.type.scale.xs,
                       color: tokens.color.neutral.n600 }}>
        <strong>{deskCopy.drawer.provenance}:</strong>{" "}
        {method?.sources.map((s) =>
          `${s.name}${s.as_of ? ` \u00B7 ${s.as_of}` : ""}${s.coverage ? ` \u00B7 ${s.coverage}` : ""}`,
        ).join(" | ")}
        {fingerprint && <> \u00B7 fp {fingerprint}</>}
        {computedAt && <> \u00B7 {computedAt}</>}
      </footer>
    </div>
  );
}
