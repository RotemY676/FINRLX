# Phase W-7 — /profile View + Edit + Profile-Aware Pipeline Trigger

**Date:** 2026-05-21
**Base commit:** `1df73ec` (W-6)
**Track:** Phase W — sub-phase 7 of 8.

## What this sub-phase ships

A `/profile` page (view + edit modes) and a backend endpoint that runs
a profile-aware recommendation pipeline for the current user. With this
sub-phase, a beta tester can complete the wizard, see their saved
profile, tweak it, and trigger a recommendation that honors it.

| Artifact | Path |
|---|---|
| Profile view + edit page | `frontend/src/app/profile/page.tsx` |
| New API endpoint | `backend/app/api/v1/profile.py` (`POST /profile/run-pipeline`) |
| raw_answers exposed on `/profile/me` | `backend/app/schemas/profile.py`, `backend/app/api/v1/profile.py` |
| FE API helper | `frontend/src/features/wizard/api.ts` (`runProfileAwarePipeline`) |
| Profile type extension | `frontend/src/features/wizard/types.ts` (`raw_answers?: AnswerMap`) |
| Tests | `backend/tests/test_phase_w7_profile_edit_and_run.py` |

## API additions

### `GET /api/v1/profile/me` — now returns `raw_answers`

Backwards-compatible: the field is optional in the schema. Existing
clients (W-2 tests, W-3 wizard) keep working. New clients (W-7 edit
page) read it to pre-fill the wizard.

### `POST /api/v1/profile/run-pipeline`

* Auth: requires `get_current_user`.
* Body: empty.
* Behavior: loads the user's active `InvestorProfile`, translates it to
  `ProfileOverrides` via `load_overrides_for_user`, calls
  `DecisionPipelineService.run_pipeline(profile_overrides=overrides)`.
* Returns: standard `ApiResponse[dict]` envelope where `data` is the
  pipeline-run summary `{status, recommendation_id, stages, warnings, message}`.
* Errors:
  - `400 no_profile` if the user hasn't completed the wizard.
  - `200` with `status='failed'` if the pipeline is missing engine
    signals or universe — same semantics as the existing
    `/api/v1/pipeline/run` endpoint.

## Frontend page

### View mode
* Risk-bucket card (accent border) with score, max drawdown, horizon.
* Definition list of: primary goal, region, base currency, cadence,
  leverage policy, sector lists, knowledge level, years investing.
* Two buttons: **Edit profile** (switches to edit mode) and
  **Run a profile-aware recommendation** (calls the new endpoint;
  shows result in an `aria-live=polite` note).

### Edit mode
* Reuses the W-3 components (`WizardLayout` + `QuestionField` + `ReviewStep`).
* Loads catalog on first switch to edit, pre-fills `answers` from
  `profile.raw_answers`.
* Submit calls the same `POST /api/v1/profile` (upsert; W-2 service
  bumps `version` and appends a revision row).
* On success: returns to view mode with the updated profile cached.

### Routing
* No profile → redirects to `/onboarding` (the wizard).
* Has profile but on `/onboarding` (per W-3) → redirects to `/decision`.
* These two redirects together create a single source of truth for
  "did the user complete the wizard?".

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (W-7 file) | **3 passed** (raw_answers pre-fill, run-pipeline 400 without profile, run-pipeline 200 with) |
| Backend pytest (W-2 regression) | **13 passed** (still green; raw_answers field is optional) |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |
| Frontend tsc | clean |
| Frontend vitest | 27 (unchanged) |
| Frontend next build | 22 routes; `/profile` 2.84 kB; `/onboarding` deduped to 1.97 kB |
| Playwright (wizard subset) | 4 passed (3 viewports + base) |

## Follow-ups

* **W-8** end-to-end Playwright spec: signup → wizard → /profile shows
  the saved profile → click "Run a profile-aware recommendation" →
  assert success. This is the last sub-phase of Phase W.
* **TPL-3** "Apply template to my profile" reuses the `/profile`
  edit flow: clicking apply navigates to `/profile?from=template:<id>`
  with the template's `answers` pre-filled.
* **Nav link to /profile.** Currently the user reaches the page by URL
  only. A sidebar entry can be added in a separate small commit; out of
  scope for W-7 to keep the change small.

## Honest limitations

* No "view revision history" panel yet. The W-2 endpoint
  `/profile/revisions/me` returns the list; we just haven't rendered
  it. Adding a collapsible "Revision history" section is a tidy follow-up
  that doesn't change any API.
* `Run a profile-aware recommendation` button works against the
  existing `/api/v1/pipeline/run` mechanism. If the seeded test
  environment has no fresh signals, the user sees a `status=failed`
  message rather than a recommendation. That's the right behavior — it
  surfaces the operational state honestly — but a future BETA-3 panel
  should expose the same status more prominently.
* The edit mode keeps Back at the top of the wizard pointing to view
  mode (not exiting the page). If the user wants to discard mid-edit
  they can press Back on the first wizard step to return to view.

## Sources

* (no new external sources beyond W-1..W-5)
