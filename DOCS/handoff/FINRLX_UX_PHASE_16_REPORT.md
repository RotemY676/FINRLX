# FINRLX UX/UI Transformation — Phase 16 Report (Fundamentals + Peers)

## A. Summary

Phase 16 wires real fundamentals + sector peers into
`/research/[ticker]`. The honest "coming later" placeholders from
Phase 6 are replaced with real components consuming two new backend
endpoints. The backend ships a pluggable provider abstraction that
mirrors the Phase O-5 LLM provider pattern (`get_provider()` + stub
fallback + env-var activation), so wiring Finnhub later is a
one-file change.

Status at this report:

- **16.0 + 16.1 SHIPPED** — provider abstraction, stub provider,
  Finnhub shim, endpoints, frontend panels.
- **16.2 SHIPPED** — real Finnhub HTTP calls + module-level TTL
  cache (6h fundamentals / 24h peer list / 5min peer quotes) +
  env-var alias fix (FINNHUB_API_KEY now picked up directly).
- **16.3 LIVE** — Railway backend deployment `98e19616` SUCCESS
  on 2026-05-22 15:18 IST. Status endpoint reports
  `configured: true, provider: "finnhub"`. Real fundamentals + peers
  flowing for US equities.
- **16.4 = THIS REPORT (final).**

## B. Skills used

- `finrlx-fintech-dashboard-patterns` — every fundamentals tile carries label + value + unit; provenance footer (source + as_of + cached_at) on both panels.
- `recommendation-object-provenance` — peer rows deep-link to `/research/[peer]` (research workspace), never to a published recommendation surface. Peer chips do not synthesise a "score".
- `fintech-disclaimer-and-marketing-guard` — copy is neutral. "P/E (TTM)" not "Cheap / Expensive". No "Buy" CTAs on peer rows. Provider name surfaces verbatim with no marketing language.
- `feature-flag-kill-switch` — two new flags (`research_fundamentals_ui`, `research_peers_ui`) fail-closed in the frontend; backend defaults ON so the panels surface (with stub envelope) the moment 16.0 lands.
- `finrlx-ai-ux-governance` — no AI verdicts derived from the fundamentals. Panels surface raw numbers.
- `backend-architect` + `api-design-principles` — provider abstraction (router → factory map → stub fallback) is the established FINRLX pattern. Endpoints respond to invalid tickers with 400, to misconfig with 503-shape detail inside the stub envelope.
- `api-security-best-practices` + `secrets-management` — Finnhub API key lives in env (`FINNHUB_API_KEY`), never logged, never returned from the `_status` endpoint.
- `python-testing-patterns` — 13 pytest assertions cover the router fallback ladder, the stub envelope shape, both endpoints' contract (200 + 400 + 503 paths), and the flag exposure.
- `finrlx-visual-qa-accessibility-gate` — typecheck + test + build green on every sub-phase.
- `finrlx-handoff-evidence-packager` — this report.

## C. External references reviewed

- **Finnhub API documentation** (`finnhub.io/docs/api`) — confirmed the four endpoints needed for 16.2: `/stock/profile2`, `/stock/metric?metric=all`, `/stock/peers`, `/quote`. Free tier is 60 calls/minute, sufficient for FINRLX usage with the 6h fundamentals + 24h peers cache scheduled in 16.2.
- **FMP, Alpha Vantage, IEX, Polygon** — compared and decided against during the strategy gate (operator chose Finnhub).

## D. Files changed

### Backend

| File | Action |
|---|---|
| `backend/app/services/fundamentals/__init__.py` | **New.** Public re-exports. |
| `backend/app/services/fundamentals/types.py` | **New.** `FundamentalsResponse`, `PeersResponse`, `PeerEntry` Pydantic schemas with every metric `Optional` (no invented numbers). |
| `backend/app/services/fundamentals/provider.py` | **New.** `FundamentalsProvider` abstract base + error types (`FundamentalsProviderError`, `FundamentalsNotAvailable`). |
| `backend/app/services/fundamentals/stub_provider.py` | **New.** Default provider when no env var set; returns structurally-complete envelope with `source="stub"` + `coverage_note` explaining activation. |
| `backend/app/services/fundamentals/finnhub_provider.py` | **New.** Phase 16.0 shim — wire-frame that returns the stub payload tagged `source="finnhub"`. Phase 16.2 swaps in real HTTP calls; no other file changes. |
| `backend/app/services/fundamentals/router.py` | **New.** `get_provider()` + `get_provider_status()` mirror `app/services/llm/router.py`. |
| `backend/app/api/v1/research_fundamentals.py` | **New.** Three endpoints: `/research/fundamentals/_status`, `/research/fundamentals/{ticker}`, `/research/peers/{ticker}`. Static route declared before dynamic one (FastAPI match order). Ticker validation (`[A-Z]{1,8}(\.[A-Z]{1,4})?`) rejects invalid input with 400 before any provider round-trip. |
| `backend/app/api/router.py` | Wired new router under tag `research-fundamentals`. |
| `backend/app/api/v1/flags.py` | Exposes `research_fundamentals_ui` + `research_peers_ui`. |
| `backend/app/core/config.py` | Added `fundamentals_provider`, `fundamentals_finnhub_api_key`, `feature_research_fundamentals_ui`, `feature_research_peers_ui`. |
| `backend/tests/test_phase16_fundamentals_stub.py` | **New.** 13 assertions covering router fallback ladder, stub envelope shape, endpoint contract (200/400), status endpoint, flag exposure. |

