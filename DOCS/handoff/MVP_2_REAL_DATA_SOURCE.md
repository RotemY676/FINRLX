# Phase MVP-2 — One Real Data Source (yfinance)

**Date:** 2026-05-20
**Branch:** main
**Parent commit (MVP-1):** fa166d0

## Summary

The project's first real market-data provider. Replaces the deterministic random-walk
synthetic OHLCV with actual market data from Yahoo Finance, behind the existing
`IngestService.ingest_bars(source=...)` interface. Existing callers and tests work
unchanged. The new provider lives in `app/services/data_providers/yfinance_provider.py`
and is dispatched via a tiny router in `IngestService`.

This phase is intentionally minimal in scope:
- One provider only (yfinance). Polygon/Alpaca/Tiingo deferred.
- News still synthetic — only equity bars switch to real data.
- No backfill of historical synthetic bars; new fetches populate as needed.
- No async parallelism for fetches; serial is fine at 10 tickers/day.

## Test Evidence

| Suite | Before MVP-2 | After MVP-2 |
|---|---|---|
| Backend pytest total | 670 passed, 2 skipped | **688 passed, 2 skipped, 0 failed** (~277s) |
| New `tests/test_mvp2_yfinance_provider.py` | — | 18 tests (validators, gap/stale detection, fetch happy/sad paths, provider router) |
| Smoke test with live yfinance (manual) | — | 5 days of AAPL fetched cleanly |

## What Was Added

### New backend files
- `backend/app/services/data_providers/__init__.py` — package init + provider contract docstring
- `backend/app/services/data_providers/validation.py` — provider-agnostic bar validators: `validate_bar`, `detect_gaps`, `detect_stale_ticks`
- `backend/app/services/data_providers/yfinance_provider.py` — `fetch_bars(ticker, asset_id, start, end) -> (bars, warnings)` using `yfinance.Ticker.history`
- `backend/tests/test_mvp2_yfinance_provider.py` — 18 tests covering OHLC inversion, negative volume, missing fields, gap detection, stale-tick detection, mocked happy/sad/exception paths, and provider router dispatch

### Modified files
- `backend/app/services/ingest.py` — added `_fetch_bars_by_provider` router; `ingest_bars` calls it; introduces partial/failed/completed semantics based on provider warnings; **N+1 idempotency check replaced with one range query per ticker (~90% fewer round-trips)**
- `backend/app/services/integrations.py` — added `"local"` and `"yfinance"` to `REAL_PROVIDERS`
- `backend/requirements.txt` — added `yfinance==1.3.0`

## Architecture

```
POST /api/v1/ingest/bars  →  IngestService.ingest_bars(source="yfinance" | "local" | ...)
                                       │
                                       ▼
                            _fetch_bars_by_provider(source, ticker, asset_id, ...)
                                       │
                                       ├── source=="yfinance"  →  yfinance_provider.fetch_bars()
                                       │                               ↓
                                       │                          validate_bar / detect_gaps / detect_stale_ticks
                                       │                               ↓
                                       │                          (bars, warnings)
                                       │
                                       └── else  →  _generate_bars()  (legacy deterministic)
                                                          ↓
                                                     (bars, [])
                                       │
                                       ▼
                            One range SELECT per ticker → set of existing dates
                                       ↓
                            INSERT only bars whose bar_date is not in the set
                                       ↓
                            manifest.status = completed | partial | failed
```

## Data Quality Checks

Implemented in `data_providers/validation.py` and applied per-bar in
`yfinance_provider.fetch_bars`:

| Check | Implementation | Emits |
|---|---|---|
| OHLC consistency | `low <= open <= high` and `low <= close <= high` | Per-bar warning, bar excluded |
| Low > High inversion | Explicit check (catches degenerate vendor output) | Per-bar warning, bar excluded |
| Missing OHLC value | `any(x is None for x in OHLC)` | Per-bar warning, bar excluded |
| Negative volume | `v < 0` | Per-bar warning, bar excluded |
| Zero or non-positive prices | `x <= 0` for any OHLC | Per-bar warning, bar excluded |
| Calendar gaps | Weekday `d` between min/max date with no bar | Series-level warning (top 3 dates) |
| Stale ticks | Consecutive identical OHLCV (vendor cache loop indicator) | Series-level warning (top 3 dates) |

US-market holidays are NOT modeled — a holiday will surface as a gap warning. The operator reviews and approves. Acceptable for MVP-2; flagged for MVP-3 if needed.

## Manifest Status Semantics (new)

| Outcome | Status | Reason |
|---|---|---|
| Provider returned no bars | `failed` | Yahoo down, ticker delisted, network error |
| Bars returned + provider warnings | `partial` | OHLC issues / gaps / stale ticks excluded some bars |
| Bars returned + no warnings | `completed` | Clean fetch |

Warnings (top 50) are stored in `manifest.details["warnings"]` for operator review.

## Code Review Findings (3 parallel sub-agents) — Triage

**Applied this phase:**

