# PROGRAM LEAP — RESUME marker (§2.2)
Completed through this session: F0; F1 backend (incl. LEAP_PRICE_CHAIN flag + DAG watchdog);
F2 core + opt-in calendar rebalances; S3 indicator pack; S4 core (tournament with
overfitting guard + regularized ML forecaster, leakage-tested).
Next tasks, in order:
1. S4 continuation: heuristic candidate pack adapters (momentum/mean-reversion/
   regime-filtered) bridging run_strategy mechanics to tournament CandidateFn;
   RL leg adapter via research-container artifacts (D35 fallback path);
   isolation regression test (GS4.4); D39 runtime budget test.
2. S2: autopilot.py stage runner + job API + dossier schema/migration + cache,
   composing single_ticker_analysis + tournament + S3 features.
3. F2 leftover: ingest date-range session filtering (low priority — providers
   already return traded days).
4. F1 leftover + all frontend phases (S1 wireframes, S5-S7): Claude Code with
   node toolchain + rotated token (E1, workflow scope).
Delete when S2+S4 close.
