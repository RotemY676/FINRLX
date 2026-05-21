---
title: Run a backtest
summary: Open the Backtests page, configure an experiment, run it, and read the result.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 1
---

This guide walks through configuring and running a backtest from the [Backtests page](/help/reference/pages/backtests). It assumes you know which universe and which engine you want to test — see [Universe and features](/help/concepts/universe-and-features) and [Agents and engines](/help/concepts/agents-and-engines) if you are still deciding.

## Before you start

You need: an active universe with the green **Ready** badge on its readiness panel, an engine you have selected from the [templates](/help/reference/pages/templates) or configured manually, and a sensible date range (at least 12 months of point-in-time data).

## Steps

1. **Open Backtests.** From the sidebar under WORKSPACES, click **Backtests**.
2. **Click "New experiment"** in the top-right of the experiments table.
3. **Pick the universe.** The universe selector lists every available universe; the one you used most recently is pre-selected.
4. **Pick the engine.** Equal weight is fastest; PPO is the typical RL starting point; the ensemble takes longest but adapts to regime.
5. **Set the date range.** Pick a window that includes at least one regime transition — pure-bull or pure-bear windows produce misleading results.
6. **Choose a cost model.** "Realistic" (default) approximates typical retail spreads and impact. Pick "Pessimistic" if you plan to deploy on illiquid names.
7. **Confirm and run.** The experiment appears in the table with `running` status. Daily windows of ~5 years finish in under two minutes on the shared compute pool.
8. **Read the result.** When the row turns `completed`, click it. The metrics row (Sharpe, Sortino, Calmar, max drawdown, turnover) is your headline; the equity curve is the picture.

## Read the result honestly

- **Compare against the equal-weight benchmark on the same window.** If you do not beat it on Sharpe, the engine is not earning its complexity.
- **Look at the turbulence shading on the equity curve.** A strategy that won only in calm shading is fragile. See [Regimes and turbulence](/help/concepts/regimes-and-turbulence).
- **Check turnover.** A Sharpe-1.5 strategy with 300% annual turnover often fails in paper because cost erodes the headline.

## What to do next

- If the backtest is strong on a single window, **re-run on a different window** to test robustness.
- If it survives the second window, [promote to paper](/help/guides/promote-to-paper).
- If it fails, revisit the universe, the features, or the engine choice. Do not tune hyperparameters on the test window — that is the path to [overfitting](/help/concepts/known-pitfalls#backtest-overfitting).

## See also

- [Backtests](/help/reference/pages/backtests) — the page reference.
- [Metrics](/help/reference/metrics) — formulas for the columns.
- [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live) — what backtests tell you and what they don't.
