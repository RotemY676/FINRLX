# FINRLX — Unimplemented / deferred functionality audit (2026-05-22)

> Source-of-truth scan across the entire repo for functionality that
> was left "for a later phase". Cross-references every Phase 0–16
> report, every code comment containing "coming later", "TODO",
> "deferred", "stub", "shim", "503", every disabled affordance, every
> "coming soon" help-doc entry.
>
> I also caught two of my own past errors — items I marked "no
> playwright config" / "no e2e tests" / "no next.config.js" in
> earlier phase reports. **All three exist.** That correction is
> included below (rows 31–33) for full honesty.

## How to read this

- **Severity** is my opinion about user-visible impact:
  - **H** = users notice this is missing or it blocks a real workflow.
  - **M** = degrades the experience but not blocking.
  - **L** = polish / tidy-up / future-proofing.
- **Effort** is rough: **S** = under a day, **M** = 1–3 days,
  **L** = a real phase.
- "Owner" is which phase report originally noted the gap (so you can
  cross-read context).

## A. Frontend product surfaces

| # | Area | What's missing | Current state | Why deferred | Owner | Severity | Effort |
|---|---|---|---|---|---|---|---|
| 1 | TopBar (v2) | Legacy v2 TopBar still in bundle | Toggle in avatar menu lets you flip between v3 (default) and v2; v2 lives at `TopBar.tsx` (~ 7 KB) | Kept until you validate v3 in a working session | 15 / 15.6 | L | S |
| 2 | UserMenu | "Add another account" / "Switch account" rows | Rendered as **disabled stubs** with "Coming later" tooltip | `AuthContext` is single-user; multi-account session not implemented | 14.2 | L | M |
| 3 | Decision page | `/decision/[id]` per-recommendation deep-link route | Only `/decision` (= current rec) exists | Frontend wiring against `/recommendations/list` + `/recommendations/{id}` not done; backend supports it | 7 / J.1 | M | M |
| 4 | Decision page | Hero + ContextPane split | Long single scroll on `/decision` | Risky restructure without user-testing data; explicitly deferred | 7 / J.2 | M | M |
| 5 | Decision page | Audit-trail drawer per recommendation | Not surfaced on frontend | No per-recommendation audit endpoint consumed yet | 7 / J.3 | M | M |
| 6 | Decision page | Publication-gate checklist | Not surfaced | Backend has gates in `publication.py`; frontend doesn't render them per-rec | 7 / J.4 → Phase 10 | M | M |
| 7 | Portfolio | `/portfolio` tabbed landing (Paper / Risk / Scenario) | `/paper` and `/risk` are still siblings; no parent route | Cosmetic restructure without user-testing data | 8 / J.1 | L | M |
| 8 | Portfolio & Risk | Correlation clusters, scenario stress, upcoming-earnings exposure | None | Backlog item P-2; needs backend work | 8 / J.3 | M | L |
| 9 | Portfolio & Risk | Inner KPI-tile typography migration (~ 20 hand-rolled `text-[Npx]` instances) | Tiles work but ship ad-hoc sizes | Tedious sweep, deferred | 8 / J.2 + 10 / J.1 | L | S |
| 10 | News / Insights | `/news` → `/insights` rename + redirect | Route still at `/news`; sidebar label unchanged | Waits for the `next.config.js` redirects rollout | 9 / J.1 | L | S |
| 11 | News / Insights | Watchlist / portfolio / decision filter on items | Only sentiment chip filter ships (frontend-only) | Needs backend taxonomy: ticker / portfolio relevance tagging | 9 / J.3 + 16 | M | L |
| 12 | News / Insights | "Why this matters" per-item summary | Sentiment label + raw RSS summary only | Needs LLM grounding or operator-curated annotation | 9 / J.2 | M | L |
| 13 | News / Insights | Backend `?sentiment=&ticker=` query params | Frontend filter runs over the full payload (50ish items) | Backend doesn't accept the filter | 9 / J.4 | L | S |
| 14 | Ops & Governance | `next.config.js` `redirects()` block for legacy paths | File exists with only the `rewrites()` block; no redirects yet | Target sub-routes (`/portfolio/*`, `/ops/policies`, `/ops/lab`, `/insights`, `/decision/[id]/compare`) don't exist | 10 / J.2 | L | S |
| 15 | Ops & Governance | Group `/policies` and `/integrations` under `/ops/*` | They live at root paths still | Same as row 14 — waits for redirects + IA target routes | 10 / E.2 | L | S |
| 16 | Ops & Governance | Progressive disclosure for incidents + audit tables | Flat tables on `/ops` | Drawer pattern already exists on `/policies`; not extended to incidents | 10 / J.3 | L | M |
| 17 | Operator console | Embedded source-grounded assistant inside `/operator` | Operator pastes LLM context manually; deep-linked from home assistant card | Backend `/api/v1/assistant/*` returns 503 (LLM provider not configured); no in-app chat surface | 11 / J.1 | M | L |
| 18 | Assistant card on Home | Live `/assistant/status` consumption + retrieval-state pill | Home preview always reads "via operator console" | Two-line follow-up; ships when an LLM provider is configured | 11 / J.2 | L | S |
| 19 | Home Decision Center | `fetchWorkspaceCounts` extension with `insights_unread` + `portfolio_alerts` | Sidebar badges work only for `overview / decisions / risk / ops` | Backend doesn't return the new fields | 9 / F + 8 / F | L | S |
| 20 | Research / ticker | `as_of` field is always null on Fundamentals | Provenance footer shows `cached_at` only | Finnhub's `metric=all` envelope doesn't carry a per-metric as-of | 16 / N.2 | L | S |
| 21 | Research / ticker | Forward P/E tile collapses for most tickers | Free tier doesn't include analyst consensus EPS | Finnhub paid tier (or alternate provider) required | 16 / N.1 + 16.4 | M | L |
| 22 | Research / ticker | Analyst consensus / recommendation trends | Not surfaced anywhere | Finnhub paid-tier feature | 16 / N.5 | L | L |
| 23 | Research / ticker | Help-articles search inside the command palette | Palette searches routes / tickers / operator analyses only | No runtime MDX index; build-step indexer not built | 14.3 / J.3 | L | M |
| 24 | Research / ticker | Recommendations list category in the command palette | Not searchable from palette | No `/recommendations/list` typed on the frontend | 14.3 / J.4 | M | M |
| 25 | TopBar / palette | OS-aware `⌘K` vs `Ctrl+K` glyph | Mac glyph hardcoded everywhere | `navigator.platform` detection follow-up | 15 / J.6 | L | S |
| 26 | Sidebar | Saved-views section per-user | Backend-implemented; renders only when the user has saved views | None — this WAS the deferred work that landed in Phase B3 | (closed) | — | — |

