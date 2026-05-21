---
title: Backtest vs. paper vs. live
summary: Why these three numbers diverge — and how to read each.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 6
---

A strong backtest is not a promise of strong live returns. Paper trading sits between them and exposes the gap. The three modes share the same engine and the same [weight-centric contract](/help/concepts/weight-centric-pipeline), but they differ along three dimensions: **data quality**, **execution realism**, and **regime coverage**. Understanding the differences is how you know which numbers to trust.

## Backtest

A backtest replays historical decisions against historical data. It is the cheapest mode — runs in seconds to minutes — and the easiest to mislead with.

What a FINRLX backtest gives you:

- Point-in-time data, including survivorship-corrected universe membership.
- The engine's full state at every decision, replayable.
- A model of transaction cost and slippage (you choose the model in the experiment configuration).
- Multiple benchmarks (equal weight, the engine's own prior, configurable extras) overlaid on the equity curve.

What a backtest **cannot** give you:

- **Real fills.** The cost model is an approximation. Real fills depend on order size, time of day, venue selection, and a dozen things the model does not see.
- **Regime coverage.** The backtest window is what it is. If the next regime is unlike anything in the window, the backtest tells you nothing about it.
- **Operational reality.** Backtests assume the data feed was always fresh and the queue was always healthy. Live, that is not always true.

Treat a backtest as a *necessary but not sufficient* indicator. A strategy that fails backtest fails. A strategy that passes backtest *might* succeed live; the only way to know is to keep running it.

## Paper

Paper trading is the same engine writing to a portfolio that uses live prices, the same execution model that would be used in production, but no real capital at risk. Paper sits between backtest and live for one specific reason: it adds **operational realism** without adding broker risk.

What paper exposes that backtest does not:

- **Data-feed timing.** If a feed is late by 90 seconds, paper sees the delay; backtest does not.
- **Queue health.** Paper depends on the publication queue actually delivering. Backtest assumes it does.
- **Engine drift.** Paper runs the *current* engine version with the *current* policy controls, every cycle. Backtest runs a frozen snapshot.
- **Real time horizons.** Paper exposes you to live regime change. Backtest is a sample, not an experience.

Paper is the recommended last gate before live. Running it for at least one rebalance cycle — for daily-rebalancing strategies, that's about 30 trading days — gives you data that backtest cannot produce.

## Live

Live is paper with real capital. Same engine, same policy, same execution model, real broker fills. The only thing live adds is broker risk: partial fills, slippage on real liquidity, market impact for sizable positions, settlement timing.

When backtest and paper agreed for 30+ days and live underperforms, the most likely explanations are:

- Slippage was worse than the cost model assumed (real spreads, real impact).
- The regime shifted in a way that paper did not yet see.
- An operational issue caused a missed cycle.

The first is correctable by tightening the cost model. The second is the unavoidable cost of doing this at all. The third is what the [Ops page](/help/reference/pages/ops) is for.

## How much gap is "normal"?

There is no universal number, but two heuristics:

- **Backtest to paper.** A well-modeled backtest should differ from paper by *less than the cost model's standard error*. If paper is consistently 30+ bps annualized below backtest, the cost model is too optimistic — tighten it.
- **Paper to live.** A correctly executed strategy should differ from paper by *less than the broker's typical slippage*. If live is consistently 50+ bps below paper, you have a slippage problem (sizing too aggressive, illiquid names, wrong order type).

## What to compare across the three

Three comparisons are useful and one is not:

- ✅ **Equity curves at the same risk-adjusted metric** (Sharpe, Sortino). A backtest with higher Sharpe than paper means the cost model is too optimistic.
- ✅ **Position-level drift.** If backtest holds AAPL at 8% and paper drifts to 6% within a week, execution is leaking weight.
- ✅ **Turnover.** Cost amplifies with turnover. A backtest with similar Sharpe but 3x the turnover of paper is suspect.
- ❌ **Absolute returns.** They will differ for many honest reasons; chasing them tells you very little.

## See also

- [The weight-centric pipeline](/help/concepts/weight-centric-pipeline) — what's shared across the three modes.
- [Run a backtest](/help/guides/run-a-backtest) — how to start one.
- [Promote a recommendation to paper](/help/guides/promote-to-paper) — how to cross the first gate.
- [Known pitfalls](/help/concepts/known-pitfalls) — including reading a backtest as a promise.
