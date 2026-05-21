# Phase W-3 — 8-step Investor Profile Wizard (Frontend)

**Date:** 2026-05-21
**Base commit:** `307a948` (W-2)
**Track:** Phase W — sub-phase 3 of 8.

## What this sub-phase ships

The `/onboarding` page is rewritten from the MVP-4 4-step generic flow
into an 8-step investor-profile wizard. Question text, choices, scoring
and step grouping come entirely from the backend catalog
(`GET /api/v1/profile/questions`), so future tuning never needs a
frontend redeploy.

| Artifact | Path |
|---|---|
| TypeScript contract | `frontend/src/features/wizard/types.ts` |
| Auth-aware API helpers | `frontend/src/features/wizard/api.ts` |
| Single-step input widget | `frontend/src/features/wizard/QuestionField.tsx` |
| Final review step | `frontend/src/features/wizard/ReviewStep.tsx` |
| Shell + footer nav | `frontend/src/features/wizard/WizardLayout.tsx` |
| Orchestration page | `frontend/src/app/onboarding/page.tsx` (rewritten) |
| Validation tests | `frontend/src/__tests__/wizard-validation.test.ts` |

## Step layout

| # | Title | Source | Required? |
|---|---|---|---|
| 1 | Welcome | static | always |
| 2 | Knowledge & experience | server (4 Q) | all required |
| 3 | Financial situation | server (4 Q) | all required |
| 4 | Risk tolerance | server (8 Q) | all required |
| 5 | Investment objectives | server (3 Q) | all required |
| 6 | Universe & sector preferences | server (4 Q) | sector lists optional |
| 7 | Operational preferences | server (3 Q) | all required |
| 8 | Review + submit | computed | — |

## Behavior

* **Redirect protection.** On mount, the page calls `/profile/me`.
  If `has_profile=true`, the user is redirected to `/decision` — the
  wizard does not show twice.
* **Step gating.** The "Continue" button is disabled until every
  required question in the current step has an answer
  (`isStepComplete`). Optional questions (sector lists) can be left
  empty.
* **Risk-bucket preview.** The Review step computes `risk_score`
  client-side from the seeded `score` values and previews the bucket.
  The submit still recomputes everything server-side for authority.
* **Submit failure handling.** A failed POST shows the message in an
  `aria-live=assertive` banner and re-enables the submit button.

## Accessibility

* Progress bar exposes `role="progressbar"` with
  `aria-valuemin/valuemax/valuenow`.
* Each question is a `<fieldset>` with a `<legend>` (radio groups)
  / `role="group"` (multi-select).
* All interactive elements meet the existing UX-1.5 touch-target lint
  (`minHeight: 44`).
* Footer button + label width keeps the 4px outline of the focus ring
  visible per UX-3.1 axe sweep.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest | 788 passed (unchanged from W-2) |
| Frontend `tsc --noEmit` | exit 0 |
| Frontend vitest | **27 passed** (was 21; +6 new wizard tests) |
| Frontend `next build` | OK; 21 routes static; `/onboarding` 6.33 kB |
| Playwright chromium | **28 passed** (full mobile-viewport suite) |
| Touch-target lint | green (no `h-6/h-8/h-9` on interactive elements) |

## Follow-ups for W-4 and beyond

* **W-4** turns `(risk_bucket, horizon_band)` into a target
  equity/defensive split with reference to Vanguard / Fidelity model
  portfolio tables. Stored as a deterministic mapping table, with one
  unit test per band.
* **W-5** wires the active profile into the pipeline:
  - sector_whitelist / sector_blacklist filter Universe at recommendation
    time;
  - region_preference scopes the data adapter;
  - max_drawdown_pct constrains the Risk Overlay;
  - trading_frequency drives the timing engine cadence.
* **W-7** "Edit my profile" page reuses the same wizard components and
  pre-fills answers from `/profile/me`.
* **W-8** end-to-end Playwright spec covers signup → complete wizard
  → land on `/decision` with the new profile linked.

## Honest limitations

* This sub-phase does **not** yet wire the profile into recommendation
  generation. A user who completes the wizard sees the same
  recommendations as before the wizard existed. W-5 closes that gap.
* The risk-bucket preview on the Review step uses the same thresholds as
  the backend; if you change the backend bands without updating
  `ReviewStep.tsx`, the preview drifts (but the saved value is always
  authoritative). Adding a contract test that asserts both ends agree
  is a tidy follow-up.
* No animation between steps; we kept the transition simple to stay
  inside the existing inline-style pattern and avoid pulling in a
  motion library mid-track.

## Sources

* [ESMA MiFID II suitability guidelines (Sept 2022)](https://www.esma.europa.eu/sites/default/files/2023-04/ESMA35-43-3172_Guidelines_on_certain_aspects_of_the_MiFID_II_suitability_requirements.pdf)
* [Wealthfront onboarding teardown (Appcues)](https://goodux.appcues.com/blog/wealthfront-personalized-ux-copy)
* WCAG 2.2 — radio-group + fieldset/legend pattern.
