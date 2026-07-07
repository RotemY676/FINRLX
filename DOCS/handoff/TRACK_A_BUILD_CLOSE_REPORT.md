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
