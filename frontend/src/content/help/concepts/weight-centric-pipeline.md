---
title: The weight-centric pipeline
summary: Why FINRLX treats portfolio-weight vectors as the universal contract between every layer.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 1
---

FINRLX is built around a single design choice: the portfolio-weight vector is the only thing that crosses the boundary between strategy logic and execution. An equal-weight allocator, a classical mean-variance optimizer, and a reinforcement-learning agent all produce the same shape of output — a sum-to-one allocation across assets — and the same weights flow identically through backtesting and live execution.

This concept page explains what that means in practice, why it matters for reproducibility, and what trade-offs it implies.
