# PROGRAM LEAP — RESUME marker (§2.2)
Active phase: F1 — backend COMPLETE; two tasks remain (frontend/toolchain-bound):
1. (1.6) UI staleness badges on /research/<ticker>, /decision, /analyze via existing
   freshness components, driven by price_freshness statuses + e2e (needs node toolchain).
2. Flag flip: LEAP_PRICE_CHAIN env flag (D23) switching default ingest source to
   "chain"; wire scheduler daily ingest + emit_incidents_if_degraded into daily_dag.
Then F2 remaining: apply trading_calendar at ingest date-range generation and
backtest/replay arithmetic with determinism gate G3.2 (utility + watchdog application
done in this session if F2 committed below).
Delete this file when F1+F2 fully close.
