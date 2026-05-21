---
title: Known pitfalls
summary: Overfitting, leakage, survivorship — the failure modes the team has seen most.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 8
---

The dominant failure mode of any ML-driven trading system is not "the model was wrong." It is "the model was right about the training window in a way that does not generalize." This page lists the specific pitfalls FINRLX defends against, where in the product the defenses live, and what residual risk you should still inspect manually.

## Backtest overfitting

**What it is.** A model that fits the noise in the backtest window rather than learning a generalizable policy. The 2022 paper *"A Practical Approach to Backtest Overfitting"* (Arnott et al., arXiv:2209.05559) formalized this as a hypothesis test and showed that *"existing RL-based methods suffer from considerable overfitting, with trained models prone to memorize the history instead of learning generalizable policies."*

**Where FINRLX defends.** Walk-forward training (the engine is retrained on a rolling window, never the whole history at once). Ensemble selection by *rolling out-of-sample* Sharpe, not in-sample Sharpe. Backtest configurations that require explicit train/validation/test splits, never random splits.

**Residual risk.** If you tune hyperparameters by re-running the *test* set, you have overfit at the human level. FINRLX cannot prevent that. The discipline is: pick hyperparameters on validation, look at test once.

## Data leakage

**What it is.** Any path by which test-set information influences training. The classic example is using normalization statistics computed across the entire dataset — train and test — for training data. Another is using forward-looking features (EPS dated 31 March but only published in April).

**Where FINRLX defends.** Features are stamped with `event_date` and `available_date`; engines see only `available_date ≤ decision_time`. Normalization is computed per-window or against a held-out prefix, never globally. The feature spec is recorded in the audit trail so leakage can be traced.

**Residual risk.** Custom features you add are only as good as their `available_date` field. If you fill it incorrectly, you have re-introduced the bias. See [Universe and features](/help/concepts/universe-and-features).

## Survivorship bias

**What it is.** A universe that silently excludes names that were delisted, merged, or removed. A backtest run on "today's S&P 500" between 2010 and 2020 will *not* include any company that was in the index in 2010 but is not in it today. Those companies are disproportionately the failures.

**Where FINRLX defends.** Universes are managed with point-in-time membership. On 2015-03-14, the engine sees the names that were in the universe *on that date*, not the names in it today.

**Residual risk.** Custom universes you build from external sources may not carry membership intervals. The [Universe page](/help/reference/pages/universe) flags any universe that does not have intervals as "survivorship-unverified."

## Underestimated transaction cost and slippage

**What it is.** A backtest that assumes 5 bps per round-trip and runs into 25 bps in production. The FinRL FAQ flatly warns that *"intraday with daily defaults silently underperforms"* for exactly this reason. A 2019 study on tax-aware portfolio construction (arXiv:1907.12093) showed that ignoring taxes alone could erode portfolio returns by more than 62%.

**Where FINRLX defends.** Multiple cost models ship with the product; you choose one at backtest configuration. Paper trading exposes the gap between the chosen cost model and live broker fills. Live deployment is gated on a paper period precisely so this can be observed.

**Residual risk.** Your cost model is your choice. Pick a pessimistic one and you are safer; pick an optimistic one and you will be surprised. See [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live).

## Reward hacking

**What it is.** A reinforcement-learning agent exploits a loophole in the reward function to score high without doing what you intended. Example: a cost-free environment rewards turnover, the agent learns to churn the portfolio every step, the "performance" is enormous and entirely fictional.

**Where FINRLX defends.** Reward functions always include transaction cost. Turnover is bounded by the overlay. The audit trail records turnover per cycle so reward hacking shows up as an anomaly even before it costs you money.

**Residual risk.** Custom reward functions can re-open the loophole. If you change the reward, run the new agent through equal-weight comparison first.

## Single-stock training

**What it is.** Training an agent on one ticker and expecting it to generalize. The FinRL documentation FAQ explicitly says: *"Agents perform poorly with single stocks due to limited state space — use the multi-stock environment, and after training only use the single stock to trade."*

**Where FINRLX defends.** Universe size validation. Shipped engines target universes of ≥ 20 names. Single-stock training is possible but flagged.

**Residual risk.** None if you respect the recommendation; full risk if you ignore it.

## Buy-and-hold may be unbeatable

**What it is.** In low-volatility steady-growth periods, a passive equal-weight portfolio can outperform every active strategy. The FinRL FAQ warns about this explicitly: in a steady bull, beating equal weight is *hard*, and trying to do so can introduce more risk than it removes.

**Where FINRLX defends.** Every backtest renders equal-weight as the baseline benchmark. If an engine cannot beat equal weight on Sharpe across the backtest window, that is the headline finding, not a footnote.

**Residual risk.** Cognitive: it is uncomfortable to ship "the buy-and-hold portfolio." The honest response when active strategies do not win is *not* to ship them anyway.

## Regime change

**What it is.** Markets are non-stationary. A model trained in regime *A* and deployed in regime *B* will underperform — often dramatically. The FinRL-Meta paper (arXiv:2211.03107) frames this as a core challenge: *"The performance of RL policies is sensitive to hyperparameters, market noise, and random seeds; policy instability can come from value-function approximation errors."*

**Where FINRLX defends.** Rolling retraining (walk-forward) so the policy refreshes against recent data. Regime classifier + turbulence index throttle so the *current* recommendation is sized to *current* conditions.

**Residual risk.** A regime entirely outside the training history is invisible to the system. The defense is operational: monitor live performance, halt if it diverges sharply from paper.

## See also

- [The weight-centric pipeline](/help/concepts/weight-centric-pipeline) — the contract these defenses share.
- [Regimes and turbulence](/help/concepts/regimes-and-turbulence) — the regime-change defense.
- [Risk overlays](/help/concepts/risk-overlays) — the overlay-level defenses.
- [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live) — why paper exists.
- [Governance and audit](/help/concepts/governance-and-audit) — how all of this stays inspectable.
