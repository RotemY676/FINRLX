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
  // Non-degrading notes on a LIVE dial: an optional/gated enhancement is
  // absent but the lane itself is working (e.g. RL leg queued, mentions-only
  // sentiment). Backend added these when it stopped degrading working lanes.
  rl_note?: string;
  scored_note?: string;
}

// Which DeskV2 panel each lane's "Go to this panel" jumps to. The dial ids are
// the closed SECTION_IDS (technical/tournament/news/social/fundamentals/sector)
// but the panels are lettered (A..F), so a naive `#panel-<id>` anchor targeted
// nothing and the link did nothing. This maps the two vocabularies.
const PANEL_FOR: Record<string, string> = {
  technical: "A",
  tournament: "B",
  news: "C",
  social: "C",
  fundamentals: "E",
  sector: "F",
};

function scrollToPanel(sectionId: string) {
  if (typeof document === "undefined") return;
  const candidates = [PANEL_FOR[sectionId], sectionId].filter(Boolean);
  let el: HTMLElement | null = null;
  for (const id of candidates) {
    el = document.getElementById(`panel-${id}`);
    if (el) break;
  }
  if (!el) return;
  const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  // Brief highlight so the reader sees where they landed.
  el.setAttribute("data-jumped", "true");
  window.setTimeout(() => el?.removeAttribute("data-jumped"), 1500);
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
  | { kind: "unavailable" }; // dials hidden, never guessed (SPEC-02 §3)

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

// ── CMP-3 EngineDial + EngineStatusRail ─────────────────────────────────────
//
// The original dial was a 30px quarter-arc whose only affordance was a `title`
// tooltip: invisible on touch, unreadable at a glance, and it never said what
// the lane measured or why it was in that state. It is replaced by a lane tile
// that is a real button — expanding it reveals the reasoning.
//
// Kept deliberately from the original contract:
//   * the closed DialState enum with assertNever (an unknown state is a
//     compile-time error, never a runtime guess — SPEC-02 R3-T1);
//   * state conveyed by shape + text, never colour alone (NFR-4);
//   * `data-testid="dial-<id>"`, `data-state` and the aria-label built from
//     deskCopy.dialAria, so existing behaviour contracts still hold.
// Styling moves to the site's own tokens (globals.css) so the desk stops
// looking like a separate product.

/** Ring geometry per state. Shape differs, so colour is never the only cue. */
function DialGlyph({ state, active }: { state: DialState; active: boolean }) {
  const R = 13;
  const C = 2 * Math.PI * R;
  let stroke: string;
  let dash: string | undefined;
  let arc: React.ReactNode = null;

  switch (state) {
    case "live":
      // Full ring — complete coverage.
      stroke = "var(--pos)";
      break;
    case "degraded":
      // Three-quarter ring with a visible gap: coverage is incomplete.
      stroke = "var(--caution)";
      dash = `${C * 0.72} ${C}`;
      arc = (
        <line x1="0" y1={-R - 4} x2="0" y2={-R + 4}
          stroke="var(--caution)" strokeWidth="2.5" strokeLinecap="round" />
      );
      break;
    case "unavailable":
      // Dashed hollow ring + slash: nothing to report.
      stroke = "var(--ink-4)";
      dash = "3 4";
      arc = (
        <line x1={-9} y1={9} x2={9} y2={-9}
          stroke="var(--ink-4)" strokeWidth="2" strokeLinecap="round" />
      );
      break;
    default:
      return assertNever(state);
  }

  return (
    <svg width="34" height="34" viewBox="-17 -17 34 34" aria-hidden="true"
      className="shrink-0">
      <circle r={R} fill="none" stroke="var(--line)" strokeWidth="3" />
      <circle
        r={R}
        fill="none"
        stroke={stroke}
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray={dash}
        transform="rotate(-90)"
        className={active && state === "live" ? "desk-dial-live" : undefined}
      />
      {arc}
    </svg>
  );
}

export function EngineDial({
  status,
  expanded = false,
  onToggle,
}: {
  status: SectionStatus;
  expanded?: boolean;
  onToggle?: (id: string) => void;
}) {
  const label = deskCopy.engines[status.id] ?? status.id;
  const { state } = status;
  const stateCopy = deskCopy.dialState[state];
  const stateText = stateCopy?.label ?? state;

  return (
    <button
      type="button"
      data-testid={`dial-${status.id}`}
      data-state={state}
      aria-label={deskCopy.dialAria(label, stateText, status.reason)}
      aria-expanded={expanded}
      aria-controls={`dial-detail-${status.id}`}
      onClick={() => onToggle?.(status.id)}
      className={[
        "inline-flex min-h-11 items-center gap-2 rounded-lg border px-2.5 py-1.5",
        "text-left transition-colors",
        expanded
          ? "border-line-strong bg-surface-2"
          : "border-transparent hover:border-line hover:bg-surface-2",
      ].join(" ")}
    >
      <DialGlyph state={state} active={!expanded} />
      <span className="flex flex-col leading-tight">
        <span className="text-xs font-medium text-ink">{label}</span>
        {/* NFR-4: the state is spelled out, not implied by the ring colour. */}
        <span className="text-[10px] text-ink-2">{stateText}</span>
      </span>
    </button>
  );
}

/**
 * The lane row plus one expanded explanation panel.
 *
 * Only one lane opens at a time: the row lives in a sticky header, and
 * stacking six open panels there would push the actual desk off-screen.
 */
export function EngineStatusRail({ sections }: { sections: SectionStatus[] }) {
  const [openId, setOpenId] = useState<string | null>(null);
  const open = sections.find((s) => s.id === openId) ?? null;

  return (
    <div className="w-full" data-testid="engine-status-rail">
      <div data-testid="dial-row" className="flex flex-wrap items-center gap-1">
        {sections.map((s) => (
          <EngineDial
            key={s.id}
            status={s}
            expanded={openId === s.id}
            onToggle={(id) => setOpenId((cur) => (cur === id ? null : id))}
          />
        ))}
      </div>

      {open && (
        <div
          id={`dial-detail-${open.id}`}
          data-testid={`dial-detail-${open.id}`}
          className="mt-2 rounded-lg border border-line bg-surface p-3 text-sm"
        >
          <div className="mb-1 flex flex-wrap items-baseline gap-2">
            <strong className="text-ink">
              {deskCopy.engines[open.id] ?? open.id}
            </strong>
            <span className="rounded-full border border-line px-2 py-0.5 text-[11px] text-ink-2">
              {deskCopy.dialState[open.state]?.label ?? open.state}
            </span>
          </div>

          {deskCopy.engineWhat[open.id] && (
            <p className="text-ink-2">{deskCopy.engineWhat[open.id]}</p>
          )}

          <p className="mt-2 font-medium text-ink">{deskCopy.rail.whyTitle}</p>
          <p className="text-ink-2">
            {deskCopy.dialState[open.state]?.meaning ?? ""}
          </p>

          {/* Server honesty renders verbatim — the client never rewrites it. */}
          <p className="mt-2 font-medium text-ink">{deskCopy.rail.reasonTitle}</p>
          {/* A live lane has no failure reason; surface its note instead so the
              useful context (e.g. "RL leg queued (E7)") is not lost. */}
          <p className="text-ink-2">
            {open.reason ?? open.rl_note ?? open.scored_note ?? deskCopy.rail.noReason}
          </p>

          {open.detail_code && deskCopy.detailCode[open.detail_code] && (
            <p className="mt-2 rounded border border-line bg-surface-2 p-2 text-ink-2">
              <span className="font-mono text-[11px] text-ink">{open.detail_code}</span>
              {" — "}
              {deskCopy.detailCode[open.detail_code]}
            </p>
          )}

          <div className="mt-2 flex flex-wrap gap-x-4 text-xs text-ink-4">
            {open.scope && <span>{deskCopy.rail.scopeTitle}: {open.scope}</span>}
            {open.freshness_bar && (
              <span>{deskCopy.rail.freshnessTitle}: {open.freshness_bar}</span>
            )}
          </div>

          <button
            type="button"
            data-testid={`jump-${open.id}`}
            onClick={() => scrollToPanel(open.id)}
            className="mt-2 inline-flex min-h-11 items-center text-sm text-primary underline"
          >
            {deskCopy.rail.jump}
          </button>
        </div>
      )}
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
        ×
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
          `${s.name}${s.as_of ? ` · ${s.as_of}` : ""}${s.coverage ? ` · ${s.coverage}` : ""}`,
        ).join(" | ")}
        {fingerprint && <> · fp {fingerprint}</>}
        {computedAt && <> · {computedAt}</>}
      </footer>
    </div>
  );
}
