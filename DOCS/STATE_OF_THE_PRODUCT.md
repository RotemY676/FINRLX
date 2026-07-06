# STATE OF THE PRODUCT — living index (Program LEAP)
Updated: 2026-07-06 · Phase: F0 · Maintained per gate U6 (every merged PR updates this file).

## Product modes (target per plan v3.0)
- Simple Mode (`/`, ticker → 360° dossier): NOT STARTED (S1–S6)
- Pro Mode (`/pro/*`): NOT STARTED (S7); all current surfaces remain at legacy routes

## Shipped and real (verified in code at branch point 4d5ce7d)
- Signal engines: technical_momentum, risk_quality, news_sentiment (ml_return_forecaster = STUB)
- Decision pipeline + publication gates + provenance + replay determinism
- Paper portfolios + FX handling + freshness watchdog (fx_freshness.py)
- News/sentiment ingestion; EDGAR filings; Finnhub fundamentals
- Single-ticker analysis engine + /analyze wizard with offline HTML report
- Daily DAG scheduler (jobs/daily_dag.py); notifications service
- Shadow-RL research container (research/finrlx_cpu; PPO/A2C; not_eligible_for_promotion)
- Operator console, universe CRUD with soft-delete provenance, onboarding wizard

## Stubbed / flagged / deferred (from FINRLX_UNIMPLEMENTED_FUNCTIONALITY_AUDIT.md)
- ml_return_forecaster: STUB → planned real in S4
- Decision page deep links / audit drawer / gate checklist / hero split: DEFERRED → S7
- IA consolidation + /news→/insights: DEFERRED → S7 (as /pro migration)
- News "why this matters" + assistant: STUB → S9
- Authenticated a11y sweep: NEVER RUN → F3
- Trading calendar: LANDED (watchdog integrated; 2 call-sites pending)
- Price provider chain: LANDED backend (yfinance→stooq→cache, provenance, quality flags, watchdog); UI pending

## LEAP phase ledger
| Phase | Status | PR | Report |
|---|---|---|---|
| F0 bootstrap | DONE | leap/F0-bootstrap | PHASE_LEAP_F0_REPORT.md |
| F1 provider chain | BACKEND DONE (UI badges + flag flip in RESUME.md) | leap/F0-bootstrap | PHASE_LEAP_F1_REPORT_PARTIAL.md |
| F2 trading calendar | CORE DONE (ingest+backtest call-sites in RESUME.md) | leap/F0-bootstrap | PHASE_LEAP_F2_REPORT_PARTIAL.md |
| F3, S1–S9, C1 | NOT STARTED | — | — |

## Feature flags
(none yet; D23 registry starts here)
