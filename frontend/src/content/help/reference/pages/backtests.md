---
title: Backtests
summary: Experiments list, equity curve, configuration, promotion review, provenance.
diataxis: reference
area: reference
updated: 2026-05-22
order: 105
---

The Backtests page is the experiment workbench.

<Annotated
  src="/help/screenshots/backtests.png"
  alt="The Backtests page showing the experiments table, the promotion review block, and the equity-curve panel"
  width={1440}
  height={900}
  callouts={[
    { x: 35, y: 16, n: 1, label: "Experiments table — every backtest run, with status, return, and a Pipeline / Seed pill identifying its provenance." },
    { x: 88, y: 22, n: 2, label: "Status pill — completed (green) means the experiment finished cleanly; check the audit row to confirm provenance." },
    { x: 30, y: 48, n: 3, label: "Promotion Review block — surfaces an experiment as a candidate when it passes the configured promotion criteria." },
    { x: 22, y: 65, n: 4, label: "Metrics row — Total Return, Annualized Return, Max Drawdown, Sharpe, Volatility, Total Trades, Avg Turnover. See Reference → Metrics." },
    { x: 22, y: 86, n: 5, label: "Equity curve — base 100 indexed to the start of the window; turbulence shading overlays calm vs. stressed regimes." },
  ]}
  caption="The Backtests page on the live workspace. The promotion-review block is the bridge from a backtest to a paper promotion."
/>

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
