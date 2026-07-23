"use client";

/**
 * Desk W1 — v2 panels: VerdictBand (CMP-2), SignalMatrixV2 (CMP-5),
 * TournamentArenaV2 (CMP-6). Every state here maps to a SPEC-03 §6
 * screenshot row; DEC-5 (n/6 evidence honesty) and QS-2 (elevation caption)
 * are enforced in markup, then in tests.
 */
import { tokens } from "@/design/deskTokens";
import { deskCopy } from "@/lib/deskCopy";

import { CollapseCard, EngineStatusRail, GatedCard, StatusFetch } from "./core";

// ── CMP-2 VerdictBand ───────────────────────────────────────────────────────

export interface DeskHead {
  ticker: string;
  name?: string;
  price?: { last?: number | null; as_of?: string; source?: string };
  stance?: {
    state?: string;
    confidence?: string | number;
    evidence_coverage?: { have: number; of: number; gated?: string[] };
    age_s?: number;
  };
  currency?: string;
}

export function VerdictBand({ head, statusFetch, onStanceClick }: {
  head: DeskHead;
  statusFetch: StatusFetch;
  onStanceClick?: () => void;
}) {
  const stance = head.stance ?? {};
  const cov = stance.evidence_coverage;
  return (
    <header
      data-testid="verdict-band"
      role="banner"
      aria-label="Research verdict"
      style={{ position: "sticky", top: 0, zIndex: 40,
               display: "flex", flexWrap: "wrap", gap: tokens.space(2),
               alignItems: "center",
               background: tokens.color.neutral.n100,
               border: tokens.border.hairline,
               borderRadius: tokens.radius.panel,
               padding: tokens.space(2) }}
    >
      <div>
        <div style={{ fontWeight: 600, fontSize: tokens.type.scale.lg }}>
          {head.ticker}
          {head.name ? ` · ${head.name}` : ""}
        </div>
        <div style={{ ...tokens.type.numeric, fontSize: tokens.type.scale.md }}
             title={head.price?.source
               ? `source: ${head.price.source}` : undefined}>
          {head.price?.last != null
            ? `${head.price.last} ${head.currency ?? ""}`
            : "— price pending"}
          {head.price?.as_of && (
            <span style={{ color: tokens.color.neutral.n600,
                           fontSize: tokens.type.scale.xs,
                           marginLeft: 8 }}>
              {head.price.as_of}
            </span>
          )}
        </div>
      </div>

      <button
        data-testid="stance-chip"
        onClick={onStanceClick}
        style={{ border: tokens.border.hairline,
                 borderRadius: tokens.radius.chip,
                 padding: "6px 14px", background: tokens.color.accentSubtle }}
      >
        <strong style={{ color: tokens.color.accent }}>
          {stance.state ?? "no stance yet"}
        </strong>
        {" · "}
        {cov
          ? deskCopy.evidenceCoverage(cov.have, cov.of)
          : deskCopy.stanceKind}
        {cov?.gated?.length ? ` (gated: ${cov.gated.join(", ")})` : ""}
      </button>

      {/* The lane row now owns a full-width slot rather than being squeezed
          to the right of the price: expanding a lane opens an explanation
          panel underneath it, which needs the width. */}
      <div style={{ marginLeft: "auto", minWidth: 0, flex: "1 1 320px" }}>
        {statusFetch.kind === "ready" && (
          <EngineStatusRail sections={statusFetch.status.sections} />
        )}
        {statusFetch.kind === "unavailable" && (
          <span data-testid="status-unavailable"
                style={{ fontSize: tokens.type.scale.xs,
                         color: tokens.color.neutral.n600 }}>
            {deskCopy.errors.statusUnavailable}
          </span>
        )}
      </div>

      {statusFetch.kind === "ready" &&
        statusFetch.status.alerts_unseen > 0 && (
          <span data-testid="alert-badge"
                aria-label={`${statusFetch.status.alerts_unseen} unseen alerts`}
                style={{ color: tokens.color.semantic.cautious,
                         fontWeight: 600 }}>
            ⚠ {statusFetch.status.alerts_unseen}
          </span>
        )}
    </header>
  );
}