## B. Backend service stubs

| # | Service | What's a stub | Activation | Owner |
|---|---|---|---|---|
| 27 | LLM assistant — Anthropic provider | All three providers (Anthropic / OpenAI / local Ollama) ship as `StubProviderError` raises; `/assistant/*` endpoints 503 | Set `LLM_PROVIDER=…` + matching key | Phase O-5 |
| 28 | Notifications backend | `app/services/notifications.py` raises `RuntimeError("NOTIFY_WEBHOOK_URL not configured")` when webhook unset | Set `NOTIFY_WEBHOOK_URL` to a real endpoint | Phase OP-3 |
| 29 | Google OAuth | `/auth/google/*` returns 503 when client_id/secret are empty | Set `GOOGLE_OAUTH_CLIENT_ID` + `GOOGLE_OAUTH_CLIENT_SECRET` | Phase OAuth-Google |
| 30 | Sentry observability | `instrumentationHook: true` in next.config.js but `SENTRY_DSN=""` by default → SDK init is a no-op | Set `SENTRY_DSN` in Railway env | Phase MVP-7 |

## C. My own factual errors in earlier phase reports — corrections

I marked these as "missing" / "not done" multiple times. **They exist.**
The actual gap is that I never ran the test suites during my phase
gates. Correcting publicly here for honesty.

| # | Item | What I said | What's actually true | Real gap (if any) |
|---|---|---|---|---|
| 31 | Playwright config | "No `playwright.config.*` in repo" (Phase 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 reports) | `frontend/playwright.config.ts` exists — Chromium project, auto-spins `next start` on 127.0.0.1:3000 | I never ran `npm run e2e:ci` at any gate; should re-baseline against the existing suite |
| 32 | E2E tests | "No `e2e/` directory" | `frontend/tests/e2e/` ships **20 spec files** (admin, backtests, comparison, decision, disclaimer, integrations, mobile-shell, news, onboarding, ops, paper, policies, replay, risk, signup, universe) | Same as 31 — they exist and never ran during my gates |
| 33 | next.config.js | "No `next.config.js` exists in the repo" (Phase 4 / 10 reports) | `frontend/next.config.js` exists with `experimental.instrumentationHook` + a `rewrites()` block proxying `/api/*` to localhost:8000 for local dev | The **`redirects()` block** for the IA rename (Phase 2 migration map) is what's missing — not the file. Adding redirects is still deferred per row 14 |

## D. Test, accessibility and verification gaps

| # | Gap | Notes |
|---|---|---|
| 34 | E2E suite not run at any UX-phase gate | See row 31. 20 specs ready. CI cost is real (`next build` + browser); decide whether to wire into a pre-push hook or accept "run on operator's machine before push" |
| 35 | No screenshot matrix captured (Phases 3 → 16) | Five `_NOT_CAPTURED.md` markers under `DOCS/handoff/screenshots/`. Local `npm start` did not bind in the polling window across multiple attempts on this Windows host. Production-side Playwright capture against Railway URLs is the realistic next step |
| 36 | `@axe-core/playwright` installed but no test consumes it | Phase 12 / J.3 — no automated a11y CI. Manual contrast spot-check only |
| 37 | No production a11y sweep run | Phase 13 / I.2 — `npx axe` against `https://frontend-production-7e8b1.up.railway.app/` not done |

## E. Honest-data residuals

