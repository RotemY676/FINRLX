---
title: Replay a decision
summary: Reconstruct any past recommendation exactly as it was at decision time.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 7
---

The [Replay page](/help/reference/pages/replay) lets you pick a past recommendation and step through it: the rationale at the snapshot, the positions it implied, the pipeline-stage snapshots that produced it. Use it for post-trade review, audit, or debugging an unexpected outcome.

## Steps

1. **Open Replay.** Sidebar → WORKSPACES → Replay & forensics.
2. **Find the recommendation** by ID, date, or status filter.
3. **Click the row** to load the replay.
4. **Read the rationale at snapshot.** This is the evidence narrative *as it would have read* at decision time, not as it reads now.
5. **Open the pipeline-stage snapshots.** Four collapsible panels show the state at each pipeline stage: data, features, engine output (raw weights), overlay output (published weights).
6. **Inspect the overlay panel.** If any constraint fired during the original run, this is where you see the engine's raw output, the projected output, and the constraint that fired.

## What replay can answer

- "What did the engine see when it made this decision?" → the data and features panels.
- "What did the engine actually want?" → the engine-output panel (pre-overlay).
- "Why was the published weight different?" → the overlay-output panel.
- "What policy was in force?" → the replay detail at the top of the page.

## Forensic patterns

### A recommendation looks wrong

Replay it. If the engine output panel shows weights that match the published weights, the engine "owned" the call. If the engine output and published weights differ, the overlay shaped it — and the overlay panel shows which constraint.

### A breach won't clear

Replay the recommendation it fired on. The pipeline-stage panels show what was true at the moment of the breach — usually a stale feed or an unusual cross-section. Resolution path: [investigate a breach](/help/guides/investigate-a-breach).

### Engine drift suspected

Replay an old recommendation against the *current* engine version using the **Re-derive with current engine** action. The diff shows what the new engine would have done differently.

## See also

- [Replay page](/help/reference/pages/replay) — the page reference.
- [Governance and audit](/help/concepts/governance-and-audit) — the determinism guarantees.
