---
title: Risk overlays
summary: Constraints, breaches, floors — the guardrails that sit on top of every recommendation.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 5
---

A risk overlay is a hard constraint applied after an engine produces weights but before a recommendation is published. Overlays enforce things like maximum single-name exposure, sector concentration limits, a cash floor, and confidence floors on data, model, and operational health.

When an overlay would be violated, the recommendation is either re-projected onto the feasible set or flagged as a **breach**. This page explains the overlay catalogue, how breaches surface, and how to investigate them.