| # | Place | Honest residual |
|---|---|---|
| 38 | `/decision` risk-overlay panel | When backend exposes no `portfolio_risk_score` + no `constraints_applied` + no `adjustments`, the panel reads "Risk overlay ran but reported no constraints, score, or adjustments for this recommendation." Honest, not a placeholder |
| 39 | Home `ResearchAssistantPreview` | Five guided-prompt rows deep-link to `/operator?surface=manual&prompt=…`. No in-app LLM call until row 17 + row 27 close |
| 40 | Notifications panel | "Mark all read" persists only in `localStorage` per-user-email (no backend write); badge count resets to current items the moment they re-fetch | 
| 41 | Operator console | Sole canonical assistant flow until row 17 lands |
| 42 | Frontend recents-searches | `localStorage` only, per-browser, per-device |
| 43 | Cache layer | Module-level in-memory; per-process. Multi-instance Railway scaling would invalidate the cache savings per instance |

## F. Open infrastructure-ish items

| # | Item | Notes |
|---|---|---|
| 44 | Finnhub API key rotation | The key surfaced in CLI output during Phase 16.2 diagnosis. Hygiene step: rotate at `finnhub.io/dashboard`, update Railway var. Not blocking |
| 45 | Pre-push hooks (forbidden language, typecheck, tests) | Phase 1 quick-win Q-3 explicitly deferred. No hook installed |
| 46 | Per-tab persistence on TopBar layout flag | `finrlx-topbar-v3` is browser-local. When a backend user-prefs surface lands, swap the storage layer |
| 47 | Operator-curated fundamentals (failover) | If Finnhub goes down or coverage misses a ticker, the panel shows the honest empty state. No fallback chain to a second provider |

## G. Items I deliberately scoped OUT (not gaps, but worth listing)

| # | Item | Why out of scope |
|---|---|---|
| X-1 | Real broker integration / live order routing | Plan §0 rule 3 — FINRLX is decision-support, not a broker |
| X-2 | Multi-tenant white-label theming | Single-tenant only |
| X-3 | New chart library (replace Recharts) | Existing components sufficient for Phases 3–16 |
| X-4 | Marketing site / landing page | Not in this redesign program |

---

## Summary by severity

| Severity | Count | Examples |
|---|---|---|
| **High** | 0 | (No high-severity blockers remain after Phase 16.) |
| **Medium** | 12 | Decision page restructure (3–6); embedded assistant (17); Forward P/E (21); Watchlist/portfolio news filter (11); IA migrations (3, 4, 5, 6); analyst consensus (22); palette recommendations (24); incidents progressive disclosure (16) |
| **Low** | 16 | Mostly cosmetic / typography / redirects / OS-glyph / cache scaling / rotation |
| **Documented errors I made** | 3 | Playwright (31), e2e tests (32), next.config.js (33) |
| **Test/a11y/screenshot gaps** | 4 | rows 34–37 |
| **Backend stubs** | 4 | LLM (27), notifications (28), Google OAuth (29), Sentry (30) |
| **Honest residuals (not bugs)** | 6 | rows 38–43 |
| **Out of scope** | 4 | rows X-1 to X-4 |
| **Closed (here for completeness)** | 1 | Saved views (row 26) |

**Total items surveyed: 50.**

---

## Recommended near-term ordering (my opinion; you decide)

If you wanted to chip away at the medium-severity list, the order I'd
go in:

1. **Row 34 — run the e2e suite once on `main`.** Establishes a real
   baseline. Until I know what's green and what's red, I'm guessing.
2. **Row 21 — Forward P/E.** Either accept the empty tile (one-line
   doc update) or upgrade Finnhub. Decision step, not engineering.
3. **Row 17 — embedded assistant inside `/operator`.** Largest UX
   win, and the backend stubs (row 27) are ready to flip the moment
   an `LLM_PROVIDER` env var lands.
4. **Row 3 — `/decision/[id]` deep linking.** Unlocks shareable URLs
   for specific recommendations.
5. **Row 14 + 15 + 10 + 7 (the IA-migration bundle).** Land
   `next.config.js redirects()`, then `/portfolio` tabbed landing,
   then `/insights` rename. Best done as one Phase 17 because they
   share infrastructure.
6. **Row 24 — recommendations in the command palette.** Small but
   high-value for navigation.
7. **Rows 35 + 36 + 37 — screenshot + a11y matrix.** Easier from a
   production URL than the flaky local `next start`.

Everything else is "Low severity" — polish that can wait until you
have a quiet day.

---

## What I would NOT recommend right now

- **Row 1 / 15.6 — v2 TopBar deletion** until you've used v3 for a
  full working session and confirmed nothing about it bothers you.
- **Row 22 (analyst consensus) / Row 21 (forward P/E)** if it means
  jumping to a paid Finnhub plan you don't otherwise need.
- **Row 2 — multi-account session** until there's a real second-
  account use case (e.g. a co-analyst sharing a desktop).
- **Row 33-related — adding next.config.js redirects in isolation**
  without their target sub-routes. The IA-migration bundle (item 5
  above) is the right framing.
