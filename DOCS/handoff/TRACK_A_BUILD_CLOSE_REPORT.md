# TRACK A — BUILD CLOSE REPORT (Analyst Desk)
Date: 2026-07-07 · Program LEAP v4.0 · Phases A1–A6 complete on `main`
(HEAD 0c49192, remote-verified each merge). Continuous council-gated
execution; zero operator questions (QZ enforced).

## What shipped
| Phase | Delivered | Evidence |
|---|---|---|
| A1 | SEC XBRL trends (keyless, D51), Finnhub insider-MSPR/filings-tone/similarity adapters; fundamentals/filings/insider real dossier sections; stance byte-identity regression | 594916b · +8 tests |
| A2 | Social lane (FINNHUB_PREMIUM gate + labeled mentions fallback), sign-based divergence, FinGPT E.7 artifact lane w/ agreement A/B | 9289e0d · +8 tests |
| A3 | FinRL ensemble E.6 contract: protocol-identity gate, re-deflated penalties, selection history + turbulence events; worker runner + state exporter | 1211990 · +5 tests |
| A4 | Regime band series (DEBT-S5-2 closed, rule-parity-tested), evidence-linked event markers, signal matrix (percentiles vs own history), split windows, 10 D42 section endpoints | 11a3e25 · +6 tests |
| A5 | `/pro/desk/[ticker]`: 10 streamed sections, mini-map, tournament arena, dual sentiment tape, XBRL rows, regime timeline; wording scan extended; 257KB first-load | 5869e2f · +13 DOM tests |
| A6 | Freshness-driven section revalidation (contract-tested), S8 alert surfacing, D49 no-loop machine enforcement | 0c49192 · +3 tests |

## Final gate state
Backend **1310 passed / 0 failed** (was 1267 pre-Track-A) · Frontend vitest
**67 passed / 0 failed** (13 files) · tsc + eslint clean · next build OK ·
desk route 7.31KB / 257KB first-load (< D27 300KB).

## Track-A KPIs (§D of plan v4.0)
KA1 12 desk surfaces render (10 streamed + header + disclaimer) — structural
tests; KA2 signal matrix = full computed feature set + percentiles — PASS;
KA3 arena shows splits/penalties/selection history — DOM-tested; KA4 dual
lanes + divergence — PASS (scored lane awaits E8); KA5 XBRL trends +
similarity delta — PASS; KA6 RL lab truthful in both E7 states — tested;
KA7 zero operator questions — PASS; **KA8 screenshots — PENDING V1**.

## Honest status of remaining work (all environment-bound, none code-bound)
This sandbox verifiably cannot run V1: Playwright browser install fails
(download blocked) and production hosts return `x-deny-reason:
host_not_allowed` (probed 2026-07-07). Therefore, per rule P3, **every visual
claim about the desk remains "visual sign-off pending"** until V1 executes in
a Claude Code environment: F3 sweeps, `leap-redirects.spec.ts`, desk
screenshot set, axe on `/pro/desk`, then tag `leap-v2`.
Operator items open: E1 (rotate exposed token + install CI), E7 (torch
research worker → activates real RL + FinGPT lanes), E8 (Finnhub social tier).

Tag `leap-track-a-build` marks this build-complete state.

## Addendum 2026-07-07 — CI incident (post-close)
A pre-existing `.github/workflows/ci.yml` (predates Program LEAP; runs ruff,
mypy, pytest, vitest, next build, and Playwright e2e) reported red on `main`.
Root causes and fixes at 073be872:
1. **Backend (41s, ruff):** 93 lint violations accumulated across the
   program's phases (our gates ran pytest/contract suites but never ruff) —
   cleared; including one REAL latent bug: `sys.exit` without `import sys`
   in single_ticker_analysis's yfinance-empty path, now a RuntimeError.
   ruff + mypy + full pytest (1310/0) green locally on CI's exact commands.
2. **Frontend (6m43s, e2e):** 17 Playwright specs predated the S7b `/pro`
   migration and asserted the Pro shell on `/` (now Simple Mode) —
   retargeted; `playwright test --list` compiles 47 tests / 21 files;
   typecheck + vitest(67/0) + build re-verified with CI's commands.
**Honest limits:** Playwright cannot execute in this sandbox and the PAT has
no Actions-read scope, so the next CI run is the arbiter. Residual risk:
content assertions inside pre-LEAP specs may have drifted beyond routing —
only CI execution reveals those. Process fix adopted: `ruff check` +
`mypy` + `playwright --list` join the local phase-gate checklist from now on.
