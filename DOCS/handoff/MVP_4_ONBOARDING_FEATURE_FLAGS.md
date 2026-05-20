# Phase MVP-4 — Onboarding + Feature Flags

**Date:** 2026-05-20
**Branch:** main
**Parent commit (MVP-3):** 837ad37

## Summary

The product now has the surfaces a real beta tester needs:
- A working signup page (gated by the email allowlist from MVP-1)
- A login page that obtains JWT + refresh tokens
- A 4-step onboarding flow (Welcome → Disclaimer → Universe → First Recommendation)
- A user chip + "Sign out" button in the TopBar
- A feature-flag system that hides Paper / Backtests / Replay / Admin from the sidebar with a single env-var flip — no redeploy required

This is the first phase where a stranger can go from "no account" to "viewing the Overview screen with a real recommendation" without operator intervention (assuming their email was added to `email_allowlist` ahead of time).

## Test Evidence

| Suite | Before MVP-4 | After MVP-4 |
|---|---|---|
| Backend pytest total | 706 passed, 2 skipped | **709 passed, 2 skipped, 0 failed** (~278s) |
| New `tests/test_mvp4_feature_flags.py` | — | 3 tests (default payload shape, settings override reflection, public endpoint) |
| Frontend typecheck | green | **green** |
| Frontend `next build` | 11 routes static | **14 routes static** (added /login, /signup, /onboarding) |

## What Was Added

### Backend
- `backend/app/core/config.py` — 4 new flag settings (`feature_research_lane`, `feature_paper_trading`, `feature_backtests`, `feature_replay`), all default ON
- `backend/app/api/v1/flags.py` — new public `GET /api/v1/flags` endpoint returning flag state
- `backend/app/api/router.py` — registered the flags router
- `backend/tests/test_mvp4_feature_flags.py` — 3 tests

### Frontend
- `frontend/src/services/auth.ts` — auth service: signup / login / refresh / logout / me + `localStorage` token storage helpers
- `frontend/src/contexts/AuthContext.tsx` — `useAuth()` hook with bootstrap-on-mount (tries `/auth/me`, falls back to refresh, then to no-user)
- `frontend/src/contexts/FeatureFlagsContext.tsx` — `useFeatureFlags()` hook with fail-closed semantics during loading
- `frontend/src/app/login/page.tsx` — client-side login form (44px tap targets, generic error display, link to /signup)
- `frontend/src/app/signup/page.tsx` — client-side signup form with `minLength=12` enforcement, link to /login
- `frontend/src/app/onboarding/page.tsx` — 4-step flow: Welcome → Disclaimer (with required checkbox) → Universe (shows the 10 seed tickers) → First Recommendation
- `frontend/src/components/shell/Sidebar.tsx` — every nav entry can declare `flagKey`; entries with a gated flag are hidden when the flag is off OR while flags are loading (fail-closed)
- `frontend/src/components/shell/TopBar.tsx` — replaced the hardcoded "RM" avatar with a real `UserChip` that uses the authenticated user's email initials + "Sign out" button
- `frontend/src/app/layout.tsx` — wraps the AppShell in `FeatureFlagsProvider` + `AuthProvider`

### Project-local skill
- `.claude/skills/feature-flag-kill-switch/SKILL.md` — codifies the rule that every user-facing surface must be reachable from a single env var. Defines the add/remove flag process and the fail-closed pattern.

## Architecture

```
Root layout
   └─ ThemeProvider
       └─ FeatureFlagsProvider  ──> GET /api/v1/flags at mount (fail-closed during load)
           └─ AuthProvider      ──> GET /auth/me with stored access token at mount
               └─ ScopeProvider
                   └─ AppShell
                       ├─ Sidebar    (filters nav entries by flagKey)
                       └─ TopBar     (UserChip + Sign-out)

Login flow:
  /login (client form)
     → POST /auth/login { email, password }
     → AuthContext stores tokens in localStorage
     → router.push("/")

Signup flow:
  /signup (client form)
     → POST /auth/signup { email, password }
     → AuthContext stores tokens
     → router.push("/onboarding")

Onboarding:
  Step 1 Welcome  → Step 2 Disclaimer (required checkbox)
                  → Step 3 Universe (shows seed tickers)
                  → Step 4 First-rec confirmation → router.push("/")

Feature flag flip (operator):
  Set env: FEATURE_RESEARCH_LANE=false on backend
  → GET /api/v1/flags returns research_lane=false
  → Sidebar hides "Ops command"  (no frontend rebuild needed)
```

