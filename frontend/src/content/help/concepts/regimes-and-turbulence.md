---
title: Regimes and turbulence
summary: How FINRLX detects market state shifts and de-risks when the world looks different.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 4
---

Markets are non-stationary — the data-generating process changes over time. A model trained in a steady-growth regime will drift when volatility regimes flip. FINRLX uses two mechanisms to handle this: a regime detector that classifies the current state (risk-on, risk-off, late-cycle, etc.), and a turbulence index — a Mahalanobis-distance measure of extreme price moves that throttles new positions when it crosses a threshold.

This page explains both and how they shape the recommendations you see.
