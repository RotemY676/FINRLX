# Phase MVP-5 — Security & Legal Scaffolding

**Date:** 2026-05-20
**Branch:** main
**Parent commit (MVP-4):** 46fac6e

## Summary

FINRLX is now safe to put in front of strangers. The phase added the cheap-but-non-negotiable security and compliance controls every beta needs before invites go out:

- **slowapi rate limiting** on auth, ingest, and recommendation-write endpoints (per-IP token bucket, X-Forwarded-For aware)
- **HTTP security headers** middleware (X-Frame-Options, HSTS, Referrer-Policy, Permissions-Policy, CORP/COOP)
- **Blocking one-time disclaimer modal** + **persistent footer banner** on every page
- **`/terms`, `/privacy`, `/disclaimer` static pages**
- **Project-local skill `fintech-disclaimer-and-marketing-guard`** registered for future copy reviews
- **PyJWT 2.10.1 → 2.12.0** (vuln fix PYSEC-2026-120)
- **`DOCS/handoff/SECRETS_RUNBOOK.md`** — rotation + leak-response playbooks

The disclaimer is the FIRST interactive element on first visit; a reasonable tester cannot reach a Recommendation without seeing it. Acceptance is persisted in `localStorage` and versioned, so the next legal-text change can force re-acceptance.

## Test Evidence

| Suite | Before MVP-5 | After MVP-5 |
|---|---|---|
| Backend pytest total | 709 passed, 2 skipped | **716 passed, 2 skipped, 0 failed** (~377s) |
| New `tests/test_mvp5_security_headers.py` | — | 4 tests (presence on /health + /api/v1/flags, X-Frame-Options DENY, HSTS year-long) |
| New `tests/test_mvp5_rate_limit.py` | — | 3 tests (429 after burst, disabled-mode unblocked, Retry-After header) |
| Frontend `tsc --noEmit` | green | **green** |
| Frontend `next build` | 14 routes static | **17 routes static** (added /terms, /privacy, /disclaimer) |

## What Was Added

### Backend

- **`backend/app/core/security_headers.py`** — `SecurityHeadersMiddleware`. Sets seven headers per response from a single module-level dict (zero-allocation per request). HSTS is sent unconditionally because Railway terminates TLS upstream.
- **`backend/app/core/rate_limit.py`** — slowapi `Limiter` keyed on `X-Forwarded-For` (Railway proxy header) with a `get_remote_address` fallback. Default cap `120/minute` global; named tighter caps per endpoint family.
- **`backend/app/core/config.py`** — five new settings: `rate_limit_enabled`, `rate_limit_default`, `rate_limit_auth` (10/min), `rate_limit_ingest` (20/min), `rate_limit_recommendation_write` (30/min). All overridable via env.
- **`backend/app/main.py`** — wires `app.state.limiter`, registers the slowapi exception handler, and adds `SecurityHeadersMiddleware` + `SlowAPIMiddleware` in the correct order.
- **`backend/app/api/v1/auth.py`** — `@limiter.limit(settings.rate_limit_auth)` on `signup`, `login`, `refresh`. Switched away from `from __future__ import annotations` and used `Annotated[X, Body()]` form because slowapi's `functools.wraps`-style wrapping leaves the wrapped function with slowapi's `__globals__`, which broke FastAPI's `get_type_hints()` resolution. **Without this fix, all POST bodies on rate-limited endpoints failed validation with "field required (query)" 422s.**
- **`backend/app/api/v1/ingest.py`** — limiter on `trigger_bar_ingestion`, `trigger_news_ingestion`.
- **`backend/app/api/v1/actions.py`** — limiter on `save_thesis`, `promote_paper`, `defer_decision`.
- **`backend/tests/conftest.py`** — sets `limiter.enabled = False` at import so the existing 700+ tests stay hermetic. Tests that need the limiter active flip it inside a `try/finally`.
- **`backend/requirements.txt`** — `slowapi==0.1.9`, `PyJWT==2.12.0` (vuln bump).

