---
title: The weight-centric pipeline
summary: Why FINRLX treats portfolio-weight vectors as the universal contract between every layer.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 1
---

FINRLX is built around a single design choice: **the portfolio-weight vector is the only thing that crosses the boundary between strategy logic and execution.** An equal-weight allocator, a classical mean-variance optimizer, and a reinforcement-learning agent all produce the same shape of output — a vector that sums to one across the assets in the universe — and that same vector flows identically through backtesting and live execution.

If you have used the upstream FinRL framework, this is the major architectural step FINRLX adds: instead of agents and environments owning the trade decision, the agent owns only the *intent*. Translation from intent to fills happens once, in a single execution layer.

## What "weight" means here

A weight is a target allocation, not a trade. A row like

| AAPL | MSFT | GOOG | CASH |
|---|---|---|---|
| 0.28 | 0.22 | 0.15 | 0.35 |

says "as of this rebalance, the portfolio should be 28% AAPL, 22% MSFT, 15% GOOG, and 35% cash". The execution layer compares this to current holdings and emits the trades that close the gap. Slippage, partial fills, and broker quirks live entirely on that execution side; they do not leak back into the engine.

## Why the contract matters

Three properties fall out of this design:

1. **Comparability.** Any engine that produces weights can be put next to any other engine in the [Comparison page](/help/reference/pages/comparison). Equal-weight, risk-parity, PPO, the ensemble — same x-axis, same y-axis, same overlay rules.
2. **Reproducibility.** A recommendation can be replayed exactly by re-running the weight pipeline against the same data snapshot and the same policy controls. The execution layer adds variance (fills) but the *decision* is deterministic.
3. **Substitutability.** Swapping the engine — say, from an RL agent to a classical optimizer — does not require re-plumbing the backtest harness, the risk overlays, or the audit trail.

## Layers that share the contract

The pipeline has four layers. Each one receives weights from the layer above and either transforms or consumes them.

- **Engine** — produces raw weights from market state. This is where PPO, A2C, the ensemble, equal-weight, or any classical optimizer lives. See [Agents and engines](/help/concepts/agents-and-engines).
- **Risk overlay** — projects raw weights onto the feasible set defined by your policy controls (cash floor, exposure caps, sector caps, turbulence throttle). See [Risk overlays](/help/concepts/risk-overlays).
- **Backtest / Paper / Live** — three modes of *consuming* the post-overlay weights. They differ in data quality and execution realism but not in the upstream contract. See [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live).
- **Governance** — records the full chain of evidence behind each weight vector: the data snapshot, the engine version, the overlay decisions, the timestamp, the user. See [Governance and audit](/help/concepts/governance-and-audit).

## What the contract is *not*

The weight-centric design narrows the engine's responsibility. Things explicitly outside the engine's job:

- **Sizing in shares.** Engines do not pick share counts. The execution layer translates weights into orders.
- **Order routing.** Smart-order-routing logic, venue selection, and broker-specific quirks belong to execution.
- **Cost modeling.** Transaction costs and slippage are applied to the *fills* produced by execution, not to the *weights* produced by the engine. This separation matters: it prevents engines from being optimized against a specific (and possibly wrong) cost model.

## Trade-offs you should know

Weight-centric is a deliberate constraint, and it has costs.

- **No order-book reasoning.** An engine cannot say "buy 10,000 shares of AAPL only if the bid-ask is tighter than 2 bps." That kind of logic lives in execution. If you need it, it goes outside the engine layer.
- **No path-dependent intra-day shaping.** Weights are evaluated at the rebalance frequency. Intra-day execution shape (TWAP, VWAP, etc.) is an execution choice.
- **No asymmetric trade pacing.** If you want to liquidate over five days but enter over one, you need to model that as a sequence of weight targets, not as a single trade with a schedule.

In practice these trade-offs are worth it: they keep the engine layer comparable, testable, and reproducible. The complexity moves to execution, where it can be measured and audited separately.

## See also

- [Universe and features](/help/concepts/universe-and-features) — what the engine sees.
- [Agents and engines](/help/concepts/agents-and-engines) — the engines that produce weights.
- [Risk overlays](/help/concepts/risk-overlays) — what happens to weights before they leave the engine layer.
