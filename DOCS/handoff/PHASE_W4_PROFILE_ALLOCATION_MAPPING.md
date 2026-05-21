# Phase W-4 — Profile → Allocation Mapping

**Date:** 2026-05-21
**Base commit:** `2c576ff` (W-3)
**Track:** Phase W — sub-phase 4 of 8.

## What this sub-phase ships

A deterministic, pure-Python lookup table that turns
`(risk_bucket, horizon)` from a saved investor profile into an
allocation target the pipeline can use. Plus 37 contract tests that
pin every cell of the published table, monotonicity, caps, and error
behavior.

| Artifact | Path |
|---|---|
| Pure mapping module | `backend/app/services/profile_mapping.py` |
| Contract tests (37) | `backend/tests/test_phase_w4_profile_mapping.py` |

## Mapping

`derive_allocation(bucket, horizon) -> AllocationTargets`

| | lt_1y | 1y_3y | 3y_5y | 5y_10y | gt_10y |
|---|---|---|---|---|---|
| Conservative | 15 | 20 | 25 | 30 | 35 |
| Moderate-Conservative | 30 | 35 | 40 | 45 | 50 |
| Moderate | 45 | 50 | 55 | 60 | 65 |
| Moderate-Aggressive | 60 | 65 | 70 | 75 | 80 |
| Aggressive | 75 | 80 | 85 | 90 | 95 |

(values are **equity %**; defensive = `100 - equity`)

`lt_1y` is computed as `1y_3y − 5pp`, floored at 10%. Floor never
activates in the current table; we keep it so a future bucket adjust
can't accidentally go negative.

## Per-bucket caps

| Bucket | max_position_pct | max_concentration_pct (top-5) | confidence_cap |
|---|---|---|---|
| Conservative | 6.0 | 25.0 | 0.70 |
| Moderate-Conservative | 8.0 | 30.0 | 0.75 |
| Moderate | 10.0 | 35.0 | 0.80 |
| Moderate-Aggressive | 14.0 | 40.0 | 0.85 |
| Aggressive | 18.0 | 50.0 | 0.90 |

All three caps grow monotonically with bucket aggressiveness. The
`confidence_cap` is read by the Risk Overlay (W-5 will wire) so a
Conservative profile never sees a 0.99-confidence rec; it's clipped
to 0.70.

## Invariants enforced by tests

1. **Pinned table:** every (bucket, horizon) → equity_pct is asserted
   verbatim. Any silent shift breaks the suite.
2. **Equity monotonic in bucket** at every horizon (more aggressive ≥
   less aggressive).
3. **Equity monotonic in horizon** within every bucket (longer ≥ shorter).
4. **Equity + defensive = 100.0** exactly.
5. **Per-bucket caps pinned** at every bucket.
6. **Caps monotonic** across buckets.
7. **`lt_1y` floor** ≥ 10.
8. **Unknown bucket / horizon** raises `AllocationMappingError`.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (W-4 file) | **37 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |

## Follow-ups

* **W-5** consumes `derive_allocation` inside the recommendation
  pipeline. The Risk Overlay applies `max_position_pct` and
  `confidence_cap`; the Allocation stage applies the equity/defensive
  split.
* **TPL** templates (Capital Preservation, Balanced, etc.) are
  effectively a (bucket, horizon, sector_tilt) triple — they'll wrap
  this function plus a template-specific sector overlay.
* When we add a Treasury / cash adapter, the "defensive %" sleeve gets
  filled with real instruments. Until then, defensive sits as a
  reserve in the paper portfolio.

## Honest limitations

* The mapping is **time-invariant**: it doesn't react to regime. A
  bear-market-aware adaptation lives further down the roadmap (Phase B1
  Risk workspace exposes the breach hooks; W-5 only consumes the
  static targets here).
* The cap numbers were chosen by triangulating Vanguard, Fidelity, and
  RBC Direct Investing model-portfolio documents. They are not
  regulator-derived; they're the most common breakpoints in published
  advisor portfolios. A user with a vetted IPS can override via TPL.

## Sources

* [Vanguard model-portfolio allocations](https://investor.vanguard.com/investor-resources-education/education/model-portfolio-allocation)
* [Fidelity Institutional — target-risk model portfolios](https://institutional.fidelity.com/advisors/investment-solutions/model-portfolios/explore-models/target-risk-models)
* [RBC Direct Investing — asset allocation models](https://www.rbcdirectinvesting.com/learn/en/di/reference/article/model-portfolios-test/jlxqhhtp)
