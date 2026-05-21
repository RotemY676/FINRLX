---
title: Risk
summary: Exposure and Concentration panels — what they measure and how to read them.
diataxis: reference
area: reference
updated: 2026-05-22
order: 107
---

The Risk page is two panels covering portfolio-level risk attributes.

## Sections

### Exposure

Per-name and per-sector exposure compared to the configured caps. Each bar shows current weight against the [EXPOSURE_SINGLE](/help/reference/policy-controls#exposure_single) or [EXPOSURE_SECTOR](/help/reference/policy-controls#exposure_sector) cap. Bars at exactly the cap are *binding* — the overlay is preventing the engine from going further.

### Concentration

Two Herfindahl-style measures of how concentrated the portfolio is — single-name HHI and sector HHI. Lower numbers indicate more diversified portfolios. Useful for tracking concentration drift across time.

## When to look at this page

- After every promotion to confirm the paper portfolio matches expectations.
- When investigating an [exposure-cap breach](/help/reference/pages/policies) — this is where you confirm what was binding.
- Periodically as part of a portfolio review — concentration drifts slowly and can compound.

## See also

- [Policy controls](/help/reference/policy-controls) — the caps that show up here.
- [Risk overlays](/help/concepts/risk-overlays) — the layer that enforces them.
