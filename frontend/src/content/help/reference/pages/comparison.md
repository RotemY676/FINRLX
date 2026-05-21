---
title: Engine comparison
summary: Side-by-side allocation, alignment scatter, position-level diff.
diataxis: reference
area: reference
updated: 2026-05-22
order: 103
---

The Comparison page puts multiple engines next to each other for the same universe and the same time window.

## Sections

### Engine matrix

Add or remove engines from the comparison via the toolbar. Each column is an engine; each row is a metric (Sharpe, Sortino, Calmar, drawdown, turnover). See [Metrics](/help/reference/metrics) for definitions.

### Engine alignment

A scatter plot in which each point is a position and the axes are two engines' recommended weights. Points on the diagonal mean both engines agree. Scattered points mean disagreement — usually a sign of regime uncertainty. See [Agents and engines](/help/concepts/agents-and-engines).

### Weight comparison

Per-position bar chart: the recommended weights from the selected engine vs. an equal-weight benchmark. The benchmark is configurable via the toolbar.

### Position detail

When you click a point in alignment or a bar in weight comparison, this panel renders the per-position evidence: the engine's signal at that position, the alignment with other engines, and the engine's prior cycle for delta.

### Recommendation rationale

A structured summary of *why* the engines differ where they differ.

## See also

- [Compare engines](/help/guides/compare-engines) — the how-to.
- [Agents and engines](/help/concepts/agents-and-engines) — the concept.
