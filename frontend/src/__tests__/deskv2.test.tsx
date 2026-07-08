/**
 * Desk W1 — v2 component gates (SPEC-03 contracts; SPEC-01 acceptance rows).
 * Fixture-only. Each test names its spec source.
 */
import { render, screen, fireEvent } from "@testing-library/react";
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it, vi } from "vitest";

import {
  CollapseCard,
  EngineDial,
  ErrorCard,
  ForensicDrawer,
  GatedCard,
} from "@/components/deskv2/core";
import {
  SignalMatrixV2,
  TournamentArenaV2,
  VerdictBand,
} from "@/components/deskv2/panels";
import { deskCopy } from "@/lib/deskCopy";

// ── CMP-3 EngineDial: exhaustive closed enum, never color-only (NFR-4) ─────

describe("EngineDial (US-2.1 AC-3)", () => {
  it("renders all three states with text labels and reasons", () => {
    const { rerender } = render(
      <EngineDial status={{ id: "technical", state: "live" }} />,
    );
    expect(screen.getByTestId("dial-technical").dataset.state).toBe("live");
    expect(screen.getByTestId("dial-technical").getAttribute("aria-label"))
      .toContain("live");

    rerender(
      <EngineDial status={{ id: "tournament", state: "degraded",
                            reason: "RL leg queued (E7)",
                            detail_code: "E7_GATED" }} />,
    );
    const d = screen.getByTestId("dial-tournament");
    expect(d.dataset.state).toBe("degraded");
    expect(d.getAttribute("aria-label")).toContain("RL leg queued (E7)");

    rerender(
      <EngineDial status={{ id: "news", state: "unavailable",
                            reason: "source down",
                            detail_code: "SOURCE_DOWN" }} />,
    );
    expect(screen.getByTestId("dial-news").dataset.state).toBe("unavailable");
  });

  it("conveys state in accessible text, not only via fill (NFR-4)", () => {
    render(
      <EngineDial status={{ id: "social", state: "degraded",
                            reason: "mentions-only fallback (E8)" }} />,
    );
    expect(
      screen.getByTestId("dial-social").getAttribute("aria-label"),
    ).toMatch(/degraded.*E8/);
  });
});

// ── CMP-13: three distinct grammars (R4-U1) ─────────────────────────────────

describe("StateCards grammar separation (R4-U1)", () => {
  it("missing vs gated vs broken carry distinct data-grammar values", () => {
    render(
      <>
        <CollapseCard nulls={4} source="stooq" />
        <GatedCard title="t" body="b" />
        <ErrorCard source="finnhub 502" />
      </>,
    );
    expect(screen.getByTestId("collapse-card").dataset.grammar).toBe("missing");
    expect(screen.getByTestId("gated-card").dataset.grammar).toBe("gated");
    expect(screen.getByTestId("error-card").dataset.grammar).toBe("broken");
  });

  it("collapse card names count, source and 'never estimated' (K1 doctrine)", () => {
    render(<CollapseCard nulls={5} source="yfinance" />);
    const txt = screen.getByTestId("collapse-card").textContent!;
    expect(txt).toContain("5");
    expect(txt).toContain("yfinance");
    expect(txt).toContain("No value here is estimated");
  });
});

// ── CMP-5 SignalMatrixV2 (US-3.1) ───────────────────────────────────────────

const ROWS = [
  { key: "return_5d", name: "5-day return", value: 0.031, percentile: 0.67,
    read: "firm" },
  { key: "volatility_20d", name: "20-day volatility", value: 0.34,
    percentile: 0.91, read: "elevated" },
  { key: "rsi_14", name: "RSI (14)", value: 55, percentile: null,
    percentile_note: "insufficient history (<1y)" },
];

