---
title: Metrics
summary: Sharpe, Sortino, Calmar, max drawdown, turnover — formulas and gotchas.
diataxis: reference
area: reference
updated: 2026-05-22
order: 3
---

FINRLX reports a small, opinionated set of performance metrics. Each metric tries to capture one specific risk-adjusted attribute of a strategy: Sharpe penalizes all volatility, Sortino only the downside, Calmar weighs return against the worst drawdown.

This reference defines each metric, gives the formula, and flags the most common ways readers misinterpret it.