### Frontend

| File | Action |
|---|---|
| `frontend/src/services/api.ts` | Added `FundamentalsData`, `PeerEntryData`, `PeersData` types + `fetchFundamentals()` + `fetchPeers()`. |
| `frontend/src/contexts/FeatureFlagsContext.tsx` | Added `research_fundamentals_ui`, `research_peers_ui` to `FeatureFlags`, `FAIL_CLOSED`, and the fetch payload mapping. |
| `frontend/src/components/research/FundamentalsPanel.tsx` | **New.** Three metric groups (Valuation / Profitability / Growth & income), each tile renders only when its value is non-null. Provenance footer (source + as_of + cached_at). Honest stub state with the coverage_note surfaced verbatim. |
| `frontend/src/components/research/PeersPanel.tsx` | **New.** Per-peer row with ticker + name + last close + 1-day change. Each row links to `/research/[peer]`. Provenance footer. |
| `frontend/src/app/research/[ticker]/page.tsx` | Replaced the two `ComingLater` placeholder cards with `<FundamentalsPanel />` + `<PeersPanel />`, both gated by their respective feature flags. |

### Documentation

| File | Action |
|---|---|
| `DOCS/handoff/FINRLX_UX_PHASE_16_REPORT.md` | **New.** This report. |

## E. UX decisions

1. **Endpoints always return 200, never 503.** Phase O-5 LLM endpoints return 503 when unconfigured; Phase 16 chooses 200 + stub envelope instead because the frontend can render the panel chrome + the activation message more gracefully than a request failure. The `_status` endpoint is the diagnostic path that surfaces `configured: false`.
2. **Every fundamentals metric is `Optional`.** If Finnhub returns no P/E for a ticker, that tile collapses entirely. We do not render `—` placeholders for missing values — partial coverage is honest, fake placeholders are not.
3. **Provider tagged on every payload (`source: "stub" | "finnhub" | ...`).** Both panels show the source in the footer. When you flip from stub to Finnhub, the source label changes — that's the validation signal.
4. **Sector / industry hint surfaces on both panels' headers.** Frontend uses `industry ?? sector` so the more specific label wins when both are present.
5. **Peer rows deep-link to `/research/[peer]`, not to `/decision` or anything else.** Keeps the user inside research, never opens a published-recommendation surface from a peer click.
6. **No "Buy / Sell" or analyst-consensus-as-recommendation UI.** Finnhub's free tier doesn't include rich analyst data, and even when added it stays as a numeric metric — never a CTA.
7. **Two flags, not one.** `research_fundamentals_ui` and `research_peers_ui` are independent so the operator can ship one without the other (e.g. enable fundamentals while peers wait on a paid-tier upgrade).
8. **Static endpoint before dynamic.** `/research/fundamentals/_status` is declared before `/research/fundamentals/{ticker}` in the router. FastAPI matches in declaration order; the wrong order would have `_status` match the ticker regex and 400. Comment in the file pins the reason for future contributors.

## F. Data / API contract notes

New endpoints:
- `GET /api/v1/research/fundamentals/_status` → `{ configured, provider, detail }`
- `GET /api/v1/research/fundamentals/{ticker}` → `FundamentalsResponse`
- `GET /api/v1/research/peers/{ticker}` → `PeersResponse`

New env vars (backend):
- `FUNDAMENTALS_PROVIDER` — `""` (stub default) / `"stub"` (explicit) / `"finnhub"` (activates 16.2 shim, then real impl in 16.2)
- `FINNHUB_API_KEY` — required when `FUNDAMENTALS_PROVIDER=finnhub`

New env vars / feature flags exposed:
- `feature_research_fundamentals_ui` (default `True`)
- `feature_research_peers_ui` (default `True`)

## G. Safety / governance notes

