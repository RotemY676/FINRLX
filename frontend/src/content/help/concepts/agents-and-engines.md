---
title: Agents and engines
summary: PPO, A2C, SAC, DDPG, TD3, and the ensemble — in plain English.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 3
---

An "engine" in FINRLX is a strategy that turns market state into portfolio weights. Engines fall into three families: classical optimizers (equal weight, minimum variance, risk parity), reinforcement-learning agents (PPO, A2C, SAC, DDPG, TD3), and the ensemble — which trains several RL agents in parallel and picks the best by rolling out-of-sample Sharpe.

This page explains the trade-offs between families and when each tends to win.