// ── CMP-5 SignalMatrixV2 ────────────────────────────────────────────────────

export interface MatrixRow {
  key: string;
  name: string;
  value: number | null;
  percentile?: number | null;
  percentile_note?: string;
  sparkline?: (number | null)[];
  read?: string;
}
export interface ElevationBlock {
  elevated: string[];
  caption: string;
  note?: string | null;
}

function PercentileBar({ p }: { p: number }) {
  return (
    <span aria-hidden="true"
          style={{ display: "inline-block", width: 120, height: 10,
                   background: tokens.color.neutral.n200,
                   position: "relative", verticalAlign: "middle" }}>
      <span style={{ position: "absolute", left: "50%", top: 0, bottom: 0,
                     width: 1, background: tokens.color.neutral.n400 }} />
      <span style={{ display: "block", height: "100%",
                     width: `${Math.round(p * 100)}%`,
                     background: tokens.color.accent }} />
    </span>
  );
}

export function SignalMatrixV2({ rows, elevation, source, onRetry }: {
  rows: MatrixRow[];
  elevation?: ElevationBlock;
  source: string;
  onRetry?: () => void;
}) {
  const nulls = rows.filter((r) => r.value == null).length;
  if (rows.length === 0 || nulls >= 3) {
    // K1 doctrine: a wall of dashes may never render (US-3.1 AC-4).
    return (
      <CollapseCard nulls={nulls || rows.length} source={source}
                    onRetry={onRetry} healthHref="/pro/ops" />
    );
  }
  const elevated = new Set(elevation?.elevated ?? []);
  return (
    <div data-testid="panel-technical">
      {elevation && elevation.elevated.length > 0 && (
        <p data-testid="elevation-caption"
           style={{ color: tokens.color.accent, fontWeight: 600,
                    fontSize: tokens.type.scale.sm }}>
          {elevation.caption}
        </p>
      )}
      {elevation?.note && (
        <p style={{ fontSize: tokens.type.scale.sm,
                    color: tokens.color.neutral.n600 }}>{elevation.note}</p>
      )}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key}
                data-testid={`signal-${r.key}`}
                data-elevated={elevated.has(r.key) || undefined}
                style={{
                  borderBottom: tokens.border.hairline,
                  borderLeft: elevated.has(r.key)
                    ? `3px solid ${tokens.color.accent}` : undefined,
                }}>
              <td style={{ padding: "6px 8px" }}>{r.name}</td>
              <td style={{ ...tokens.type.numeric, padding: "6px 8px" }}>
                {r.value != null ? r.value : (
                  <span style={{ color: tokens.color.neutral.n600 }}>
                    {r.read ?? "unpopulated"}
                  </span>
                )}
              </td>
              <td style={{ padding: "6px 8px" }}>
                {typeof r.percentile === "number" ? (
                  <>
                    <PercentileBar p={r.percentile} />{" "}
                    <span style={tokens.type.numeric}>
                      {Math.round(r.percentile * 100)}
                      <span aria-hidden="true">th</span> pct
                    </span>
                  </>
                ) : (
                  <span data-testid={`insufficient-${r.key}`}
                        style={{ color: tokens.color.neutral.n600,
                                 fontSize: tokens.type.scale.xs }}>
                    {r.percentile_note ?? deskCopy.signals.insufficient}
                  </span>
                )}
              </td>
              <td style={{ padding: "6px 8px",
                           color: tokens.color.neutral.n600,
                           fontSize: tokens.type.scale.xs }}>
                {r.read}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── CMP-6 TournamentArenaV2 ────────────────────────────────────────────────

export interface Candidate {
  key?: string;
  name: string;
  kind?: string;
  train_sharpe?: number;
  val_sharpe?: number;
  divergence?: number;
  // Backend D42 tournament section names this `penalty`; the early v2 draft
  // assumed `deflation_penalty`. Accept both so real payloads and fixtures
  // both render (this mismatch shipped the first crash — see US-3.2 tests).
  deflation_penalty?: number;
  penalty?: number;
  score?: number;
  rationale?: string;
  note?: string;
}
export interface TournamentPayload {
  // Backend returns the winning candidate as an OBJECT; the v2 draft assumed a
  // string. Accept either — rendering an object as a React child crashes the
  // whole Desk (React #31).
  winner?: string | Candidate;
  why?: string;
  scoreboard?: Candidate[];
  candidates?: Candidate[];
  selection_history?: { date: string; winner: string; score?: number }[];
  rl?: { status?: string };
}

export function TournamentArenaV2({ payload }: { payload: TournamentPayload }) {
  const rlGated = payload.rl?.status === "queued_for_research_run";
  const legs = rlGated ? "2 of 3 legs" : "all legs";
  // Normalize the two payload shapes (real backend vs. early fixtures).
  const winnerName =
    typeof payload.winner === "string" ? payload.winner : payload.winner?.name;
  const winnerWhy =
    payload.why ??
    (typeof payload.winner === "object" ? payload.winner?.rationale : undefined);
  const board: Candidate[] = payload.scoreboard ?? payload.candidates ?? [];
  return (
    <div data-testid="panel-tournament">
      {winnerName && (
        <div data-testid="winner-card"
             style={{ border: tokens.border.hairline,
                      borderRadius: tokens.radius.card,
                      padding: tokens.space(2),
                      marginBottom: tokens.space(2) }}>
          <strong style={{ color: tokens.color.accent }}>
            {deskCopy.arena.winner}: {winnerName}
          </strong>
          {winnerWhy && <p style={{ margin: "6px 0 0" }}>{winnerWhy}</p>}
        </div>
      )}
      {board.length > 0 && (
        <table data-testid="scoreboard"
               style={{ width: "100%", borderCollapse: "collapse",
                        fontSize: tokens.type.scale.sm }}>
          <thead>
            <tr>
              {[deskCopy.arena.colCandidate, deskCopy.arena.colVal,
                deskCopy.arena.colDivergence, deskCopy.arena.colPenalty]
                .map((h) => (
                  <th key={h} style={{ textAlign: "left", padding: "4px 8px",
                                       borderBottom: tokens.border.hairline }}>
                    {h}
                  </th>
                ))}
            </tr>
          </thead>
          <tbody style={tokens.type.numeric}>
            {board.map((c) => (
              <tr key={c.key ?? c.name} data-testid={`candidate-${c.name}`}>
                <td style={{ padding: "4px 8px" }}>{c.name}</td>
                <td style={{ padding: "4px 8px" }}>{c.val_sharpe ?? "–"}</td>
                <td style={{ padding: "4px 8px" }}>{c.divergence ?? "–"}</td>
                <td style={{ padding: "4px 8px" }}>
                  {c.deflation_penalty ?? c.penalty ?? "–"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {rlGated && (
        <div style={{ marginTop: tokens.space(2) }}>
          <GatedCard title={deskCopy.arena.queueTitle}
                     body={deskCopy.arena.queueBody(legs)} />
        </div>
      )}
      <div data-testid="selection-history" style={{ marginTop: tokens.space(2),
           fontSize: tokens.type.scale.xs, color: tokens.color.neutral.n600 }}>
        {payload.selection_history && payload.selection_history.length > 0 ? (
          payload.selection_history.slice(0, 5).map((h) => (
            <div key={h.date}>
              {h.date}: {h.winner}
              {h.score != null ? ` (${h.score})` : ""}
            </div>
          ))
        ) : (
          <em>{deskCopy.arena.firstRun}</em>
        )}
      </div>
    </div>
  );
}
