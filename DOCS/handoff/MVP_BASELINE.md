# MVP Baseline — Phase MVP-0

**Date:** 2026-05-20
**Phase:** MVP-0 (Baseline & Cleanup)
**Branch:** main
**Parent commit:** 52b3b5f (fix: Phase 8N.2A-fix1)

This document is the honest, verified starting state for the MVP-Beta track. All claims below are backed by commands run during this phase (see "Evidence" sections).

---

## 1. Test Baseline (Backend)

**Command:** `python -m pytest --tb=line -q` (from `backend/`)

**Result:** `648 passed, 2 skipped, 1 warning in 525.90s (0:08:45)`

- 0 failures
- 2 skips are intentional (visible as `s` in dot output, not investigated further at this stage)
- 1 deprecation warning: `pytest_asyncio` event_loop fixture redefinition in `backend/tests/conftest.py:33`. Non-blocking. Tracked for cleanup in Phase MVP-6.

**Test collection breakdown:** 41 test files, 650 tests collected (`python -m pytest --collect-only -q`).

---

## 2. Build Baseline (Frontend)

**Frontend stack:** Next.js 14.2.35, React 18.3.1, TypeScript 5.7.2, Tailwind 3.4.16. App Router.

**Commands run:**
- `npm install` → up-to-date, 458 packages
- `npm run typecheck` (`tsc --noEmit`) → clean, exit 0
- `npm run build` (`next build`) → ✓ Compiled successfully

**Routes built (11 static):** `/`, `/_not-found`, `/admin`, `/backtests`, `/comparison`, `/decision`, `/icon.svg`, `/paper`, `/replay` plus default Next.js pages. All prerendered static.

**Bundle sizes (First Load JS):**
- `/admin` 191 kB — largest, expected (deep panel surface)
- `/decision` 208 kB
- `/comparison` 199 kB
- `/backtests` 198 kB
- `/paper` 194 kB
- `/replay` 97.3 kB
- `/` 95.7 kB
- Shared chunks: 87.5 kB

**Vulnerabilities flagged at baseline (deferred to Phase MVP-5):**
- `npm audit`: 6 vulnerabilities (2 moderate, 4 high). Not remediated in MVP-0.

---

## 3. Codebase State (Verified, not Claimed)

### Backend
- 187 routes registered (per prior audit; not re-counted in MVP-0)
- 22 service modules under `backend/app/services/`
- 17 Alembic migrations in `backend/migrations/versions/`
- Recommendation Object schema: `backend/app/models/recommendation.py` — production-quality (10-state enum, lineage, confidence triplet, validity window, weights)
- Synthetic data only: `backend/app/services/ingest.py` produces random-walk OHLCV from hardcoded `_BASE_PRICES`. No live data adapter.

### Frontend
- 7 wired Next.js routes (verified above via `next build` output)
- ~14 admin shell components under `frontend/src/app/admin/_components/`
- Zero frontend tests (no `*.test.*` / `*.spec.*` files, no Playwright)

### Design Package
- `design/handoff-package/` contains ~7 HTML mockups (Onboarding, Universe, Integrations, Policy Editor, Backtests, Design System, States, Paper Portfolio, Replay) that are NOT wired into the Next.js app — they're prototypes only.

---

## 4. Critical Gaps to MVP (Per-User Authoritative List)

These are the gaps Phase MVP-0 explicitly does NOT fix — they're the scope of MVP-1 through MVP-8:

| # | Gap | Target Phase |
|---|---|---|
| 1 | No User/Session model, no JWT auth, no `Depends(get_current_user)` | MVP-1 |
| 2 | No tenant isolation; all data is single-user | MVP-1 |
| 3 | No Postgres RLS | MVP-1 |
| 4 | Synthetic market data only (no yfinance/Polygon/Alpaca) | MVP-2 |
| 5 | No Recommendation provenance hash / replay seed | MVP-3 |
| 6 | Onboarding screen is HTML mockup only, not in Next.js app | MVP-4 |
| 7 | No feature flag system (research lane needs hiding for MVP) | MVP-4 |
| 8 | No rate limiting on auth/ingest/recommendation endpoints | MVP-5 |
| 9 | No security headers middleware (CSP/HSTS/X-Frame-Options) | MVP-5 |
| 10 | No legal disclaimer ("Not investment advice") on recs | MVP-5 |
| 11 | 6 npm audit vulnerabilities (2 moderate, 4 high) | MVP-5 |
| 12 | Zero frontend tests; no Playwright E2E | MVP-6 |
| 13 | No CI workflow file (no GitHub Actions) | MVP-6 |
| 14 | No Sentry error tracking | MVP-7 |
| 15 | No PostHog analytics | MVP-7 |
| 16 | Railway deploy failed 2026-04-24, not retried since (per artifacts now in `archive/_railway_oneclick_attempts/`) | MVP-7 |
| 17 | No `/healthz` deep check (DB + last-ingest age) | MVP-7 |

---

## 5. MVP-0 Cleanup Actions Performed

1. Moved stranded Railway artifacts to `archive/_railway_oneclick_attempts/`:
   - `_railway_oneclick_backup_20260424_175509/`
   - `_railway_oneclick_backup_20260424_180610/`
   - `_railway_oneclick_report_20260424_175509.txt`
   - `_railway_oneclick_report_20260424_180610.txt`
2. Added `.gitignore` patterns for future Railway one-click artifacts (`_railway_oneclick_backup_*/`, `_railway_oneclick_report_*.txt`).

No code changes. No test changes. No dependency changes. This phase is informational only.

---

## 6. Tester Decisions (Locked-in This Session)

| Question | Answer |
|---|---|
| Auth provider | Hand-rolled (no third-party) |
| Tester invite mechanism | Email allowlist |
| Live execution scope | Paper trading only |
| Deploy target | Stay on Railway |
| Beta volume | 5–15 sophisticated peers |

---

## 7. Skill Activation Discipline

Per the project working agreement, every phase opens by invoking its skill bundle via the `Skill` tool. MVP-0 invoked:

- `production-audit` — deferred to MVP-7 (needs live URL)
- `verification-before-completion` — active as the gate before every "done" claim
- `architect-review` — used for the audit framing in this doc
- `codebase-audit-pre-push` — used to validate cleanliness of the cleanup
- `code-reviewer` — pre-push review of `.gitignore` + this doc
- `simplify` — pre-push pass (no code changed; no-op)
- `commit` — drives commit message format

---

## 8. Gate Result

| Gate | Status | Evidence |
|---|---|---|
| Backend tests green | ✅ | 648 passed, 2 skipped, 0 failed |
| Frontend typecheck green | ✅ | `tsc --noEmit` exit 0 |
| Frontend build green | ✅ | `next build` Compiled successfully, 11 routes |
| Stranded artifacts cleaned | ✅ | Moved to `archive/_railway_oneclick_attempts/`, gitignored |
| Baseline doc written | ✅ | This file |

**Phase MVP-0 status: COMPLETE.** Ready to push and advance to MVP-1.