describe("SignalMatrixV2", () => {
  it("renders human names, percentile bars, and the insufficiency note (AC-1/2)", () => {
    render(<SignalMatrixV2 rows={ROWS} source="chain" />);
    expect(screen.getByText("5-day return")).toBeTruthy();
    expect(screen.getByTestId("insufficient-rsi_14").textContent)
      .toContain("insufficient history");
    // no raw key ever renders as a visible name (Finding D ban)
    expect(screen.queryByText("return_5d")).toBeNull();
  });

  it("elevates top-3 with the fixed non-prediction caption (AC-3, QS-2)", () => {
    render(
      <SignalMatrixV2
        rows={ROWS}
        elevation={{ elevated: ["volatility_20d", "return_5d"],
                     caption:
                       "most statistically unusual for this stock \u2014 not a prediction" }}
        source="chain"
      />,
    );
    expect(screen.getByTestId("elevation-caption").textContent)
      .toContain("not a prediction");
    expect(screen.getByTestId("signal-volatility_20d").dataset.elevated)
      .toBe("true");
    expect(screen.getByTestId("signal-rsi_14").dataset.elevated)
      .toBeUndefined();
  });

  it("collapses to ONE card at \u22653 nulls \u2014 zero dash nodes (AC-4)", () => {
    const nulls = ROWS.map((r) => ({ ...r, value: null as number | null }));
    const { container } = render(
      <SignalMatrixV2 rows={nulls} source="stooq" />,
    );
    expect(screen.getByTestId("collapse-card")).toBeTruthy();
    expect(screen.queryByTestId("panel-technical")).toBeNull();
    expect(container.textContent).not.toContain("\u2014 \u2014");
    expect((container.textContent!.match(/\u2014/g) ?? []).length)
      .toBeLessThanOrEqual(1); // doctrine: no wall
  });
});

// ── CMP-6 TournamentArenaV2 (US-3.2) ───────────────────────────────────────

describe("TournamentArenaV2", () => {
  const payload = {
    winner: "Regime-filtered momentum",
    why: "won on out-of-sample stability",
    scoreboard: [
      { name: "Regime-filtered momentum", val_sharpe: 0.94, divergence: 0.11,
        deflation_penalty: 0.04 },
      { name: "ML forecaster", val_sharpe: 0.88, divergence: 0.31,
        deflation_penalty: 0.18 },
    ],
    selection_history: [],
    rl: { status: "queued_for_research_run" },
  };

  it("shows winner, divergence & penalty columns (AC-1)", () => {
    render(<TournamentArenaV2 payload={payload} />);
    expect(screen.getByTestId("winner-card").textContent)
      .toContain("Regime-filtered momentum");
    expect(screen.getByText(deskCopy.arena.colDivergence)).toBeTruthy();
    expect(screen.getByText(deskCopy.arena.colPenalty)).toBeTruthy();
  });

  it("renders the dashed E7 queue card with honest legs copy (AC-4)", () => {
    render(<TournamentArenaV2 payload={payload} />);
    const gated = screen.getByTestId("gated-card");
    expect(gated.textContent).toContain("E7");
    expect(gated.textContent).toContain("2 of 3 legs");
    expect(gated.textContent).toContain("never simulated");
  });

  it("first run renders the honest no-history line", () => {
    render(<TournamentArenaV2 payload={{ ...payload, rl: {} }} />);
    expect(screen.getByTestId("selection-history").textContent)
      .toContain("first analysis");
  });

  // Regression: the live D42 tournament section returns `winner` as an OBJECT
  // and lists rows under `candidates` with a `penalty` field — the early v2
  // draft assumed a string winner + `scoreboard`/`deflation_penalty`, which
  // rendered an object as a React child and crashed the whole Desk (React #31).
  it("renders the real backend shape (winner object + candidates + penalty)", () => {
    const real = {
      winner: {
        key: "buy_hold", name: "Buy & Hold", kind: "benchmark",
        val_sharpe: 0.0, divergence: 0.0, penalty: 0.2081, score: -0.208,
        rationale: "highest validation score across 3 walk-forward splits",
      },
      candidates: [
        { key: "buy_hold", name: "Buy & Hold", val_sharpe: 0.0,
          divergence: 0.0, penalty: 0.2081 },
        { key: "mom", name: "Momentum", val_sharpe: 0.31,
          divergence: 0.12, penalty: 0.05 },
      ],
      rl: { status: "queued_for_research_run" },
    };
    render(<TournamentArenaV2 payload={real} />);
    expect(screen.getByTestId("winner-card").textContent).toContain("Buy & Hold");
    expect(screen.getByTestId("winner-card").textContent)
      .toContain("highest validation score");
    // both candidate rows render, penalty column reads the `penalty` field
    expect(screen.getByTestId("candidate-Momentum")).toBeTruthy();
    expect(screen.getByTestId("candidate-Buy & Hold").textContent).toContain("0.2081");
  });
});

// ── CMP-2 VerdictBand (US-2.1) ──────────────────────────────────────────────

