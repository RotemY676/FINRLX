/**
 * Dossier visuals — geometry and honesty contracts.
 *
 * A chart is a claim about data. These tests pin the claims: that nothing is
 * drawn when there is nothing to draw, that the axis is the engine's real
 * scale, and that the marked extremes are the actual extremes of the series.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { featureValue } from "@/components/simple/DossierView";
import {
  CAUTIOUS_AT,
  CONSTRUCTIVE_AT,
  EngineVotes,
  EnsembleDial,
  PriceArea,
  SentimentSplit,
} from "@/components/simple/DossierVisuals";

describe("featureValue (signal cell shape)", () => {
  // Regression guard for a live bug: the backend ships {value, status} per
  // signal, the UI assumed bare numbers, so the populated-signal count was
  // always zero and every dossier claimed "waiting on price history" while
  // holding a full set of signals. Verified against production before the fix.
  it("reads the {value,status} shape the backend actually sends", () => {
    expect(featureValue({ value: 55.2, status: "ok" })).toBe(55.2);
    expect(featureValue({ value: -0.002071, status: "ok" })).toBe(-0.002071);
  });

  it("still reads the legacy flat-number shape", () => {
    // Persisted dossiers predating the wrapper must not crash the card.
    expect(featureValue(42)).toBe(42);
  });

  it("treats a genuinely absent value as absent", () => {
    expect(featureValue({ value: null, status: "insufficient_history" })).toBeNull();
    expect(featureValue(null)).toBeNull();
    expect(featureValue(undefined)).toBeNull();
    expect(featureValue({ value: NaN, status: "ok" })).toBeNull();
  });
});

const engines = {
  technical_momentum: { score: 0.62, confidence: 0.8, stance: "buy", risk_level: "Low" },
  risk_quality: { score: -0.4, confidence: 0.5, stance: "sell", risk_level: "High" },
  news_sentiment: { score: 0.05, confidence: 0.2, stance: "hold" },
};

describe("EnsembleDial", () => {
  it("renders the score and maps engine vocabulary to research language", () => {
    render(<EnsembleDial score={0.42} confidence={0.66} stance="buy" />);
    expect(screen.getByTestId("ensemble-dial")).toBeTruthy();
    expect(screen.getByText("constructive")).toBeTruthy();
    // Raw engine words must never reach the DOM on this surface.
    expect(screen.queryByText(/\bbuy\b/i)).toBeNull();
  });

  it("states the engine's real thresholds rather than invented ones", () => {
    // If the backend thresholds move, this drifts and must be updated in both.
    expect(CONSTRUCTIVE_AT).toBe(0.3);
    expect(CAUTIOUS_AT).toBe(-0.25);
  });

  it("describes itself for screen readers", () => {
    render(<EnsembleDial score={-0.5} confidence={0.3} stance="sell" />);
    const img = screen.getByRole("img");
    expect(img.getAttribute("aria-label")).toContain("-0.50");
    expect(img.getAttribute("aria-label")).toContain("cautious");
  });
});

describe("EngineVotes", () => {
  it("shows every engine's own score, not just the blend", () => {
    render(<EngineVotes engines={engines} />);
    expect(screen.getByText("Technical momentum")).toBeTruthy();
    expect(screen.getByText("Risk & quality")).toBeTruthy();
    expect(screen.getByText("News sentiment")).toBeTruthy();
    expect(screen.getByText("0.62")).toBeTruthy();
    expect(screen.getByText("-0.40")).toBeTruthy();
  });

  it("renders nothing when there are no engines, rather than an empty frame", () => {
    const { container } = render(<EngineVotes engines={{}} />);
    expect(container.firstChild).toBeNull();
  });

  it("ignores malformed engine entries instead of drawing them as zero", () => {
    render(
      <EngineVotes
        engines={{
          ...engines,
          // A missing score is absence of evidence, not a neutral vote.
          broken: { score: undefined as unknown as number, confidence: 1, stance: "hold" },
        }}
      />,
    );
    expect(screen.queryByText("broken")).toBeNull();
  });
});

describe("SentimentSplit", () => {
  it("renders the real counts", () => {
    render(<SentimentSplit counts={{ positive: 3, neutral: 1, negative: 2 }} />);
    expect(screen.getByTestId("sentiment-split")).toBeTruthy();
    expect(screen.getByText("6")).toBeTruthy(); // total
  });

  it("renders nothing when every count is zero", () => {
    const { container } = render(<SentimentSplit counts={{ positive: 0, negative: 0 }} />);
    expect(container.firstChild).toBeNull();
  });
});

describe("PriceArea", () => {
  const series = [
    { date: "2026-01-02", close: 100 },
    { date: "2026-01-03", close: 90 },
    { date: "2026-01-06", close: 130 },
    { date: "2026-01-07", close: 120 },
  ];

  it("marks the true low and high of the series", () => {
    render(<PriceArea series={series} latestBar="2026-01-07" ticker="TST" />);
    expect(screen.getByText("low 90.00")).toBeTruthy();
    expect(screen.getByText("high 130.00")).toBeTruthy();
    expect(screen.getByText("last 120.00")).toBeTruthy();
  });

  it("reports the real first-to-last change", () => {
    render(<PriceArea series={series} latestBar="2026-01-07" ticker="TST" />);
    expect(screen.getByText("+20.0%")).toBeTruthy(); // 100 -> 120
  });

  it("draws nothing for a single point — one dot is not a trend", () => {
    const { container } = render(
      <PriceArea series={[{ date: "2026-01-02", close: 100 }]} latestBar="2026-01-02" ticker="TST" />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("survives a series containing non-finite closes", () => {
    const dirty = [
      { date: "a", close: 10 },
      { date: "b", close: NaN as unknown as number },
      { date: "c", close: 20 },
    ];
    render(<PriceArea series={dirty} latestBar="c" ticker="TST" />);
    // NaN dropped, not plotted as zero.
    expect(screen.getByText("low 10.00")).toBeTruthy();
    expect(screen.getByText("high 20.00")).toBeTruthy();
  });
});
