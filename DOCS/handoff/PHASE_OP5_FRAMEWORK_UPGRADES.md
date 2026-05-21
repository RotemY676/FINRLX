# Phase OP-5 — FastAPI 0.115→0.118 + Next 14→15 + React 18→19 (closes Phase OP)

**Date:** 2026-05-21
**Base commit:** `c68ae07` (OP-4)
**Track:** Phase OP — sub-phase 5 of 5 (closes Phase OP).

## What this sub-phase ships

Backend FastAPI bumped from 0.115.6 → 0.118.0 (pulls in Starlette 0.46+
with its CVE patches). Frontend Next.js bumped from 14.2.35 → 15.5.18,
which brings React 18.3.1 → 19.2.6 and the React 19 type definitions.
Both went through with **zero source-code edits required** and full
gate-suite green.

| Change | Before | After |
|---|---|---|
| `fastapi` | 0.115.6 | 0.118.0 |
| `starlette` (pinned) | (transitive ~0.41) | `>=0.46, <1.0` |
| `next` | 14.2.35 | 15.5.18 |
| `react`, `react-dom` | 18.3.1 | 19.2.6 |
| `vite` (explicit dep, needed by Next 15 → vitest plugin chain) | — | 6.4.2 |

## Risk audit — why each upgrade was safe for FINRLX

### FastAPI 0.115 → 0.118

Three documented breaking categories; none affected FINRLX:

1. **401 vs 403 from `HTTPBearer`** — we don't use `HTTPBearer`.
   `app/api/auth_deps.py` reads the Authorization header manually and
   returns 401 throughout. Confirmed via `grep -rn "HTTPBearer" app/` (no
   hits).
2. **Dependency `yield` ordering change** — only matters when a
   `yield` dep is consumed by a `StreamingResponse` that itself uses
   the yielded resource. Our only `yield` dep is `get_db`
   (`app/core/database.py`), and no endpoint streams from a live DB
   iterator. The 0.118 change is actually a bug fix in our direction.
3. **Python 3.8 dropped** — we run on 3.11 (CI logs confirm).

Bonus: starlette had to be pinned `< 1.0`. The first pip run pulled
starlette 1.0.0 (released independently of FastAPI's compatibility
window), which removed `Router.__init__(on_startup=...)` that FastAPI
0.118 still uses. The pin in `requirements.txt` keeps the install
deterministic and is documented inline.

### Next 14 → 15 (with React 19)

Four documented breaking categories; none caused issues:

1. **`fetch()` no longer cached by default** — we don't rely on Next's
   `fetch()` caching; our data layer uses `services/api.ts` →
   `apiFetch` (raw fetch + manual no-cache semantics).
2. **`request.cookies` / `request.headers` may be async** — we never
   touch these in app code.
3. **`runtime = "experimental-edge"` deprecated** — `grep -rn "edge"
   src/app/` returns no app-layer config.
4. **React 19 type changes** — `tsc --noEmit` exit code 0; no
   adjustments needed.

`vite` had to be added as an explicit devDependency because Next 15's
peer-resolution stopped hoisting it transitively for the
`@vitejs/plugin-react` chain that vitest uses.

## Gate results (verified locally, 2026-05-21)

| Gate | Pre-OP-5 | Post-OP-5 |
|---|---|---|
| Backend pytest | 924 / 2 skipped | **924 / 2 skipped** (unchanged) |
| Frontend tsc | clean | clean |
| Frontend vitest | 27 passed | **27 passed** (unchanged) |
| Frontend next build | 23 routes | **23 routes** (unchanged) |
| Playwright chromium | 31 passed | **31 passed** (unchanged) |
| Backend ruff | clean | clean |
| Backend mypy on `app/core/` | clean | clean |

Total gate impact: zero regressions across ~982 tests, two framework
major-version bumps.

## What changed at the dependency layer

| Layer | What pulled what |
|---|---|
| FastAPI 0.118 | requires Starlette ≥0.46 (pinned <1.0 to dodge Starlette 1.0 API removal) |
| Next 15 | requires React 19; eagerly pulls a different bundle of `@vitejs/plugin-react`-related transitives so `vite` must be explicit |
| React 19 | type definitions backward-compatible enough that no FINRLX `.tsx` needed an edit |

## Phase OP — ledger

| Sub | Title | Commit | New tests | Notes |
|---|---|---|---|---|
| OP-1 | Live deploy runbook | `8689c16` | (docs only) | blocked on user |
| OP-2 | Daily DAG + JobRun + cron CLI | `b8535c1` | +12 | no APScheduler dep |
| OP-3 | Notifications (webhook + SMTP) | `7bc9318` | +10 | idempotent at DB UNIQUE |
| OP-4 | DR runbook + JWT rotation + GDPR export | `c68ae07` | +3 | |
| OP-5 | FastAPI 0.118 + Next 15 / React 19 | this commit | (no new tests; covered by 982 existing) | zero source edits |

**Phase OP total:** 5 sub-phases. 25 new backend tests. 3 new DB tables
(`job_runs`, `notifications` plus the 2 already in earlier phases). 5
new CLI scripts. 2 new endpoint groups. 1 framework-version bump pair.

## Follow-ups

* **BETA-1..BETA-4** open the beta to 3–5 testers + ship a feedback
  channel + capture per-user usage in `/ops`.
* Watch for any Sentry-reported React-19 hydration warnings once OP-1
  goes live. React 19 tightens hydration mismatch checks; a few
  inline-style edge cases may warrant cleanup.
* When FastAPI publishes a Starlette-1.x-compatible release, remove the
  `starlette<1.0` pin.

## Honest limitations

* **Local-only verification.** The framework upgrade is green on my
  machine + my hermetic test DB. Production verification waits for
  OP-1's live deploy.
* **`npm audit` reports 15 vulnerabilities** post-install. Most are
  in dev-only transitives that Next 15 pulled. A separate cleanup
  commit can `npm audit fix --force` once we know it won't roll back
  the Next 15 install.
* **No Lighthouse run.** UX track's Lighthouse gate (Perf≥80,
  A11y≥95, BP≥95) requires a deployed URL; tracked alongside OP-1.
* **The 2 skipped tests** are pre-existing (one Phase-W8 conditional
  skip when the hermetic pipeline can't complete; one MVP-7
  observability skip when no DSN is set). Both remain skipped.

## Sources

* [FastAPI 0.118.0 release notes](https://fastapi.tiangolo.com/release-notes/) (yield ordering + Python 3.8 drop + Starlette ≥0.46)
* [Next.js 15 upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-15) (fetch caching, async request APIs, runtime export deprecation)
* [Next.js 15 release blog](https://nextjs.org/blog/next-15) (React 19, codemods)
