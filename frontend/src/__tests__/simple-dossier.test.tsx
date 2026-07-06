/**
 * PROGRAM LEAP S5 — One Screen dossier rendering tests.
 * Council coverage: UX Critic (all key regions render; degraded states
 * labeled) and Truthfulness Auditor (disclaimers, tournament rationale,
 * honest RL status all visible).
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DossierView } from "../app/simple/DossierView";

const baseDossier = {
  ticker: "TEST",
  generated_at: "2026-07-06T12:00:00Z",
  freshness: { latest_bar: "2026-07-03", bars: 500, news_source_available: true },
  summary: {
    latest_close: 123.45,
    stance: "hold",
    composite_score: 0.05,
    avg_confidence: 0.6,
    regime: "uptrend",
    stance_kind: "research stance from the FINRLX engine ensemble — not advice",
  },
  sections: {
    technical: {
      regime: { label: "uptrend", detail: "price above SMA50", kind: "research overlay — rule-based label, not a prediction" },
      composite: { drivers: ["[technical_momentum] 20d return positive"], caveats: [] },
      engines: {},
    },
    news_sentiment: {
      available: true,
      note: null,
      counts: { positive: 3, neutral: 2 },
      items_7d: [
        { date: "2026-07-02", title: "Test headline", sentiment: "positive", compound: 0.4 },
      ],
    },
    fundamentals: { available: false, note: "Fundamentals join the dossier when a provider is configured." },
    model_insight: {
      status: "complete",
      n_splits: 3,
      deflation_penalty: 0.21,
      candidates: [
        { key: "sma_xover", name: "SMA(20/50) crossover", kind: "heuristic", train_sharpe: 0.9, val_sharpe: 0.8, divergence: 0.1, score: 0.5 },
        { key: "ml_gbr", name: "ML return forecaster", kind: "ml", train_sharpe: 1.4, val_sharpe: 0.3, divergence: 1.1, score: -0.4 },
      ],
      winner: {
        name: "SMA(20/50) crossover", kind: "heuristic", score: 0.5,
        rationale: "Selected 'SMA(20/50) crossover' — highest validation score after an overfitting-divergence penalty.",
      },
      rl: { status: "queued_for_research_run", note: "RL candidates train only in the isolated research environment." },
    },
  },
  price_series: [
    { date: "2026-07-01", close: 120 },
    { date: "2026-07-02", close: 121.5 },
    { date: "2026-07-03", close: 123.45 },
  ],
  stages: [{ stage: "ingest — price history", ms: 800 }],
  disclaimers: [
    "Research analysis, not investment advice.",
    "Past performance does not guarantee future results.",
  ],
  served_from_cache: false,
} as never;

describe("DossierView", () => {
  it("renders the summary bar, all four cards, and the freshness stamp", () => {
    render(<DossierView dossier={baseDossier} />);
    expect(screen.getByTestId("dossier-ticker").textContent).toBe("TEST");
    expect(screen.getByTestId("stance-badge").textContent).toContain("hold");
    for (const id of ["card-price", "card-technical", "card-news", "card-fundamentals", "card-model"]) {
      expect(screen.getByTestId(id)).toBeTruthy();
    }
    expect(screen.getByTestId("freshness").textContent).toContain("2026-07-03");
  });

  it("explains the automatic model selection and shows the honest RL status", () => {
    render(<DossierView dossier={baseDossier} />);
    expect(screen.getByTestId("tournament-winner").textContent).toContain("SMA(20/50) crossover");
    expect(screen.getByTestId("card-model").textContent).toContain("overfitting-divergence penalty");
    expect(screen.getByTestId("rl-status").textContent).toContain("queued for research run");
    expect(screen.getByTestId("scoreboard")).toBeTruthy();
  });

  it("always shows the research-not-advice disclaimers", () => {
    render(<DossierView dossier={baseDossier} />);
    expect(screen.getByTestId("disclaimers").textContent).toContain("not investment advice");
  });

  it("labels a degraded news section instead of hiding it", () => {
    const degraded = structuredClone(baseDossier) as typeof baseDossier & {
      sections: { news_sentiment: { available: boolean; note: string } };
    };
    degraded.sections.news_sentiment.available = false;
    degraded.sections.news_sentiment.note =
      "News source unavailable — section degraded, analysis continued without it.";
    render(<DossierView dossier={degraded as never} />);
    expect(screen.getByTestId("news-degraded").textContent).toContain("degraded");
  });

  it("shows an honest message when history is insufficient for the tournament", () => {
    const insufficient = structuredClone(baseDossier) as never as {
      sections: { model_insight: { status: string; winner: null; note: string } };
    };
    insufficient.sections.model_insight = {
      status: "insufficient_history",
      winner: null,
      note: "Fewer than 30 weekly observations — the tournament needs more history.",
    } as never;
    render(<DossierView dossier={insufficient as never} />);
    expect(screen.getByTestId("tournament-insufficient").textContent).toContain("needs more history");
  });
});