describe("VerdictBand", () => {
  const status = {
    fingerprint: "a41cdeadbeef",
    computed_at: "2026-07-07T07:41:00Z",
    alerts_unseen: 2,
    sections: [
      { id: "technical", state: "live" as const },
      { id: "tournament", state: "degraded" as const,
        reason: "RL leg queued (E7)", detail_code: "E7_GATED" as const },
      { id: "news", state: "live" as const },
      { id: "social", state: "degraded" as const,
        reason: "mentions-only fallback (E8)",
        detail_code: "E8_GATED" as const },
      { id: "fundamentals", state: "live" as const },
      { id: "sector", state: "live" as const, scope: "benchmark_only" },
    ],
  };

  it("renders six dials from API-4 only, n/6 coverage and gated names (DEC-5)", () => {
    render(
      <VerdictBand
        head={{ ticker: "UMC",
                price: { last: 25.83, as_of: "2026-07-04" },
                stance: { state: "constructive",
                          evidence_coverage: { have: 4, of: 6,
                                               gated: ["tournament", "social"] } } }}
        statusFetch={{ kind: "ready", status }}
      />,
    );
    expect(screen.getByTestId("dial-row").children.length).toBe(6);
    const chip = screen.getByTestId("stance-chip").textContent!;
    expect(chip).toContain("evidence 4/6");
    expect(chip).toContain("tournament");
    expect(screen.getByTestId("alert-badge").textContent).toContain("2");
  });

  it("hides dials with an honest notice when status is unavailable (SPEC-02 \u00A73)", () => {
    render(
      <VerdictBand head={{ ticker: "UMC" }}
                   statusFetch={{ kind: "unavailable" }} />,
    );
    expect(screen.getByTestId("status-unavailable").textContent)
      .toContain("hidden rather than guessed");
    expect(screen.queryByTestId("dial-technical")).toBeNull();
  });
});

// ── CMP-7 ForensicDrawer (US-4.1) ──────────────────────────────────────────

describe("ForensicDrawer", () => {
  const method = {
    summary: "Plain two-sentence summary of the computation.",
    factors: [{ name: "daily closes (3y window)", role: "input" }],
    detail_md: "Full method text.",
    sources: [{ name: "price provider chain", as_of: "2026-07-04",
                coverage: "740 bars" }],
  };

  it("renders the three-part anatomy in order + provenance footer (AC-1/2)", () => {
    render(
      <ForensicDrawer panel="A" method={method}
                      fingerprint="a41cdeadbeef"
                      computedAt="2026-07-07T07:41:00Z"
                      onClose={() => {}} />,
    );
    const drawer = screen.getByTestId("drawer");
    const html = drawer.innerHTML;
    expect(html.indexOf("drawer-summary"))
      .toBeLessThan(html.indexOf("drawer-factors"));
    expect(html.indexOf("drawer-factors"))
      .toBeLessThan(html.indexOf("drawer-detail"));
    const prov = screen.getByTestId("drawer-provenance").textContent!;
    expect(prov).toContain("price provider chain");
    expect(prov).toContain("a41cdeadbeef");
    expect(prov).toContain("2026-07-07T07:41:00Z");
    expect(drawer.getAttribute("aria-modal")).toBe("true");
  });

  it("ESC closes (AC-3)", () => {
    const onClose = vi.fn();
    render(<ForensicDrawer panel="B" method={method} onClose={onClose} />);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("renders the honest method-missing state", () => {
    render(<ForensicDrawer panel="F" method={null} onClose={() => {}} />);
    expect(screen.getByTestId("drawer").textContent)
      .toContain(deskCopy.drawer.methodMissing);
  });
});

// ── wording & raw-key scans over the v2 tree (NFR-7, Finding D) ────────────

describe("desk v2 source scans", () => {
  const tree = ["src/components/deskv2", "src/lib/deskCopy.ts"]
    .flatMap((p) => {
      const full = path.resolve(process.cwd(), p);
      const stat = fs.statSync(full);
      return stat.isDirectory()
        ? fs.readdirSync(full).map((f) => path.join(full, f))
        : [full];
    })
    .map((f) => fs.readFileSync(f, "utf8"))
    .join("\n");

  it("no advice verbs in desk v2 copy (wording scan)", () => {
    expect(tree).not.toMatch(/\b(buy now|should buy|we recommend|sell now)\b/i);
  });

  it("no raw feature keys hardcoded as user-facing labels", () => {
    // keys may appear as data identifiers (testids) but never inside
    // rendered label strings like ">return_5d<"
    expect(tree).not.toMatch(/>\s*return_5d\s*</);
    expect(tree).not.toMatch(/>\s*volatility_20d\s*</);
  });
});
