# Phase W-1 — Investor Profile Schema

**Date:** 2026-05-21
**Base commit:** `ed18d07`
**Track:** Phase W (Investor Profile Wizard) — first of 8 sub-phases.

## What this sub-phase ships

Three new tables backing the investor-profile wizard, an idempotent seed
script for the question catalog, and contract tests.

| Artifact | Path |
|---|---|
| Models | `backend/app/models/profile.py` |
| Migration | `backend/migrations/versions/021_investor_profiles.py` |
| Seed script | `backend/scripts/seed_profile_questions.py` |
| Tests | `backend/tests/test_phase_w1_investor_profile_schema.py` |
| Model index update | `backend/app/models/__init__.py` |

## Schema

### `investor_profiles` — current snapshot per user

Insert-or-update semantics: one row per user. Writing a new profile
bumps `version` and writes a fresh `investor_profile_revisions` row.

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` PK | UUID |
| `user_id` | `String(36)` UNIQUE | one current profile per user |
| `version` | `Integer` | starts at 1, monotonic |
| `risk_score` | `Integer` | 8-32 (Grable-Lytton 8-item subset, each 1-4) |
| `risk_bucket` | `String(40)` | one of `RISK_BUCKETS` |
| `horizon_band` | `String(20)` | one of `HORIZON_BANDS` |
| `primary_goal` | `String(40)` | one of `PRIMARY_GOALS` |
| `max_drawdown_pct` | `Float` | upper bound enforced by Risk Overlay |
| `knowledge_level` | `String(20)` | MiFID II §1 |
| `years_investing` | `Integer` | MiFID II §1 |
| `instruments_traded_json` | `Text` | JSON list, MiFID II §1 |
| `investable_amount_band` | `String(20)` | MiFID II §2, banded only |
| `income_band` | `String(20)` | MiFID II §2, banded only |
| `liquid_net_worth_band` | `String(20)` | MiFID II §2, banded only |
| `sector_whitelist_json` | `Text` | JSON list of sector names |
| `sector_blacklist_json` | `Text` | JSON list of sector names |
| `region_preference` | `String(10)` | `us` / `eu` / `global` |
| `exclude_leverage` | `Boolean` | default true |
| `base_currency` | `String(3)` | drives Phase FX layer |
| `trading_frequency` | `String(20)` | `monthly` / `weekly` / `daily` |
| `raw_answers_json` | `Text` | full audit copy of wizard answers |
| `completed_at` | `DateTime(tz)` | when the wizard finished |
| `created_at`, `updated_at` | `DateTime(tz)` | from `TimestampMixin` |

Index: `ix_investor_profiles_user` (unique) on `user_id`.

### `investor_profile_revisions` — append-only history

Every InvestorProfile write produces a revision. Recommendations
reference `(user_id, version)` so replay can reconstruct the exact
suitability frame that drove a given recommendation.

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` PK | UUID |
| `profile_id` | `String(36)` | references investor_profiles.id |
| `user_id` | `String(36)` | denormalized for fast user-scoped lookup |
| `version` | `Integer` | matches investor_profiles.version at write time |
| `snapshot_json` | `Text` | full profile snapshot serialized |
| `change_summary` | `String(500)` nullable | human-readable diff or note |
| `created_at` | `DateTime(tz)` | |

Indexes: `ix_investor_profile_revisions_profile`, `ix_investor_profile_revisions_user`.

### `profile_questions` — canonical wizard catalog

