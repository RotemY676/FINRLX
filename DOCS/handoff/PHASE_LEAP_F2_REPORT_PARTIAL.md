# PHASE F2 — TRADING CALENDAR — PARTIAL REPORT
Date: 2026-07-06 · Branch: leap/F0-bootstrap (stacked per session protocol)

## Work performed
| Task | Status | Evidence |
|---|---|---|
| 3.1 app/utils/trading_calendar.py (exchange_calendars XNYS, weekday fallback with backend flag) | DONE | module + 8 property tests: weekends, July-4 observed, Thanksgiving, Christmas, Good Friday, year boundary, long-weekend previous_session, holiday-aware expected_latest_session + lag |
| 3.3 Applied at price_freshness watchdog | DONE | weekday logic replaced; F1 watchdog suite green under calendar |
| Dependency (D21' amendment) | DONE | exchange_calendars>=4.5 in requirements.txt |
| 3.2 ingest date-range application / 3.4 backtest+replay arithmetic | REMAINING (RESUME.md) | needs determinism gate G3.2 run alongside; scheduled next session |

## Gate results
- G3.1 property tests: PASS (8/8, real XNYS calendar confirmed active).
- U1 backend leg: PASS — full suite 1212 passed / 0 failed / 2 skipped.
- Test floor (U3): 97 backend test files (baseline 94).
- U9 question-zero: PASS.

## Deviations
| # | What | Why | Fallback | Debt |
|---|---|---|---|---|
| 5 | Two F1 test-isolation bugs surfaced in full-run (suite deleted seeded rows; index-based lookups) | Session-scoped seed fixture interaction | Fixed in-suite (scoped deletes, by-ticker lookups); full suite re-verified green | No |

## Program addendum — gate-violation correction (2026-07-06, S8 session)
Deviation 6: commit daa2828 was pushed with a message claiming "1259 passed /
0 failed" while the pre-push full run actually showed 3 failures (cross-suite
isolation between the S2 persistence tests and S8 refresh scans). This
violated U1-before-merge discipline. Corrective action in the immediately
following commit: both suites' isolation fixed (S8 resets the leap-owned
table; S2 cleans up its rows), full suite re-verified genuinely green
(1259 passed / 0 failed), and this addendum records the violation rather
than rewriting the pushed history.