### Frontend

- **`frontend/src/components/legal/DisclaimerBanner.tsx`** — pinned footer with the standard not-investment-advice line + links to the three legal pages. Marked `data-disclaimer="true"` for the guard skill to detect.
- **`frontend/src/components/legal/DisclaimerModal.tsx`** — blocking modal on first visit. Acceptance versioned (`STORAGE_KEY = "finrlx-disclaimer-accepted-v1"`); changing `DISCLAIMER_VERSION` forces re-acceptance after a copy change. Falls back to "show every visit" if localStorage is blocked.
- **`frontend/src/components/shell/AppShell.tsx`** — mounts `<DisclaimerModal />` + `<DisclaimerBanner />` so every routed page inherits both.
- **`frontend/src/app/disclaimer/page.tsx`**, **`terms/page.tsx`**, **`privacy/page.tsx`** — static legal copy. The privacy page enumerates what data is and isn't collected; relevant for the GDPR ask if/when EU testers join.

### Skills & docs

- **`.claude/skills/fintech-disclaimer-and-marketing-guard/SKILL.md`** — listed in the available-skills feed. Encodes the forbidden-verbs list (FINRA Rule 2210 / MiFID II Article 24 grounded) and the disclosure-presence rule (every Recommendation render tree must include `<DisclaimerBanner />` or `data-disclaimer="true"`).
- **`DOCS/handoff/SECRETS_RUNBOOK.md`** — inventory, rotation playbooks (planned + emergency), leak-response procedure.

## Audit results

### Backend (`pip-audit -r backend/requirements.txt`)

| Package | Version | CVE | Fix version | Action |
|---|---|---|---|---|
| PyJWT | 2.10.1 → **2.12.0** | PYSEC-2026-120 | 2.12.0 | **Fixed.** |
| PyJWT | 2.12.0 | PYSEC-2025-183 | (no fix) | Documented; no fix available upstream. Re-check next phase. |
| python-dotenv | 1.0.1 | CVE-2026-28684 | 1.2.2 | Dev-only loader. Deferred to MVP-6 dependency upgrade pass. |
| pytest | 8.3.4 | CVE-2025-71176 | 9.0.3 | Dev-only. Deferred. |
| starlette | 0.41.3 | CVE-2025-54121 / CVE-2025-62727 | 0.47.2 / 0.49.1 | Bundled with FastAPI 0.115.6. The fix requires FastAPI 0.118+, a major upgrade. Deferred to MVP-6 dependency upgrade pass. |

### Frontend (`npm audit`)

6 vulnerabilities in Next.js 14.2.35 (already the latest stable on the 14.2 line). The only available fix is `next@16.x`, which is a breaking change for the App Router contract. Deferred to MVP-6 framework upgrade pass; the specific CVEs (DoS via next/image, RSC cache poisoning, SSRF on WebSocket upgrade) do not apply to our current usage of next/image, our RSC patterns, or our (absent) WebSocket endpoints — so the risk is low for the closed beta.

## Gate decisions

- ✅ Every gate test for MVP-5 passes (7/7 new + 716 cumulative).
- ✅ Frontend builds and typechecks cleanly. Three new static routes (`/terms`, `/privacy`, `/disclaimer`).
- ✅ Manual smoke: disclaimer modal blocks first paint until accepted; banner persists on every route.
- ✅ /simplify reviewer findings addressed (conftest limiter placement, test cap derived from settings).
- ⚠️ Two SAST/deps findings deferred to MVP-6 (FastAPI/starlette major + Next.js major) — documented above, not silently ignored.

## What's next — Phase MVP-6 (Testing Foundation + Hygiene Gates)

Goal: regression-safe before deploy. Will add Vitest + Playwright E2E + axe-core a11y + GitHub Actions CI + the backtest-hygiene-gate skill. Will also pick up the dependency upgrades deferred here (FastAPI/starlette major; Next.js 14 → 16).