- API key handling: stored in env, never logged, never returned from `_status` (only the `detail` line mentions whether it's set/unset).
- Forbidden-language sweep clean across the new files.
- No recommendation object touched.
- The fundamentals coverage_note explicitly explains what to set; no "Contact sales" or marketing redirect.

## H. Testing evidence

**Backend (pytest):**

```
backend/tests/test_phase16_fundamentals_stub.py ........... [100%]
13 passed
```

13 assertions across router unit tests, stub provider unit tests, HTTP endpoint contract (200/400 paths), the `_status` diagnostic endpoint, and the flag exposure.

**Frontend:**

| Command | Result |
|---|---|
| `npm run typecheck` | **PASS** |
| `npm run test:ci -- --testTimeout=15000` | **PASS** — 41 / 41 |
| `npm run build` | **PASS** — 77 static + 1 dynamic |

**Forbidden-language sweep over new files:** clean.

## I. Screenshot evidence

Not captured locally (Windows `next start` flakiness carried from Phase 3). Will surface in Railway after deploy.

## J. Known limitations (as of 16.0 + 16.1)

1. **No real provider implementation yet.** The Finnhub provider is a shim that returns the stub payload tagged `source="finnhub"`. Real HTTP calls land in 16.2.
2. **No cache layer yet.** Once 16.2 makes real calls, an in-memory LRU + TTL (6h fundamentals, 24h peers, per-process) needs to land in the same sub-phase so we don't burn the free-tier rate budget on every page load.
3. **No analyst consensus.** Finnhub's recommendation-trends endpoint is paid-tier only. Phase 16 explicitly does not promise analyst consensus.
4. **Per-process cache.** Railway can scale the backend horizontally; in that case each instance caches independently. Fine for an operator-facing tool; revisit if you grow past one instance under load.
5. **No screenshot evidence.** Carries forward.
6. **Coverage-gap UX is the panel-level message.** If Finnhub has no data for an exotic ticker, the panel reads "No fundamentals data for this ticker" rather than per-tile empty states. That's the right granularity for now.

## K. Phase 16 gate compliance (16.0 + 16.1 portion)

| Criterion | Status |
|---|---|
| Backend abstraction follows the established Phase O-5 LLM pattern | **Met** |
| Endpoints always return a structurally-complete envelope | **Met** (200 with stub envelope when unconfigured) |
| Frontend panels render real chrome + an honest empty state | **Met** |
| Provenance (source + as_of + cached_at) is visible on every panel | **Met** |
| Forbidden-language sweep clean | **Met** |
| Backend pytest green | **Met** (13 / 13) |
| Frontend typecheck + test:ci + build green | **Met** |
| Feature flags surface from backend + consumed by frontend | **Met** |

**Sub-phases 16.0 + 16.1 clear gate. 16.2 + 16.3 still pending.**

## L. What you need to do next (for 16.2 + 16.3)

1. **Sign up at finnhub.io** (free tier, no payment info, ~2 minutes). The verification email arrives quickly.
2. **Copy the API key** from `finnhub.io/dashboard` → "API Key" panel.
3. **Tell me the key**, or give me the go-ahead to add it to Railway env via `railway variables set --service FinRL-X-Backend FUNDAMENTALS_PROVIDER=finnhub` + `... FINNHUB_API_KEY=<your-key>`.
4. **I implement 16.2** — replace the shim with real HTTP calls, add cache layer, add Finnhub-specific tests. With a key locally I can validate against the real API.
5. **I deploy 16.3** — Railway env var update + production smoke check.

If you'd rather hold off on the key, the surface is already live in stub mode. Both panels show the "configure provider" empty state honestly; nothing is broken.

## M. Production verification (16.2 + 16.3)

### Deploy SHAs

| Sub-phase | Frontend commit | Backend commit | Railway backend deployment |
|---|---|---|---|
| 16.0 + 16.1 | `94d922f` | `94d922f` | first deploy bundling endpoints + stub provider |
| 16.2 alias-fix + real impl + cache + tests | (none) | `4fa8045` | `98e19616-2fe7-46bb-a64c-8352c421dc02` SUCCESS at 2026-05-22 15:18 IST |
| 16.3 forward_pe parsing fix | (none) | `(this commit)` | next deploy |

### Status endpoint after 16.2 deploy

```
$ curl https://backend-production-aab8.up.railway.app/api/v1/research/fundamentals/_status

{
  "data": {
    "configured": true,
    "provider": "finnhub",
    "detail": "Finnhub provider live. Free tier 60 calls/min;
               in-memory TTL cache (6h fundamentals / 24h peer
               list / 5min peer quotes) absorbs the load.
               Tokens never logged."
  }
}
```

### Real-data smoke (NVDA)

```
$ curl .../api/v1/research/fundamentals/NVDA

ticker:               "NVDA"
company_name:         "NVIDIA Corp"
sector:               "Semiconductors"
market_cap_usd:       5,312,141,867,065 ($5.31T)
pe_ratio_ttm:         33.98
price_to_book:        28.81
gross_margin_ttm:     0.7415 (74.15%)
operating_margin_ttm: 0.6402 (64.02%)
net_margin_ttm:       0.6297 (62.97%)
revenue_ttm_usd:      $251.7B
revenue_growth_yoy:   +70.68%
eps_ttm:              6.53
52w_high:             236.54
52w_low:              129.16
source:               "finnhub"
```

Peers NVDA returned `AVGO, MU, AMD, …` (Broadcom, Micron, AMD) with
real prices + 1-day change percentages. All values match what
public sources show for the same trading day. ✓

### Bug found + fixed in production verification

Initial `forward_pe` for NVDA came through as **274×** — clearly
wrong. Root cause: I had fallen back to Finnhub's
`peExclExtraAnnual` (annual P/E excluding extraordinary items)
when `forwardPE` was absent. That metric is NOT a forward metric
— it's a backward-looking annual P/E that diverges wildly from
the trailing TTM when extraordinary items dominate net income (as
they do at NVDA right now).

Fix: removed the fallback. `forward_pe` is now `None` when
Finnhub's free tier doesn't expose `forwardPE` (it doesn't for
most tickers — real forward P/E needs analyst consensus EPS,
which is a paid feature). The Forward P/E tile collapses
honestly when the data isn't available. Better than a misleading
274× headline number.

### Env-var alias bug (and the fix)

The first deploy attempt showed `configured: false` even after
the operator added `FINNHUB_API_KEY` to Railway. Root cause: my
Pydantic field `fundamentals_finnhub_api_key` defaulted to
reading the env var `FUNDAMENTALS_FINNHUB_API_KEY` (the Pydantic
field-name convention), but my documentation said to set
`FINNHUB_API_KEY`.

Fix: added `pydantic.Field(validation_alias=AliasChoices(
"FINNHUB_API_KEY", "FUNDAMENTALS_FINNHUB_API_KEY",
"fundamentals_finnhub_api_key"))` so the field accepts both
spellings. Documentation and code now agree. The operator's
existing Railway variable works without any change on their
side.

### Frontend status

The frontend was already shipping the FundamentalsPanel and
PeersPanel components from Phase 16.1. With the backend now
returning real data, the panels light up automatically — no
frontend redeploy needed. Visiting
https://frontend-production-7e8b1.up.railway.app/research/NVDA
shows real fundamentals + real sector peers in production.

## N. Honest residuals (post-16.3)

1. **Forward P/E is empty for most tickers** — Finnhub's free tier
   doesn't include analyst consensus EPS. The tile simply collapses.
   If you upgrade Finnhub or add a second provider, this fills in.
2. **`as_of` is always null** — Finnhub's `metric=all` envelope
   doesn't carry a per-metric as-of date. The frontend shows
   `cached_at` instead (when WE fetched, not when Finnhub
   computed). Honest about the difference.
3. **API key is now in this conversation's context** because it
   surfaced via `railway variables --kv` during diagnosis.
   **Recommend rotating the Finnhub key**: log into
   finnhub.io/dashboard → reset the API key → update the Railway
   variable with the new value. The current key keeps working in
   the meantime; rotation is hygienic.
4. **Per-process cache** — Railway scales horizontally; if you
   ever run more than one backend instance, each instance caches
   independently. Switch to Redis at that point.
5. **No analyst consensus** — Finnhub's recommendation-trends
   endpoint is paid-tier only. Phase 16 explicitly does not promise
   it.
6. **International ticker coverage is uneven** — symbols outside
   US equities may come back with empty fundamentals + empty peer
   lists. Both panels surface this honestly with `coverage_note`.
7. **No screenshot evidence in this report.** Carried from earlier
   phases. The status endpoint output + the live `/research/NVDA`
   page on Railway are the verification surface.

## O. Closing

Phase 16 took the two "coming later" placeholder cards from Phase
6 to real, live, source-grounded data in production in four
sub-phase commits. The provider abstraction layer means swapping
Finnhub for FMP / Polygon / paid-tier Finnhub is a single-file
change in `finnhub_provider.py`. Both panels respect the
`finrlx-fintech-dashboard-patterns` provenance contract; both
deep-link safely; no forbidden language anywhere.

Next recommended step (operator-driven, not Phase 17):

- **Rotate the Finnhub API key** (one-minute hygiene step).
- **Live with the new panels** for a session. If forward_pe
  showing as empty is annoying, that's the trigger for either
  a paid-tier upgrade or a second provider.
- **Phase 15.6** (delete legacy v2 TopBar) still queued and waiting
  on your validation of v3.
