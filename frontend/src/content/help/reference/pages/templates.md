---
title: Templates
summary: Seed templates that bundle a universe, an engine, and a default policy set.
diataxis: reference
area: reference
updated: 2026-05-22
order: 115
---

A **template** bundles a universe, an engine, and a default set of [policy controls](/help/reference/policy-controls) so you can stand up a new decision flow with one click. FINRLX ships five seed templates covering common configurations.

## Seed templates

### US Large Cap · Ensemble · Balanced

Universe: top 100 US large-cap names with point-in-time membership.
Engine: ensemble of PPO + A2C + DDPG with quarterly rolling retraining.
Policy: balanced — 5% cash floor, 10% single-name cap, 40% sector cap.

### US Large Cap · PPO · Conservative

Universe: same as above.
Engine: PPO with monthly retraining.
Policy: conservative — 15% cash floor, 8% single-name cap, 30% sector cap.

### Diversified Global · Risk Parity · Conservative

Universe: multi-region ETF basket.
Engine: classical risk-parity.
Policy: conservative.

### Sector Rotation · PPO · Balanced

Universe: top-10 sector ETFs.
Engine: PPO trained on the sector universe with weekly retraining.
Policy: balanced.

### Crypto Majors · SAC · Aggressive

Universe: BTC, ETH, and the top-3 major altcoins.
Engine: SAC with daily retraining.
Policy: aggressive — 0% cash floor, 25% single-name cap.

## Using a template

Pick a template from the list, click **Use template**, and the workspace clones the template's universe, engine configuration, and policy bundle into a new decision flow under your account. You can then customize any of the components without affecting the seed template.

## See also

- [Universe and features](/help/concepts/universe-and-features) — what's in the universe.
- [Agents and engines](/help/concepts/agents-and-engines) — what the engine choice implies.
- [Policy controls](/help/reference/policy-controls) — the default policy.
