# PROGRAM LEAP — RESUME marker (§2.2)
Active phase: F1 (price provider chain) — PARTIAL on branch leap/F0-bootstrap.
Completed: stooq_provider.py; chain_provider.py (late-bound, D1 order);
ingest "chain" source wiring; tests/test_leap_f1_provider_chain.py (11 pass);
full backend suite green (1194 passed).
Remaining F1 tasks, in order:
1. (1.3) Additive migration: per-bar provenance columns {fetched_at, chain_position, quality_flag} per D7/D8 + serializer exposure. Downgrade must be tested.
2. (1.4) Ingest validation quality_flag rules per D8 (suspect >40% move w/o corp action, duplicates, nonpositive) + exclusion from features + ops surfacing.
3. (1.5) Equity freshness watchdog generalizing fx_freshness.py, thresholds D6 (calendar-naive with TODO(F2) until F2 merges).
4. (1.6) UI staleness badges on /research/<ticker>, /decision, /analyze via existing freshness components + e2e (requires frontend toolchain — run in Claude Code).
5. Flip ingest default source to "chain" behind env flag LEAP_PRICE_CHAIN (D23), default ON after 1.3–1.5 land.
Gates outstanding: G1.2 (provenance assertion), G1.3 (badge e2e), G1.5 (smoke).
Delete this file in F1's final commit.