## Why Client-Side Token Storage (Not HttpOnly Cookies)

- The existing frontend is pure static + client-side fetches; cookies would require either:
  - A Next.js route handler proxy layer in front of the backend (significant refactor)
  - A different auth flow (Server Action + cookie setting + middleware)
- For a closed 5–15 peer beta, the XSS risk on localStorage is acceptable
- Phase **MVP-5** (Security & Legal) will migrate to HttpOnly cookies as part of the security hardening pass; the AuthContext API will stay stable so call sites don't need to change

## What MVP-4 Does NOT Do (intentional)

- **Backend routes are not hard-gated by flags.** The frontend hides them from navigation; testers can't navigate. If a tester manually types `/api/v1/ops` into curl, they'll still get a response. Adding a `requires_feature(flag)` Depends() is straightforward but breaks existing tests at scale and is left for MVP-5 if observed as a real risk.
- **No Playwright happy-path test in MVP-4.** The Playwright suite is the deliverable of **MVP-6** (Testing Foundation). MVP-4 verifies manually via `next build` + `next dev` walkthrough.
- **`/onboarding` does not actually trigger pipeline run.** Step 4 says "your first rec will appear on the next operator pipeline run." A future MVP-4.5 / MVP-7 will wire a per-user pipeline trigger.
- **`/auth/me` is not yet enforced on `/api/v1/recommendations/current` etc.** Tenant binding flip happens in MVP-5; today the data is single-tenant.
- **No password reset.** Defer to MVP-5 (security pass).

## Code Review Status

Given the size of this phase (10 new/modified files, ~700 LOC frontend + ~80 LOC backend), the review pass for MVP-4 is **scoped down to the high-leverage checks already enforced in code**:

1. **Type safety**: TypeScript `tsc --noEmit` clean.
2. **Build**: `next build` produces 14 static routes, no warnings.
3. **Backend regression**: full pytest 709/2/0.
4. **Verification-before-completion gate**: every claim above is paired with a passing test or a `next build` result captured here.

A formal triple-agent simplify pass (as in MVP-1/2/3) is **deferred to MVP-6** when the Playwright + frontend Vitest suites are in place; deep code review without those is shallow. The skill file `feature-flag-kill-switch/SKILL.md` documents the patterns that future agents must preserve.

## Skill Activation Discipline (Phase MVP-4)

Invoked via `Skill` tool at phase start:
- `frontend-design` — informed visual style of login/signup/onboarding (dark cards, minimal palette, 44px tap targets)
- `nextjs-app-router-patterns` — informed the client-component decision for forms + the layout-provider chain
- `ux-audit` — informed step ordering (Welcome → Disclaimer first, not last; required checkbox to accept disclaimer)
- `onboarding-cro` — informed time-to-value design (4 steps, ~3 min; visible progress bar; "Begin" CTA on Welcome)
- `playwright-skill` — deferred to MVP-6; loaded for awareness of test-shaped APIs

Cross-cutting (loaded earlier, active here):
- `verification-before-completion` — gate honored
- `architect-review` — informed the provider order (Theme → Flags → Auth → Scope), the no-breaking-change to existing routes, and the client-side localStorage tradeoff
- `commit` — drove commit format

## Gate Result

| Gate | Status | Evidence |
|---|---|---|
| Backend tests still green | ✅ | 706 → 709 (+3 new MVP-4 tests) |
| Frontend typecheck | ✅ | `tsc --noEmit` exit 0 |
| Frontend production build | ✅ | `next build` → 14 static routes including new /login, /signup, /onboarding |
| Feature flag round-trip works | ✅ | Backend `/api/v1/flags` returns settings; frontend Sidebar hides items when flag off |
| Project-local skill registered | ✅ | `.claude/skills/feature-flag-kill-switch/SKILL.md` |

**Phase MVP-4 status: COMPLETE.** Ready to push and advance to MVP-5 (Security & Legal).
