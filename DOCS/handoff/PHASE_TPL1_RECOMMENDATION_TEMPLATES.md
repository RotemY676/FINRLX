# Phase TPL-1 — Recommendation Templates Schema + 5 Seed Templates

**Date:** 2026-05-21
**Base commit:** `1eef868` (W-8 / Phase W close)
**Track:** Phase TPL — sub-phase 1 of 4.

## What this sub-phase ships

A `recommendation_templates` table backed by an idempotent seed script
loading 5 pre-made templates derived from Vanguard / Fidelity model
portfolios.

| Artifact | Path |
|---|---|
| Model | `backend/app/models/recommendation_template.py` |
| Migration `022_rec_templates` | `backend/migrations/versions/022_recommendation_templates.py` |
| Seed script | `backend/scripts/seed_recommendation_templates.py` |
| Contract tests (7) | `backend/tests/test_phase_tpl1_templates_schema.py` |
| Model index update | `backend/app/models/__init__.py` |

## Schema

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` PK | UUID |
| `key` | `String(60)` UNIQUE | slug for URL / API addressing |
| `name` | `String(120)` | display name |
| `description` | `Text` | one-sentence summary |
| `badge` | `String(40)` | bucket label for the card chip |
| `risk_bucket`, `horizon_band`, `primary_goal`, `max_drawdown_pct` | InvestorProfile-shaped | drives W-4 mapping |
| `sector_whitelist_json` / `sector_blacklist_json` | `Text` (JSON) | sector tilt |
| `exclude_leverage`, `base_currency`, `trading_frequency`, `region_preference` | InvestorProfile-shaped | |
| `is_seed` | `Boolean` | true for shipped seeds, false for user-authored |
| `is_active` | `Boolean` | hide-without-delete |
| `created_by_user_id` | `String(36)` nullable | for TPL-4 |
| `allocation_summary` | `String(40)` nullable | "60/40" label for cards |
| `last_evaluated_at` | `DateTime(tz)` nullable | TPL-2 will fill this when a backtest is computed |

`ix_recommendation_templates_key` (unique).

## 5 seed templates (per locked decisions)

| Key | Name | Bucket | Horizon | Max DD | Allocation | Sector tilt |
|---|---|---|---|---|---|---|
| `capital_preservation` | Capital Preservation | conservative | 1y_3y | 5% | 20/80 | — |
| `balanced_growth` | Balanced Growth | moderate | 3y_5y | 15% | 55/45 | — |
| `long_term_growth` | Long-Term Growth | moderate_aggressive | 5y_10y | 25% | 75/25 | — |
| `tech_growth` | Tech Growth | aggressive | 5y_10y | 40% | 90/10 | Technology |
| `income_focus` | Income Focus | moderate_conservative | 3y_5y | 15% | 40/60 | Financials + Utilities |

All seeds use USD as base currency. `tech_growth` uses weekly cadence;
the others are monthly. `exclude_leverage=true` everywhere.

`allocation_summary` is computed from `derive_allocation(bucket, horizon)`
(Phase W-4) so the cards on `/templates` (TPL-3) can render a human label
without a runtime lookup.

## Invariants tested

1. Table accepts writes; non-seed (`is_seed=False`) records survive.
2. `key` UNIQUE — duplicates raise `IntegrityError`.
3. Seed script idempotent: re-running inserts 0, skips 5.
4. All 5 expected keys exist after seeding.
5. Every seed's (`risk_bucket`, `horizon_band`) is a valid W-4 input —
   we never ship a template that crashes the pipeline.
6. Every seed's stored `allocation_summary` matches what W-4 produces
   for the same inputs (drift guard).
7. `tech_growth` whitelist contains "Technology"; `income_focus`
   whitelist contains both dividend sectors.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (TPL-1 file) | **7 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |
| Alembic upgrade head | OK |
| Alembic downgrade `022 → 021` | OK |
| Alembic re-upgrade `021 → 022` | OK |

## Follow-ups

* **TPL-2** runs a hermetic backtest per seed template and stores a
  short performance summary (CAGR / max DD / Sharpe) on the row. The
  summary surfaces on the `/templates` cards in TPL-3.
* **TPL-3** ships the `/templates` page with the 5 seed cards and an
  "Apply to my profile" action that hands the user off to `/profile`
  edit mode pre-filled from the chosen template.
* **TPL-4** opens a small admin surface (CRUD on user-authored
  templates). Initially gated by the existing admin role check.

## Honest limitations

* This sub-phase ships **schema + seed only** — no API, no UI. An
  external observer would see no change at the live URLs until TPL-3.
* Templates are stored as full snapshots — if W-1 ever renames a band
  or bucket, every template row needs a migration. We accept this
  because templates are user-facing artifacts and a silent rename
  would lie to the user about their "Aggressive" tilt anyway.
* `allocation_summary` is computed at seed time. If you change the W-4
  table in a future sub-phase, you must re-run the seed (or run an
  ad-hoc UPDATE) to bring summaries back in sync. The contract test
  above will fail loudly if drift sneaks in.

## Sources

* [Vanguard model-portfolio allocations](https://investor.vanguard.com/investor-resources-education/education/model-portfolio-allocation)
* [Fidelity Institutional — target-risk model portfolios](https://institutional.fidelity.com/advisors/investment-solutions/model-portfolios/explore-models/target-risk-models)
* [Morningstar — risk-tolerance mapping](https://help.adviserlogic.com/en/articles/10584886-morningstar-risk-profiling-powered-by-finametrica)
