---
title: Replay
summary: Replay any past recommendation exactly as it was at decision time.
diataxis: reference
area: reference
updated: 2026-05-22
order: 104
---

Replay is the post-trade review tool. Pick a past recommendation from the list, and the screen reconstructs the rationale, positions, and pipeline-stage snapshots that produced it. The reconstruction is deterministic — see [Governance and audit](/help/concepts/governance-and-audit#the-guarantees).

## Sections

### Available replays

Filterable list of past recommendations. Filters: date range, engine, status (published / draft / deferred / promoted). Click a row to load it.

### Replay detail

Once a recommendation is loaded, this section shows the policy controls in force, the regime label, the turbulence value, and the data snapshot ID. These are the inputs to the engine at decision time.

### Rationale at snapshot

The evidence narrative *as it would have read* at decision time, not as it reads now. If the underlying narrative generator was updated since, the diff is surfaced.

### Positions at snapshot

Tabular view of every position with weight, value, and the engine's rationale per name. "Click a row to inspect" is the inline hint.

### Pipeline stage snapshots

Four collapsible panels showing the state at each pipeline stage at decision time: data, features, engine output, overlay output. The engine output panel exposes the raw (pre-overlay) weights; the overlay output panel exposes the published weights and the constraints that fired.

## Actions

- **Re-derive with current engine** — re-runs the engine on the saved data snapshot with the *current* engine version, and surfaces the diff between then and now.
- **Fork to new backtest** — clones the configuration into a new experiment in [Backtests](/help/reference/pages/backtests).
- **Export evidence** — downloads the full audit-trail entry as JSON.

## See also

- [Replay a decision](/help/guides/replay-a-decision) — the how-to.
- [Governance and audit](/help/concepts/governance-and-audit) — the concept.
