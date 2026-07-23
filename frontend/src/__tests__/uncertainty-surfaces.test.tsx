/**
 * Phase 4 — make uncertainty, disagreement and reasoning legible.
 *
 * All three of these render payload fields the backend has always sent and the
 * UI silently dropped:
 *   - per-split validation Sharpe (a mean hides a model carried by one window)
 *   - distance to the nearest category boundary (0.29 and 0.85 both read
 *     "neutral"; only the distance separates them)
 *   - each engine's own drivers and caveats
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SplitConsistency } from "@/components/simple/DossierView";
import {
  CAUTIOUS_AT,
  CONSTRUCTIVE_AT,
  EngineVotes,
  EnsembleDial,
  nearestBoundary,
} from "@/components/simple/DossierVisuals";

describe("SplitConsistency", () => {
  it("distinguishes a consistent winner from one carried by a single split", () => {
    const { unmount } = render(<SplitConsistency splits={[0.4, 0.4, 0.5]} />);
    expect(screen.getByTestId("split-consistency").textContent).toContain("3 of 3");
    expect(screen.getByTestId("split-consistency").textContent).toContain("consistent");
    unmount();

    render(<SplitConsistency splits={[-0.6, 0.1, 1.8]} />);
    const text = screen.getByTestId("split-consistency").textContent ?? "";
    expect(text).toContain("2 of 3");
    expect(text).toContain("not evenly earned");
  });

  it("shows each split's real value", () => {
    render(<SplitConsistency splits={[-0.6, 0.1, 1.8]} />);
    expect(screen.getByText("-0.60")).toBeTruthy();
    expect(screen.getByText("1.80")).toBeTruthy();
  });

  it("says so when every split was negative", () => {
    render(<SplitConsistency splits={[-0.2, -0.4]} />);
    expect(screen.getByTestId("split-consistency").textContent).toContain("negative in every");
  });

  it("draws nothing without at least two splits — one window is not a spread", () => {
    const { container, rerender } = render(<SplitConsistency splits={[0.5]} />);
    expect(container.firstChild).toBeNull();
    rerender(<SplitConsistency splits={undefined} />);
    expect(container.firstChild).toBeNull();
  });
});

describe("nearestBoundary", () => {
  it("measures distance to the boundary it has not crossed", () => {
    const near = nearestBoundary(0.26);
    expect(near?.edge).toBe(CONSTRUCTIVE_AT);
    expect(near?.gap).toBeCloseTo(0.04);
    expect(near?.toward).toBe("constructive");
  });

  it("works on the cautious side too", () => {
    const near = nearestBoundary(-0.2);
    expect(near?.edge).toBe(CAUTIOUS_AT);
    expect(near?.toward).toBe("cautious");
  });

  it("returns nothing for a non-finite score rather than guessing", () => {
    expect(nearestBoundary(NaN)).toBeNull();
  });
});

describe("ThresholdProximity via EnsembleDial", () => {
  it("states the distance to the boundary", () => {
    render(<EnsembleDial score={0.26} confidence={0.6} stance="hold" />);
    expect(screen.getByTestId("threshold-proximity").textContent).toContain("0.04");
  });

  it("flags a reading sitting on a boundary as label-sensitive", () => {
    render(<EnsembleDial score={0.29} confidence={0.6} stance="hold" />);
    expect(screen.getByTestId("threshold-proximity").textContent).toContain("sensitive");
  });

  it("does not flag a reading far from any boundary", () => {
    render(<EnsembleDial score={0.85} confidence={0.6} stance="buy" />);
    expect(screen.getByTestId("threshold-proximity").textContent).not.toContain("sensitive");
  });
});

describe("EngineVotes reasoning", () => {
  const engines = {
    technical_momentum: {
      score: 0.6,
      confidence: 0.8,
      stance: "buy",
      drivers: ["60d return +18.2%", "20d return 4.1%"],
      caveats: ["Volatility 34% — elevated"],
    },
    risk_quality: { score: -0.2, confidence: 0.5, stance: "hold" },
  };

  it("surfaces the caveat count before the reader has to expand anything", () => {
    render(<EngineVotes engines={engines} />);
    expect(screen.getByText("1 caveat")).toBeTruthy();
  });

  it("renders the engine's drivers and caveats verbatim on expand", () => {
    render(<EngineVotes engines={engines} />);
    fireEvent.click(screen.getByText("Why this vote"));
    const panel = screen.getByTestId("engine-why-technical_momentum");
    expect(panel.textContent).toContain("60d return +18.2%");
    expect(panel.textContent).toContain("Volatility 34% — elevated");
  });

  it("offers no reasoning control for an engine that reported none", () => {
    render(<EngineVotes engines={{ risk_quality: engines.risk_quality }} />);
    expect(screen.queryByText("Why this vote")).toBeNull();
  });
});
