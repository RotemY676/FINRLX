---
title: Known pitfalls
summary: Overfitting, leakage, survivorship — the failure modes the team has seen most.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 8
---

The dominant failure mode of any ML-driven trading system is backtest overfitting — a model that memorizes the training window instead of learning a generalizable policy. Data leakage and survivorship bias are close behind. Underestimating transaction cost and slippage can flip a profitable agent into a loss-making one. Reward hacking is real.

This page enumerates the specific pitfalls FINRLX defends against, where the defenses live in the product, and what residual risk you should still inspect manually.