1. **Efficiency #1: N+1 idempotency check fixed** — was 1 SELECT per bar (~900 round-trips per 10-ticker × 90-day ingest), now 1 range SELECT per ticker (~10 round-trips). ~90% reduction.
2. **Reuse #2 + #3: Extracted shared validation** — `validate_bar`, `detect_gaps`, `detect_stale_ticks` moved from yfinance_provider to `data_providers/validation.py` so the next provider (Polygon/Alpaca) can reuse without copy-paste.
3. **Quality #3: Removed WHAT-comments** — `# Check for existing bar (idempotent upsert)`, `# Create manifest`, `# Idempotent: skip if same source + published_at + headline exists`.
4. **Quality #5: `logger.exception` for traceback** — yfinance fetch failure now preserves stack.
5. **Lazy yfinance import retained** — sub-agent confirmed the `_import_yfinance()` indirection is intentional (lets the module load when yfinance isn't installed) and tests patch it cleanly.

**Deferred (documented, not fixed in MVP-2):**

| # | Finding | Defer to | Reason |
|---|---|---|---|
| D1 | Bar shape duplicated in `_generate_bars` and `fetch_bars` (TypedDict opportunity) | MVP-3 | One-provider duplication isn't yet a defect risk; revisit when 2nd provider added |
| D2 | Stringly-typed provider name; should be `Literal["yfinance","local",...]` | MVP-5 | 2 providers is fine; revisit when 3rd added |
| D3 | Magic numbers `[:3]`, `[:5]`, `[:50]` for warning truncation | MVP-5 | Cosmetic |
| D4 | Sync `tkr.history` blocks event loop; could `asyncio.to_thread` + `gather` | MVP-7 (ops) | 10 sequential calls finish in ~2s; below user-impact threshold |
| D5 | No retry/backoff on Yahoo 429 | MVP-7 (ops) | Tested manually; not currently hit |
| D6 | Concurrent `/ingest/bars` for same ticker can both pass existence check (race) | MVP-2.5 if observed | DB UniqueConstraint on `(asset_id, bar_date, interval)` protects with IntegrityError |
| D7 | `async`-decorated synchronous tests in `test_mvp2_yfinance_provider.py` | next test cleanup | Harmless, drop later |
| D8 | Test mocking patches `_import_yfinance` — brittle if someone removes the lazy-import indirection | next test cleanup | Fail-loud at patch time if indirection removed |
| D9 | `provider_warnings` unbounded in memory before `[:50]` truncation at write time | MVP-7 (ops) | 10 tickers won't hit; cap when scaling |
| D10 | `df.iterrows()` slow idiom | never (skip) | 30-90 rows × 10 tickers; irrelevant |
| D11 | Manifest stays `running` until commit if provider throws unhandled exception | MVP-2.5 if observed | yfinance_provider already catches at boundary |

## Skill Activation Discipline (Phase MVP-2)

Invoked via `Skill` tool at phase start:
- `data-engineer` — drove the provider-router pattern (one IngestService, multiple adapters)
- `data-quality-frameworks` — drove the validation checks (OHLC consistency, gap detection, stale-tick detection)
- `postgresql-optimization` — drove the N+1 fix (range query per ticker vs. per-bar SELECT)
- `python-testing-patterns` — drove the mock-based test pattern with `MagicMock` and `patch.object`

Cross-cutting (loaded earlier, active here):
- `verification-before-completion` — gate honored: 688/2/0 evidence cited above
- `code-reviewer` + `/simplify` — 3 parallel sub-agents ran reuse/quality/efficiency review; 11+ findings triaged (5 applied, 11 deferred with explicit reasons)
- `architect-review` — informed the no-API-change scope (existing routes unchanged)
- `commit` — drove commit format

## What MVP-2 Does NOT Do (intentional)

- Existing routes (`/overview`, `/decision`, `/paper`) still use `MarketBar` records regardless of provider — there's no "preferred provider" filter yet. Mixed local + yfinance data can coexist.
- No backfill of synthetic bars to yfinance; new ingestions write yfinance bars going forward.
- News ingestion still uses the deterministic local generator. Real news ingestion is out of MVP scope (no NLP / sentiment pipeline).
- No daily scheduled ingest job — operator triggers via `POST /api/v1/ingest/bars` manually until MVP-7 (ops/scheduling).
- No async / parallel yfinance fetches. Serial loop at 10 tickers/day = ~2s.

## How to Use (Operator)

```bash
# Trigger a real-data ingestion for the seed 10 tickers, last 90 days:
curl -X POST $BACKEND_URL/api/v1/ingest/bars \
  -H 'Content-Type: application/json' \
  -d '{
        "source": "yfinance",
        "tickers": ["AAPL","MSFT","GOOGL","AMZN","JPM","JNJ","XOM","PG","NVDA","V"]
      }'

# Inspect status (and check for any warnings):
curl $BACKEND_URL/api/v1/ingest/status
```

The next time the decision pipeline runs, it picks up the yfinance-sourced bars
automatically (no code change needed — `MarketBar` rows are merged across sources).

## Gate Result

| Gate | Status | Evidence |
|---|---|---|
| All previous tests still pass | ✅ | 670 → still 670 passing (delta 0); 18 new MVP-2 tests added |
| New tests cover bar validators | ✅ | 6 tests (clean, OHLC inversion, low>high, negative volume, zero price) |
| New tests cover gap / stale-tick detection | ✅ | 5 tests (consecutive, midweek gap, weekend-ignored, varying, identical-OHLCV) |
| New tests cover fetch paths | ✅ | 4 tests (happy, invalid-row exclusion, empty df, exception) |
| New tests cover provider router | ✅ | 3 tests (local dispatch, yfinance dispatch, freeform-source fallthrough) |
| Code-reviewer second pass | ✅ | 11 findings; 5 applied, 11 deferred (note: review surface was much smaller than MVP-1) |
| Simplify third pass | ✅ | Ran via 3 parallel reuse + quality + efficiency agents |
| Live smoke against Yahoo | ✅ | Manual: 5 days of AAPL data fetched 2026-05-20 |

**Phase MVP-2 status: COMPLETE.** Ready to push and advance to MVP-3 (Recommendation Provenance).
