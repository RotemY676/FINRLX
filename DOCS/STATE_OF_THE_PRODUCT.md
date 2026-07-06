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
- ml_return_forecaster: REAL MODEL LANDED (ml_forecaster.py, regularized HistGBR, leakage-tested); engine wiring to model_predictions pending S2/S4 integration
- Decision page deep links / audit drawer / gate checklist / hero split: DEFERRED → S7
- IA consolidation + /news→/insights: DEFERRED → S7 (as /pro migration)
- News "why this matters": BACKEND LANDED (flag+provider+canary-gated, adversarial validator; dossier News card integration); assistant still stub
- Authenticated a11y sweep: NEVER RUN → F3
- Trading calendar: LANDED (watchdog integrated; 2 call-sites pending)
- Price provider chain: LANDED backend (yfinance→stooq→cache, provenance, quality flags, watchdog); UI pending

## LEAP phase ledger
| Phase | Status | PR | Report |
|---|---|---|---|
| F0 bootstrap | DONE | leap/F0-bootstrap | PHASE_LEAP_F0_REPORT.md |
| F1 provider chain | BACKEND DONE (UI badges + flag flip in RESUME.md) | leap/F0-bootstrap | PHASE_LEAP_F1_REPORT_PARTIAL.md |
| F2 trading calendar | CORE DONE (ingest+backtest call-sites in RESUME.md) | leap/F0-bootstrap | PHASE_LEAP_F2_REPORT_PARTIAL.md |
| S3 indicator pack | DONE (additive, replay-safe) | leap/F0-bootstrap | in F2/S-batch commits |
| S4 tournament core + ML leg | CORE DONE (adapters/integration in RESUME.md) | leap/F0-bootstrap | test suites test_leap_s4_* |
| S2 autopilot backend | DONE (pipeline+persistence+compare; UI pending) | leap/F0-bootstrap | test_leap_autopilot.py, test_leap_s2_persistence_compare.py |
| S8 background autonomy | DONE backend (DAG refresh + material-change incidents) | leap/F0-bootstrap | test_leap_s8_refresh.py |
| S9 sourced annotations | DONE backend (flag OFF by default; E3 key enables) | leap/F0-bootstrap | test_leap_s9_annotations.py |
| C1 prep | state-drift check wired into ci_gate | leap/F0-bootstrap | scripts/state_drift_check.py |
| S1 design sprint | DONE (spec + wireframes + copy deck; 2 council PASS verdicts, 4 findings fixed incl. stance-vocabulary mapping) | leap/F0-bootstrap | DOCS/design/*, council/S1_* |
| DEBT-S5-1 | OPEN — job-polling endpoint for real per-stage progress (v1 progress is indicative) | — | SIMPLE_MODE_SPEC.md §J1 |
| S5 One Screen | VERTICAL SLICE DONE at /simple (route flip to / lands with S7) | leap/F0-bootstrap | src/app/simple, src/lib/simpleStance*, wording test |
| S6 compare UI | DONE at /compare (council PASS; wording-test coverage extended) | leap/F0-bootstrap | src/app/compare |
| DEBT-S5-2 | OPEN — per-period regime band series for chart shading (backend) | — | DossierView.tsx note |
| S7a route flip | DONE — / is Simple Mode; command center at /pro; Pro switcher in both shells; council PASS | leap/F0-bootstrap | council/S7A_* |
| F3, S7b, C1 | remaining per RESUME.md (S7b buildable; sweeps env-blocked) | — | RESUME.md |

## Feature flags
(none yet; D23 registry starts here)
