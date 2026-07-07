/**
 * LEAP A5 — structural DOM tests for the Analyst Desk sections (rule P2:
 * composition changes ship rendered-DOM assertions). Fixture payloads mirror
 * the D42 section contracts from backend/tests/test_leap_a4_desk_payload.py.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  ChartSection,
  FilingsSection,
  FundamentalsSection,
  HeaderSection,
  InsiderSection,
  NewsSocialSection,
  RiskSection,
  RLLabSection,
  SignalMatrixSection,
  TournamentSection,
} from "@/components/desk/sections";

describe("HeaderSection", () => {
  it("renders the bounded stance vocabulary, never raw engine words", () => {
    render(
      <HeaderSection
        payload={{
          ticker: "NVDA",
          summary: {
            latest_close: 123.45, stance: "buy", composite_score: 0.42,
            regime: "uptrend",
            stance_kind: "research stance from the FINRLX engine ensemble — not advice",
          },
          freshness: { latest_bar: "2026-07-06" },
          config_version: "a1-leap-s4-v1",
        }}
      />,
    );
    expect(screen.getByTestId("desk-header")).toBeTruthy();
    expect(screen.getByText("constructive")).toBeTruthy(); // mapped, not "buy"
    expect(screen.queryByText(/^buy$/i)).toBeNull();
    expect(screen.getByText(/regime: uptrend/)).toBeTruthy();
  });
});

describe("ChartSection", () => {
  const payload = {
    price_series: [
      { date: "2026-06-01", close: 100 },
      { date: "2026-06-02", close: 101 },
      { date: "2026-06-03", close: 99 },
    ],
    regime_bands: [{ start: "2026-06-01", end: "2026-06-03", label: "uptrend" }],
    event_markers: [
      { date: "2026-06-02", type: "news", label: "headline", evidence_ref: "x" },
      { date: "2026-06-03", type: "rebalance", label: "tournament rebalance", evidence_ref: "y" },
    ],
  };
  it("renders the marker legend with per-type counts", () => {
    render(<ChartSection payload={payload} />);
    const legend = screen.getByTestId("marker-legend");
    expect(legend.textContent).toContain("news marker (1)");
    expect(legend.textContent).toContain("rebalance marker (1)");
    expect(legend.textContent).toContain("filing marker (0)");
  });
  it("degrades honestly without a price series", () => {
    render(<ChartSection payload={{ price_series: [] }} />);
    expect(screen.getByText(/no_price_series/)).toBeTruthy();
  });
});

describe("SignalMatrixSection", () => {
  it("renders percentile pills and honest insufficient-history notes", () => {
    render(
      <SignalMatrixSection
        payload={{
          signal_matrix: [
            { key: "return_5d", name: "5-day return", value: 0.012,
              percentile: 0.83, sparkline: [1, 2, 3], read: "short-term momentum" },
            { key: "return_60d", name: "quarter", value: 0.05,
              percentile: null, percentile_note: "insufficient history (<1y)",
              sparkline: [1, 2], read: "quarter momentum" },
            { key: "news_sentiment_7d", name: "news sentiment 7d", value: null,
              status: "missing", read: "engine input (no rolling distribution computed)" },
          ],
        }}
      />,
    );
    expect(screen.getByTestId("signal-return_5d").textContent).toContain("p83");
    expect(screen.getByTestId("signal-return_60d").textContent).toContain("insufficient history");
    expect(screen.getByTestId("signal-news_sentiment_7d").textContent).toContain(
      "no rolling distribution",
    );
  });
});

describe("TournamentSection", () => {
  const payload = {
    status: "complete",
    candidates: [
      { key: "rl_ppo", name: "PPO (FinRL ensemble)", kind: "rl", score: 0.9,
        val_sharpe: 1.2, train_sharpe: 1.4, divergence: 0.2, penalty: 0.15,
        imported_from_artifact: true },
      { key: "sma", name: "SMA cross", kind: "heuristic", score: 0.4,
        val_sharpe: 0.6, train_sharpe: 0.8, divergence: 0.2, penalty: 0.15 },
    ],
    winner: { key: "rl_ppo", rationale: "highest validation score after penalties" },
    split_windows: [
      { split: 1, train: { start: "2025-01-01", end: "2025-06-01" },
        validation: { start: "2025-06-08", end: "2025-08-01" } },
    ],
  };
  it("highlights the winner, badges research artifacts, draws split windows", () => {
    render(<TournamentSection payload={payload} />);
    expect(screen.getByTestId("cand-rl_ppo").textContent).toContain("selected");
    expect(screen.getByTestId("cand-rl_ppo").textContent).toContain("research artifact");
    expect(screen.getByTestId("cand-sma").textContent).not.toContain("selected");
    expect(screen.getByTestId("split-viz").textContent).toContain("validate 2025-06-08");
    expect(screen.getAllByText(/penalty −0.15/).length).toBe(2); // same re-deflated penalty on every row
  });
});

describe("RLLabSection", () => {
  it("renders the honest queued state", () => {
    render(
      <RLLabSection
        payload={{ status: "queued_for_research_run",
          note: "PPO/A2C/DDPG ensemble legs (ICAIF-2020 recipe) train only in the isolated research environment (operator item E7)." }}
      />,
    );
    expect(screen.getByTestId("desk-rl").textContent).toContain("queued for research run");
    expect(screen.getByTestId("desk-rl").textContent).toContain("E7");
  });
  it("renders selection history with turbulence flags when merged", () => {
    render(
      <RLLabSection
        payload={{ status: "artifact_merged", recipe: "icaif2020-ensemble",
          note: "RL agents compete under the same protocol.",
          selection_history: [
            { period: "split-1", selected: "rl_ppo", val_sharpe: 1.1, turbulence_gate: false },
            { period: "split-2", selected: "rl_a2c", val_sharpe: 0.7, turbulence_gate: true },
          ],
          turbulence_events: [{ date: "2026-04-07", action: "liquidate" }] }}
      />,
    );
    const strip = screen.getByTestId("rl-selection-strip");
    expect(strip.textContent).toContain("split-1: rl_ppo");
    expect(screen.getByText(/2026-04-07 \(liquidate\)/)).toBeTruthy();
  });
});

describe("NewsSocialSection", () => {
  it("renders dual lanes, the mentions-only label, and divergence", () => {
    render(
      <NewsSocialSection
        payload={{
          available: true,
          items_7d: [
            { date: "2026-07-01", title: "Good quarter", compound: 0.5,
              sentiment_llm: 0.8, agreement: true },
          ],
          fingpt_lane: { status: "ok", agreement_rate: 0.5 },
          social: { available: true, scored: false, label: "mentions only, unscored",
            trending: true, rank: 3, mentions_24h: 512 },
          divergence: { status: "not_applicable",
            reason: "social lane is mentions-only or unavailable — divergence requires two scored lanes" },
        }}
      />,
    );
    expect(screen.getByText(/lex 0.5/)).toBeTruthy();
    expect(screen.getByText(/llm 0.8/)).toBeTruthy();
    expect(screen.getByTestId("social-mentions").textContent).toContain("mentions only, unscored");
    expect(screen.getByTestId("divergence").textContent).toContain("not applicable");
    expect(screen.getByTestId("fingpt-status").textContent).toContain("agreement 50%");
  });
});

describe("InsiderSection", () => {
  it("always shows the noise caveat", () => {
    render(
      <InsiderSection
        payload={{ available: true, latest_mspr: 42.0,
          series_12m: [{ year: 2026, month: 6, mspr: 42.0, net_change: 5 }],
          caveat: "Insider MSPR is a noisy contextual gauge — shown for context, never as a signal." }}
      />,
    );
    expect(screen.getByTestId("insider-caveat").textContent).toContain("noisy");
    expect(screen.getByText("insider buying tilt")).toBeTruthy();
  });
  it("degrades with the named reason", () => {
    render(<InsiderSection payload={{ available: false, reason: "no_api_key" }} />);
    expect(screen.getByText(/no_api_key/)).toBeTruthy();
  });
});

describe("FundamentalsSection + FilingsSection + RiskSection", () => {
  it("renders XBRL ratio rows", () => {
    render(
      <FundamentalsSection
        payload={{ available: true,
          xbrl: { available: true, entity: "TESTCO INC", cik: 12345,
            revenue: [{ fy: 2024, value: 1.5e9 }],
            net_margin: [{ fy: 2024, value: 0.2 }],
            leverage_liab_over_equity: [{ fy: 2024, value: 2.0 }],
            dilution_yoy: [{ fy: 2024, value: 0.1 }] } }}
      />,
    );
    const el = screen.getByTestId("desk-fundamentals");
    expect(el.textContent).toContain("TESTCO INC");
    expect(el.textContent).toContain("2024: 1.5B");
    expect(el.textContent).toContain("20.0%");
  });
  it("renders the similarity delta with its non-directional read", () => {
    render(
      <FilingsSection
        payload={{ available: true,
          tone: { available: true, form: "10-K", filed_date: "2026-02-01",
            tone: { negative: 0.1, positive: 0.2 }, method: "Loughran-McDonald word lists (Finnhub filings NLP)" },
          similarity: { available: true, cosine_all: 0.71,
            read: "Lower similarity vs last year means the company changed its disclosure language materially — a documented change-in-disclosure research signal, not a directional call." } }}
      />,
    );
    expect(screen.getByTestId("similarity-delta").textContent).toContain("0.710");
    expect(screen.getByTestId("similarity-delta").textContent).toContain("not a directional call");
  });
  it("renders the regime timeline with the rule-parity disclaimer", () => {
    render(
      <RiskSection
        payload={{ regime_bands: [
            { start: "2026-01-01", end: "2026-03-01", label: "uptrend" },
            { start: "2026-03-02", end: "2026-04-01", label: "risk-off" },
          ],
          signal_matrix: [{ key: "volatility_20d", name: "20-day volatility",
            value: 0.18, percentile: 0.65 }] }}
      />,
    );
    expect(screen.getByTestId("regime-timeline").textContent).toContain("not a prediction");
    expect(screen.getByTestId("desk-risk").textContent).toContain("p65 vs own history");
  });
});
