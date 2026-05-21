# Phase W-2 — Investor Profile API + Scoring Service

**Date:** 2026-05-21
**Base commit:** `48bfe2c` (W-1)
**Track:** Phase W (Investor Profile Wizard) — sub-phase 2 of 8.

## What this sub-phase ships

A REST API + scoring service over the W-1 schema. The wizard frontend
(W-3) can now post answers and read the resulting profile.

| Artifact | Path |
|---|---|
| Pure scoring + persistence service | `backend/app/services/profile.py` |
| Pydantic request/response schemas | `backend/app/schemas/profile.py` |
| API endpoints | `backend/app/api/v1/profile.py` |
| Router registration | `backend/app/api/router.py` |
| Contract tests | `backend/tests/test_phase_w2_profile_api.py` |

## Endpoints

All require auth via `get_current_user`. Profile data is strictly
per-tenant — there is no admin / cross-user surface.

| Method | Path | Returns | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/profile/questions` | `ApiResponse[list[ProfileStep]]` | Step-grouped catalog the wizard renders |
| `GET` | `/api/v1/profile/me` | `ApiResponse[ProfileMeResponse]` | `{has_profile, profile?}` |
| `POST` | `/api/v1/profile` | `ApiResponse[InvestorProfile]` (201) | Submit wizard answers; computes risk_score+bucket; upserts; appends revision |
| `GET` | `/api/v1/profile/revisions/me` | `ApiResponse[list[ProfileRevision]]` | Append-only revision history, newest first |

### Submission shape

```jsonc
POST /api/v1/profile
{
  "answers": {
    "K_01_LEVEL": "intermediate",
    "K_02_YEARS": "3",
    "K_03_INSTRUMENTS": ["equities", "etfs"],
    "R_01_VOL_COMFORT": "3",
    "R_02_LOSS_REACTION": "3",
    "...": "...",  // all R_01..R_08 required
    "O_01_HORIZON": "3y_5y",
    "P_01_CURRENCY": "USD"
  },
  "change_summary": "first save"  // optional, <=500 chars
}
```

Validation errors return `422` with the offending field code in `detail`.

## Scoring algorithm

`score_answers(answers, risk_question_choices) -> ScoredProfile`

1. For each step-4 question (`R_*`), look up the chosen value's `score`
   in its `choices_json` and sum → `risk_score` (8-32).
2. `bucket_from_score(risk_score)` → one of:
   - `8-12` conservative
   - `13-17` moderate_conservative
   - `18-22` moderate
   - `23-27` moderate_aggressive
   - `28-32` aggressive
3. Validate every enum (`horizon_band`, `primary_goal`, `region_preference`,
   `base_currency`, `trading_frequency`, knowledge level, bands) against
   the constants in `app/models/profile.py`.
4. Cast numeric answers (`K_02_YEARS`, `O_03_MAX_DD`) and check bounds.

The scoring function is **pure**: it never touches the database. The
`ProfileService.upsert` then writes the new profile row (or updates
the existing one in place) and appends a revision in a single
transaction.

## Bucket-threshold rationale

Vanguard's published model portfolios use 5 risk levels. Fidelity's
target-risk model portfolios use the same band structure (Conservative,
Moderately Conservative, Balanced, Moderately Aggressive, Aggressive),
each with a clean break of ~20% growth-asset weighting between bands.

Mapping the 8-32 Grable-Lytton subset to 5 equal-width bands (5 points
each) preserves that boundary spacing and lines up cleanly with W-4's
upcoming risk→allocation table.

## Tenant boundary

* Every endpoint takes `user: User = Depends(get_current_user)` and
  scopes all reads/writes to `user.id`.
* The `investor_profiles.user_id` UNIQUE constraint guarantees one
  current profile per user; the upsert mutates the existing row.
* Revisions remain append-only, keyed by `(profile_id, version)`.
* The W-2 test suite includes a positive cross-user test: user B reads
  `/profile/me` after user A has submitted, must see `has_profile=false`.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (W-2 file) | **13 passed** (boundary, pure scoring, full API matrix) |
| Backend pytest (full) | **788 passed, 2 skipped** (was 775 after W-1; +13 new) |
| Backend ruff | clean across `app/` |
| Backend mypy | clean on `app/core/` |
| Alembic head | unchanged from W-1 (no schema change in W-2) |

## Follow-ups for W-3 and beyond

* **W-3 frontend wizard** consumes `/profile/questions` to render
  every step from server-side data. No question text lives in the
  frontend.
* **W-3** submits to `POST /profile` and on 201 routes to `/decision`
  (first recommendation page).
* **W-5 pipeline integration** will read `ProfileService.get_current(user_id)`
  during recommendation generation and apply the user's sector
  filters / region / max-DD constraint.
* **W-5 also reads** `instruments_traded` to gate the surfacing of
  derivatives / leverage instruments in the universe.
* The seeded catalog covers steps 2-7. Steps 1 (Welcome) and 8 (Review)
  are pure UI in W-3 — no DB rows needed.

## Honest limitations

* **No frontend yet.** Until W-3 lands, the only client is the test
  suite. An external observer testing the live API by hand would need
  to seed `profile_questions` first (run
  `python -m scripts.seed_profile_questions` after `alembic upgrade head`).
* **No drift detection.** If you change the `text` of a seeded question
  after a user has saved a profile, the historical `raw_answers_json`
  in their revision rows still points to the old `code`. The text drift
  is invisible to the audit trail by design — we only audit choices,
  not question prose.
* **No idempotency keys on `POST /profile`.** Two rapid identical
  submits create two version bumps. The wizard frontend (W-3) is
  expected to disable the submit button while awaiting the response.

## Sources

* [Grable & Lytton 1999 — original 13-item scale, 8-32 distilled range](https://openjournals.libs.uga.edu/fsr/article/view/3240)
* [Vanguard — model portfolio allocations](https://investor.vanguard.com/investor-resources-education/education/model-portfolio-allocation)
* [Fidelity Institutional — target-risk model portfolios](https://institutional.fidelity.com/advisors/investment-solutions/model-portfolios/explore-models/target-risk-models)
* [Morningstar/FinaMetrica risk→growth mapping](https://help.adviserlogic.com/en/articles/10584886-morningstar-risk-profiling-powered-by-finametrica)
