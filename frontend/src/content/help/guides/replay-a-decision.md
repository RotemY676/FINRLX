---
title: Replay a decision
summary: Reconstruct any past recommendation exactly as it was at decision time.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 7
---

The **Replay** screen lets you pick a past recommendation and step through it: the rationale at the snapshot, the positions it implied, the pipeline-stage snapshots that produced it. This is the standard tool for post-trade review, audit, and debugging an unexpected outcome.

Replay is read-only by design — you can copy weights, export evidence, or fork into a new backtest, but you cannot mutate the historical record.
