---
title: Replay
summary: Replay any past recommendation exactly as it was at decision time.
diataxis: reference
area: reference
updated: 2026-05-22
order: 104
---

Replay is the post-trade review tool. Pick a past recommendation from the list, and the screen reconstructs the rationale, positions, and pipeline-stage snapshots that produced it. The reconstruction is deterministic — see [Governance and audit](/help/concepts/governance-and-audit#the-guarantees).

<Annotated
  src="/help/screenshots/replay.png"
  alt="The Replay / Forensics page showing the Available Replays list with status pills and the Replay Detail header below"
  width={1440}
  height={900}
  callouts={[
    { x: 30, y: 10, n: 1, label: "Page header — Replay / Forensics. Count below shows how many recommendations are available for forensic inspection." },
    { x: 30, y: 17, n: 2, label: "Active replay row — highlighted row is the recommendation currently loaded; click any other row to switch context." },
    { x: 88, y: 17, n: 3, label: "Status pill — draft / staged / published / deferred. Pills mirror the recommendation's lifecycle state at the snapshot." },
    { x: 88, y: 73, n: 4, label: "Promoted recommendation — the green published pill marks the cycle that was promoted to paper." },
    { x: 30, y: 90, n: 5, label: "Replay Detail — captured-at and data-as-of timestamps for the loaded recommendation. Scroll down for pipeline-stage snapshots." },
  ]}
  caption="The Replay page on the live workspace. The available-replays list is the entry point; click a row to load that recommendation."
/>

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
