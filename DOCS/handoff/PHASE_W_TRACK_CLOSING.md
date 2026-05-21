# Phase W — Track Closing

**Date:** 2026-05-21
**Final commit:** to be set after W-8 commit + push
**Track:** Phase W (Investor Profile Wizard) — 8 of 8 sub-phases complete.

## Sub-phase ledger

| Sub | Title | Commit | Tests added | Doc |
|---|---|---|---|---|
| W-1 | Schema + seeded question catalog | `48bfe2c` | 7 backend | `PHASE_W1_INVESTOR_PROFILE_SCHEMA.md` |
| W-2 | Scoring service + 4 REST endpoints | `307a948` | 13 backend | `PHASE_W2_PROFILE_API.md` |
| W-3 | 8-step wizard frontend | `2c576ff` | 6 vitest + 3 e2e | `PHASE_W3_WIZARD_FRONTEND.md` |
| W-4 | Risk × horizon → allocation mapping | `9b906c4` | 37 backend | `PHASE_W4_PROFILE_ALLOCATION_MAPPING.md` |
| W-5 | Profile → pipeline integration | `005c512` | 14 backend | `PHASE_W5_PROFILE_PIPELINE.md` |
| W-6 | A11y + mobile axe sweep | `1df73ec` | 3 e2e | `PHASE_W6_WIZARD_A11Y_MOBILE.md` |
| W-7 | /profile view+edit + run-pipeline trigger | `48fdb36` | 3 backend | `PHASE_W7_PROFILE_PAGE.md` |
| W-8 | Full E2E lifecycle | this commit | 2 backend | `PHASE_W8_PROFILE_E2E.md` |

**Total new tests across Phase W:** ~76 backend + 6 vitest + 6 Playwright = **~88 new tests.**

## End-state surfaces

### Backend (5 endpoints)
| Method | Path | Phase |
|---|---|---|
| GET | `/api/v1/profile/questions` | W-2 |
| GET | `/api/v1/profile/me` | W-2 (raw_answers added in W-7) |
| POST | `/api/v1/profile` | W-2 (upsert + revision) |
| GET | `/api/v1/profile/revisions/me` | W-2 |
| POST | `/api/v1/profile/run-pipeline` | W-7 |

### Backend (3 tables)
* `investor_profiles` — one current row per user
* `investor_profile_revisions` — append-only audit
* `profile_questions` — seeded catalog (26 items, 6 dimensions)

### Backend (4 services)
* `app.services.profile.ProfileService` — persistence + scoring orchestration
* `app.services.profile.score_answers` — pure scoring function
* `app.services.profile_mapping.derive_allocation` — risk×horizon → targets
* `app.services.profile_pipeline_overrides.load_overrides_for_user` — pipeline bridge

### Frontend (2 routes + 5 components)
* `/onboarding` — 8-step wizard
* `/profile` — view + edit + run trigger
* `features/wizard/{WizardLayout, QuestionField, ReviewStep, types, api}`

## End-state gate snapshot

| Gate | Pre-Phase-W (commit `ed18d07`) | Post-Phase-W |
|---|---|---|
| Backend pytest | 747 / 2 skipped / 0 failed | **844 / 2 skipped / 0 failed** (+97) |
| Frontend vitest | 21 | **27** (+6) |
| Playwright chromium | 28 | **31** (+3) |
| Frontend tsc | clean | clean |
| Backend ruff | clean | clean |
| Backend mypy on `app/core/` | clean | clean |
| Next build routes | 21 | 22 (+1 `/profile`) |

## Methodology sources actually consumed

* [Grable & Lytton 1999 — 13-item scale](https://openjournals.libs.uga.edu/fsr/article/view/3240) — risk-tolerance items (W-1 used 8-item subset)
* [ESMA MiFID II suitability guidelines (Sept 2022)](https://www.esma.europa.eu/sites/default/files/2023-04/ESMA35-43-3172_Guidelines_on_certain_aspects_of_the_MiFID_II_suitability_requirements.pdf) — three-dimension frame (W-1)
* [Vanguard model-portfolio allocations](https://investor.vanguard.com/investor-resources-education/education/model-portfolio-allocation) — equity table (W-4)
* [Fidelity Institutional — target-risk model portfolios](https://institutional.fidelity.com/advisors/investment-solutions/model-portfolios/explore-models/target-risk-models) — equity table cross-check (W-4)
* [Morningstar/FinaMetrica risk→growth mapping](https://help.adviserlogic.com/en/articles/10584886-morningstar-risk-profiling-powered-by-finametrica) — bucket boundaries (W-2/W-4)

## Honest "what's still incomplete"

These are intentional limitations carried forward into the next phases:

* **No real-data pipeline trigger from the wizard.** `POST /profile/run-pipeline`
  runs the pipeline in-process against whatever signals exist. There is no
  scheduler yet, so it depends on `/api/v1/engines/run` having been triggered
  recently. → **OP-2** adds the scheduler.
* **No multi-currency P&L.** The wizard captures `base_currency`, the pipeline
  honors it for confidence/cap purposes, but the paper portfolio still values
  positions in USD. → **FX-2** adds `PaperPortfolio.base_currency` + FX translation.
* **No template library.** Five seed templates live only in the plan. →
  **TPL-1..TPL-4**.
* **No region filter applied.** The profile carries `region_preference` and
  the overrides struct exposes it, but the universe filter only acts on
  `sector`. Adding a region filter is trivial once we have non-US assets.
* **No live deploy verified.** The handoff explicitly notes this is the
  unblocking step for the beta. → **OP-1** (user-gated).

## Continuation order

Per the locked roadmap in `project_post_mvp_roadmap.md` and
`project_phase_w_tpl_fx_op_decisions.md`:

  **TPL → FX → OP-1 → OP-2..5 → BETA**

Phase W is closed. Phase TPL (template library) begins next.
