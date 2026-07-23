/**
 * Model lab — the verdict and RL lane render honestly.
 *
 * The dashboard's whole reason to exist is turning a real comparison into one
 * truthful read. These pin the two properties that keep it honest: a passive
 * winner is shown as "no active edge", and the RL lane is gated (never faked)
 * when no artifact exists.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ModelLab } from "@/components/models/ModelLab";

function mockDossier(insight: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ data: { sections: { model_insight: insight } } }),
    })),
  );
}

const PASSIVE_WINNER = {
  status: "complete",
  n_splits: 3,
  deflation_penalty: 0.208,
  winner: { key: "buy_hold", name: "Buy & Hold", kind: "benchmark", rationale: "…" },
  candidates: [
    {
      key: "buy_hold", name: "Buy & Hold", kind: "benchmark",
      val_sharpe: 1.65, train_sharpe: 1.6, divergence: 0.05, penalty: 0.208,
      score: 0.79, per_split_val_sharpe: [3.49, -1.64, 3.09],
    },
    {
      key: "tech_mom", name: "Tech-momentum only", kind: "heuristic",
      val_sharpe: 0.28, train_sharpe: 0.3, divergence: 0.02, penalty: 0.208,
      score: -0.02, per_split_val_sharpe: [0.41, 0.0, 0.42],
    },
  ],
  rl: { status: "queued_for_research_run", note: "PPO/A2C/DDPG train only in the research worker (E7)." },
  verdict: {
    verdict: "inconclusive",
    headline: "No active model beat passive holding — no active edge found.",
    reasons: ["The best-validated candidate is a passive benchmark (Buy & Hold); no active model beat simply holding."],
    models_compared: 2,
    winner_name: "Buy & Hold",
    winner_score: 0.79,
    winner_is_passive: true,
    rl_participated: false,
    disclaimer: "Research synthesis of a walk-forward model comparison — not investment advice, not a prediction.",
  },
};

afterEach(() => vi.unstubAllGlobals());

describe("ModelLab", () => {
  it("shows a passive winner as no active edge, never as a signal", async () => {
    mockDossier(PASSIVE_WINNER);
    render(<ModelLab />);
    fireEvent.change(screen.getByLabelText("Ticker"), { target: { value: "AAPL" } });
    fireEvent.click(screen.getByRole("button", { name: /compare/i }));

    await waitFor(() => expect(screen.getByTestId("model-verdict")).toBeTruthy());
    const verdict = screen.getByTestId("model-verdict");
    expect(verdict.textContent).toContain("no active edge");
    expect(verdict.textContent).toContain("not investment advice");
  });

  it("gates the RL lane honestly when no artifact exists", async () => {
    mockDossier(PASSIVE_WINNER);
    render(<ModelLab />);
    fireEvent.change(screen.getByLabelText("Ticker"), { target: { value: "AAPL" } });
    fireEvent.click(screen.getByRole("button", { name: /compare/i }));

    await waitFor(() => expect(screen.getByTestId("rl-lane")).toBeTruthy());
    expect(screen.getByTestId("rl-lane").textContent).toContain("not yet trained");
  });

  it("renders every candidate with its real score", async () => {
    mockDossier(PASSIVE_WINNER);
    render(<ModelLab />);
    fireEvent.change(screen.getByLabelText("Ticker"), { target: { value: "AAPL" } });
    fireEvent.click(screen.getByRole("button", { name: /compare/i }));

    await waitFor(() => expect(screen.getByTestId("model-row-buy_hold")).toBeTruthy());
    expect(screen.getByTestId("model-row-tech_mom")).toBeTruthy();
    expect(screen.getByTestId("model-row-buy_hold").textContent).toContain("selected");
  });

  it("marks RL as included when an artifact merged", async () => {
    mockDossier({
      ...PASSIVE_WINNER,
      rl: { status: "artifact_merged", recipe: "icaif2020-ensemble", agents: ["rl_ppo", "rl_a2c"] },
      verdict: { ...PASSIVE_WINNER.verdict, rl_participated: true },
      candidates: [
        ...PASSIVE_WINNER.candidates,
        {
          key: "rl_ppo", name: "PPO (FinRL ensemble)", kind: "rl",
          val_sharpe: 0.3, train_sharpe: 0.4, divergence: 0.1, penalty: 0.208,
          score: -0.06, per_split_val_sharpe: [0.5, -0.2, 0.6], imported_from_artifact: true,
        },
      ],
    });
    render(<ModelLab />);
    fireEvent.change(screen.getByLabelText("Ticker"), { target: { value: "AAPL" } });
    fireEvent.click(screen.getByRole("button", { name: /compare/i }));

    await waitFor(() => expect(screen.getByTestId("rl-lane").textContent).toContain("RL agents included"));
    expect(screen.getByTestId("model-row-rl_ppo").textContent).toContain("research artifact");
  });
});
