# Phase WIZ — Onboarding Wizard Implementation Report

Date: 2026-05-21
Branch: `main`
Phase commits: `6fb0b9d` → `75014e2` → `7f74bf3`

## 1. Reported issues

The user reported (Hebrew, translated):

> "This wizard should appear immediately after email signup. There must
>  also be an option to re-run it again and again through the personal
>  details / profile page in order to update the choices. Besides that,
>  the wizard isn't implemented at all yet."

Observed in production screenshots:

- `/onboarding` Step 1 (Welcome) renders correctly.
- `/onboarding` Step 2 says **"This step has no questions yet."**
- `/onboarding` Step 8 (Review) renders with empty risk score `0 / 32`.

## 2. Root cause

The wizard frontend (Phase W-3, components in `frontend/src/features/wizard/`)
was fully implemented, including all 26 question types, choice rendering,
multi-select handling, review screen, and submit pipeline. **The wizard
was broken in production because the `profile_questions` catalog table
was empty on the Railway database.**

The seed script `backend/scripts/seed_profile_questions.py` exists from
Phase W-1 and contains the full 26-question catalog (Knowledge ×4,
Financial ×4, Risk ×8, Objectives ×3, Universe ×4, Operational ×3), but
it was a one-off script and was **never wired into the Railway boot
sequence**. The boot seed `backend/seed.py` populated assets,
recommendations, ops/policy/RL state, but skipped the wizard catalog
entirely.

The result: `GET /api/v1/profile/questions` returned an empty list, the
frontend received zero questions for steps 2-7, and the placeholder
copy "This step has no questions yet" rendered.

A second, smaller issue: Google OAuth finish and email login both
routed every user to `/` after authentication, even if their
investor-profile was missing. New Google users could not reach the
wizard except by typing `/onboarding` manually.

A third, UX issue: the `/profile` page exposed re-running the wizard
behind a button labelled "Edit profile" — accurate but ambiguous about
whether it actually restarts the full questionnaire and saves a new
revision.

## 3. Phases shipped

### Phase B — Backend seeding (commit `6fb0b9d`)

`fix(seed): WIZ-1 — auto-seed profile_questions + templates on Railway boot`

- File: `backend/seed.py`
- Imports `scripts.seed_profile_questions.seed` and
  `scripts.seed_recommendation_templates.seed` inside
  `_seed_pipeline_stages`. Both are idempotent, so they no-op on
  subsequent boots once the catalogs exist.
- Each call is wrapped in `try/except` so a seed failure cannot crash
  the API on startup.
- Verified locally on a fresh SQLite migration:
  - First run: `inserted=26` profile questions, `inserted=5` templates.
  - Second run: `inserted=0` for both (skipped 26 / 5).
- Pytest: 20 Phase W1/W2 tests still pass.

### Phase C — Sign-in routing (commit `75014e2`)

`feat(auth): WIZ-2 — route incomplete users to /onboarding after sign-in`

- File: `frontend/src/app/login/page.tsx` — after `await login()`,
  probes `fetchMyProfile()`:
  - `has_profile === true` → `router.push("/")`
  - `has_profile === false` → `router.push("/onboarding")`
  - probe error → fallback to `/` (fail-open).
- File: `frontend/src/app/login/google-finish/page.tsx` — same logic at
  the OAuth finish step. First-time Google users land on the wizard;
  returning users go straight home.
- Email signup already routed to `/onboarding` (line 29 of
  `signup/page.tsx`) — unchanged.

### Phase D — Profile re-run discoverability + tests (commit `7f74bf3`)

`feat(profile): WIZ-3 — explicit 'Re-run the wizard' entry point on /profile`

- File: `frontend/src/app/profile/page.tsx`
  - Renamed "Edit profile" → **"Re-run the wizard"**.
  - Added `data-testid="rerun-wizard"` so the contract is locked in.
  - Added a one-line hint above the action buttons: "Run the wizard
    again any time to update your knowledge level, financial situation,
    risk appetite, objectives, or sector preferences. A new revision is
    saved each time."
- File: `frontend/src/__tests__/wizard-flow.test.tsx` — new test file
  with four contract tests:
  1. Email signup navigates to `/onboarding`.
  2. Email login → `/onboarding` when no profile.
  3. Email login → `/` when profile exists.
  4. `/profile` renders the "Re-run the wizard" button with the
     documented `data-testid` and the revision-explanation copy.

## 4. Verification

| Gate | Result |
|---|---|
| `python -m pytest backend/tests/test_phase_w*.py` | PASS — 24 passed, 1 skipped |
| `python scripts/seed_profile_questions.py` (idempotency) | PASS — 26 → 0 inserted on second run |
| `python scripts/seed_recommendation_templates.py` (idempotency) | PASS — 5 → 0 inserted on second run |
| `npm run typecheck` (frontend) | PASS — no TS errors |
| `npm run test:ci` (frontend) | PASS — 41/41 tests across 10 files |
| `npm run build` (frontend) | PASS — 27 static routes |
| Local SQLite seed end-to-end | PASS — both catalogs populate |

## 5. Files changed

| File | Phase | Change |
|---|---|---|
| `backend/seed.py` | B | Added profile_questions + templates to boot seed |
| `frontend/src/app/login/page.tsx` | C | Probe `/profile/me` after login |
| `frontend/src/app/login/google-finish/page.tsx` | C | Probe `/profile/me` after Google OAuth |
| `frontend/src/app/profile/page.tsx` | D | Re-labeled CTA, added hint, `data-testid` |
| `frontend/src/__tests__/wizard-flow.test.tsx` | D | New 4-test contract suite |

## 6. Expected behavior after Railway deploy

Once Railway picks up commit `7f74bf3` (or later) and reboots the
backend, every request to `GET /api/v1/profile/questions` will return
the full 26-question catalog. End-to-end the user-facing behavior is:

1. **Email signup**: `/signup` → `/onboarding` → wizard steps 1-8
   populated → `submitProfile` → `/decision`.
2. **Email login (incomplete user)**: `/login` → `/onboarding`. Picks
   up wherever the wizard answers were last saved (currently the
   wizard is in-memory until submit; the user starts from step 1 but
   the catalog renders correctly).
3. **Email login (complete user)**: `/login` → `/`.
4. **Google signup or first sign-in**: `/login/google-finish` →
   `/onboarding`.
5. **Google returning sign-in**: `/login/google-finish` → `/`.
6. **Re-run wizard**: `/profile` → click "Re-run the wizard" →
   inline 8-step wizard with current answers pre-filled →
   "Save changes" → new revision (v2, v3, …) persisted.

## 7. Honest limitations

- **Live Railway probe**: At report-write time the Railway deploy for
  commit `6fb0b9d` (Phase B seed wiring) is in flight; the seed will
  run on the next container reboot. I cannot confirm from outside
  authentication whether the catalog is currently populated — the user
  must re-test `/onboarding` after Railway finishes deploying.
- **In-memory wizard state**: If a user starts the wizard, answers
  some questions, and refreshes the page, they restart at step 1. The
  wizard does not persist intermediate answers — only the final
  submission. That is a pre-existing limitation (Phase W-3); not in
  scope here.
- **No backend tests for the boot seed integration** were added.
  Adding one would require booting the FastAPI app in a fixture, which
  is heavy. The seed functions themselves are covered by their own
  scripts. Idempotency was verified by manually running the seeds
  twice on a fresh SQLite DB.
- **Old "Edit profile" copy callers**: no other call sites referenced
  that label (grep clean), so the rename did not break any other
  routing or analytics events.