Seeded once. Wizard frontend reads this list at runtime so question
text + choices live in a single place.

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` PK | |
| `code` | `String(40)` UNIQUE | e.g. `R_01_VOL_COMFORT` |
| `step` | `Integer` | 1-8 |
| `order_in_step` | `Integer` | display order |
| `dimension` | `String(20)` | one of `PROFILE_DIMENSIONS` |
| `text` | `Text` | the question itself |
| `helper_text` | `Text` nullable | rendered as subtitle |
| `choices_json` | `Text` | `[{value, label, score?}, ...]` |
| `is_required` | `Boolean` | default true |
| `is_active` | `Boolean` | default true |

Indexes: `ix_profile_questions_code` (unique), `ix_profile_questions_step`.

## Question catalog (seeded set)

**26 questions, 6 dimensions, 6 steps.** Steps 1 (Welcome) and 8
(Review) are UI-only with no questions.

| Step | Dimension | Items | Source |
|---|---|---|---|
| 2 | knowledge | 4 (`K_01`..`K_04`) | MiFID II §1 |
| 3 | financial | 4 (`F_01`..`F_04`) | MiFID II §2, bands only |
| 4 | risk | 8 (`R_01`..`R_08`) | Grable-Lytton 1999 (8-item subset, each 1-4) |
| 5 | objectives | 3 (`O_01`..`O_03`) | MiFID II §3 |
| 6 | universe | 4 (`U_01`..`U_04`) | sector/region/leverage |
| 7 | operational | 3 (`P_01`..`P_03`) | currency / frequency / notifications |

## Methodology rationale

* **8-item Grable-Lytton subset**: chosen for highest discriminating
  power per the 2014 retrospective (Cronbach α 0.77, n>1M profiles
  generated via the original 13-item scale across 20+ countries).
* **MiFID II three-dimension frame**: knowledge & experience, financial
  situation, investment objectives (ESMA 35-43-3172, Sept 2022).
* **Banded financial data**: stored as enums (`lt_10k`, `50k_250k`, etc.)
  rather than precise figures, to minimize PII surface.
* **Sector preferences feed Universe filters**: at recommendation time,
  the pipeline reads `sector_whitelist_json` / `sector_blacklist_json`
  and prunes UniverseMembership accordingly (wired in W-5).

## Storage choices

* JSON columns are `Text`, not `JSONB`, for SQLite-in-tests + Postgres-in-prod
  parity (same pattern as `saved_views.filters_json`).
* `user_id` is a loose `String(36)` (no FK), matching every other table
  in the codebase. Tenant boundary is enforced at the API layer via
  `get_current_user`, not at the DB layer.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest | **775 passed, 2 skipped** (was 768 before W-1; 7 new tests added) |
| Backend ruff | clean across `app/` |
| Backend mypy | clean on `app/core/` |
| Alembic upgrade head | OK against fresh SQLite + asyncpg URL pattern |
| Alembic downgrade `021 → 020` | OK |
| Alembic re-upgrade `020 → 021` | OK |

## Follow-ups documented for W-2 and beyond

* W-2: `POST /api/v1/profile`, `GET /api/v1/profile/me`, scoring service
  reads the seeded `profile_questions` to compute `risk_score` and the
  derived `risk_bucket`.
* W-2 also reads `choices_json[].score` for step-4 items only; other
  dimensions are stored as raw enum values in `raw_answers_json`.
* W-4: deterministic mapping from `(risk_bucket, horizon_band)` to a
  target equity / defensive split (Vanguard/Fidelity model-portfolio
  tables).
* W-5: pipeline patch to read the active `InvestorProfile` per user and
  apply: universe filtering (sector lists, region), max-DD constraint
  (Risk Overlay), trading cadence (timing engine).
* W-5 + project-local `recommendation-object-provenance` skill:
  embed `(profile_id, profile_version)` in every Recommendation so
  replay can reconstruct the exact suitability frame.

## Honest limitations

* This sub-phase ships **schema + seed + tests only** — no API, no UI.
  An external observer would see no behavior change.
* The `RISK_BUCKETS` and other tuples are read at module import; if you
  rename one, both the model and any migration that reads it must be
  updated together. We do not expose them as DB enum types because that
  would lock SQLite tests.
* The seed script is idempotent **per `code`**; if you edit a question's
  `text` after seeding, you must re-run with a script tweak (delete by
  code then re-insert) or update by raw SQL — this is intentional, to
  protect the audit trail in `raw_answers_json` from text drift.

## Sources

* [Grable & Lytton 1999 — original 13-item scale](https://openjournals.libs.uga.edu/fsr/article/view/3240)
* [ESMA MiFID II suitability guidelines (Sept 2022)](https://www.esma.europa.eu/sites/default/files/2023-04/ESMA35-43-3172_Guidelines_on_certain_aspects_of_the_MiFID_II_suitability_requirements.pdf)
* [Morningstar/FinaMetrica risk-tolerance mapping](https://help.adviserlogic.com/en/articles/10584886-morningstar-risk-profiling-powered-by-finametrica)
* [Vanguard — model portfolio allocations](https://investor.vanguard.com/investor-resources-education/education/model-portfolio-allocation)
