---
title: Paper portfolio
summary: Performance summary, drift, holdings, warnings, event log.
diataxis: reference
area: reference
updated: 2026-05-22
order: 106
---

The Paper portfolio page is your sim-to-real gate. It tracks the live behavior of a promoted recommendation using the same execution model that would be used in production, and surfaces every divergence from intent.

## Sections

### Performance summary

Top-of-page metrics: total return since promotion, annualized return, Sharpe, max drawdown, and turnover. Computed over the live-paper window — not over a historical backtest. See [Metrics](/help/reference/metrics).

### Drift from target

Per-position bar chart of *actual* paper weight vs. *target* weight from the most recent recommendation. Drift > 50 bps on a name usually means execution is leaking weight or a corporate action has not been reflected. Drift is most often a fixable execution issue, not a problem with the engine.

### Holdings

Tabular view of every paper holding with quantity, price, value, weight, and the engine's target weight.

### Warnings

A panel of operational warnings: stale prices, missing fills, drift over threshold, recent breaches.

### Event log

Reverse-chronological feed of every action that touched the paper portfolio: promotion, rebalance, fill, drift correction, manual edit. Each entry is timestamped and identifies the actor.

## See also

- [Promote a recommendation to paper](/help/guides/promote-to-paper) — the how-to.
- [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live) — why paper exists.
