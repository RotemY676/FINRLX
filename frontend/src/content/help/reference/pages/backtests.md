---
title: Backtests
summary: Experiments list, equity curve, configuration, promotion review, provenance.
diataxis: reference
area: reference
updated: 2026-05-22
order: 105
---

The Backtests page is the experiment workbench.

## Sections

### Experiments table

Every backtest run, with columns: name, universe, engine, date range, status, Sharpe, max drawdown, last-run timestamp. Sortable on every column. Click a row to load the experiment detail.

### Promotion review — Shadow ML

If an experiment has passed the configured promotion criteria, this panel surfaces it as a candidate. The block shows the metrics that triggered the candidacy and offers a one-click "Promote to paper" path.

### Equity curve (base 100)

Time-series chart of the experiment's portfolio value, indexed to 100 at the start. Overlaid with the configured benchmarks (equal weight by default). The chart is shaded by [turbulence](/help/concepts/regimes-and-turbulence) so you can see how much of the return came in calm vs. turbulent windows.

### Experiment configuration

Read-only view of the parameters in force for the selected experiment: universe, engine, feature spec, cost model, train/validation/test split, random seed, total_timesteps.

### Provenance

Audit-trail entry for the experiment, including the user who created it, the engine version it ran against, and any policy controls embedded in the run.

## Actions

- **Run** — starts the experiment with its current configuration.
- **Clone** — creates a new experiment seeded with this one's configuration.
- **Promote** — sends the result to shadow ML for paper promotion.
- **Export** — downloads the full experiment artifact (configuration + results) as JSON.

## See also

- [Run a backtest](/help/guides/run-a-backtest) — the how-to.
- [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live) — what backtests are good for and what they aren't.
- [Metrics](/help/reference/metrics) — formula definitions for the columns.
