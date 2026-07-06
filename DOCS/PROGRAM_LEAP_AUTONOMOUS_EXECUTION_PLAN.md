# PROGRAM LEAP — Autonomous Step-Change Execution Plan for FINRLX

**Version:** 3.0 · **Date:** 2026-07-06 · **Supersedes:** v2.0 (same day)
**Companion:** `DOCS/handoff/FINRLX_DEEP_ANALYSIS_REPORT_2026-07-06.md`

**Changelog:**
v3.0 — Program re-centered on the **Simple-Mode Revolution**: ticker-in → automatic 360° research dossier out, zero configuration; new Autopilot Research Engine with automatic model tournament (heuristics + ML + shadow-RL candidates, auto-selected per ticker with overfitting guards); The One Screen as the default product; all manual/advanced surfaces migrated to a Pro area; agent + council development topology for Claude Code (§3); Question-Zero enforcement as a hard gate (§2.5); phases restructured F0–F3 / S1–S9 / C1; new KPIs; Decision Register extended to D40.
v2.0 — autonomy architecture, D1–D28, file-level phase specs, hardening track, KPIs.
v1.0 — initial program.

---

## 1. Product vision being executed (the "what")

**The simple user's entire contract with the system:** type a stock ticker. Nothing else. The system then autonomously:
1. Ingests prices (provider chain), news + sentiment, fundamentals, and filings for that ticker.
2. Computes the full technical vocabulary (returns, volatility, drawdown, MACD, RSI, regimes, turbulence).
3. Runs the **Autopilot Model Tournament**: candidate analysis models — rule-based heuristics, an ML return forecaster, and shadow-RL agents (PPO/A2C, small CPU configs) — are each walk-forward validated on that ticker's data cross-referenced with news signals; an **overfitting guard** (deflated-Sharpe-style penalty + train/validation divergence check) scores each candidate; the best-suited model is selected **fully automatically** and the choice is *explained*, not hidden.
4. Produces a **360° dossier**: one screen with verdict cards (Technical · News & Sentiment · Fundamentals · Model Insight), price chart with regime shading, evidence drill-ins, data-freshness stamps, and honest limitation labels.
5. Keeps it alive in the background: scheduled refresh, news-triggered re-analysis, notification on material change.
6. Supports **comparison**: 2–4 tickers side-by-side on the same dossier dimensions.

**The pro user** gets everything that exists today — decision pipeline, governance, policies, universes, paper portfolios, RL benchmarks, operator console — relocated intact under `/pro/*`. Simple Mode is the front door; Pro Mode is the workshop.

**Truthfulness constraints (non-negotiable, inherited):** dossiers are *research analysis*, not investment advice, and say so; model-tournament results show validation evidence and overfitting scores; RL candidates run as research models whose outputs appear in dossiers with full labeling — they **never** enter the governed recommendation/publication pipeline (the existing isolation invariant is preserved and regression-tested). "Automatic" never means "oracular": every automatic choice ships with its why.

---

## 2. Operating contract & autonomy architecture

Unchanged from v2.0 §§1–2 (seven-step phase loop, RESUME.md survivability, self-verification, deviation ledger, mechanical rollback, hard stops S1–S4) — with these additions:

### 2.5 Question-Zero rule (the operator's stated acceptance test)
The program passes only if it runs end-to-end **without a single question directed at the operator**. Enforcement is mechanical, not aspirational:
- **QZ-1:** The agent never asks the operator anything, in any channel. Every fork resolves via the Decision Register (§4) or its fallback.
- **QZ-2:** Gate on every PR: report + PR body contain no interrogative sentence addressed to the operator ("should we…?", "do you want…?", "?"-terminated requests). A `scripts/question_zero_check.py` linter scans PR bodies and reports; failure blocks merge.
- **QZ-3:** Genuinely undecidable items (money, external accounts, irreversible brand moves) do not become questions — they become **Blocked Reports** naming the single E-item that unblocks, and the agent proceeds to the next unblocked phase.
- **QZ-4:** The C1 close report certifies: zero questions asked across the program, with the deviations ledger as evidence of how forks were resolved instead.

---

## 3. Agent & Council topology (development is multi-agent inside Claude Code)

Claude Code supports spawning subagents; the program mandates this topology per phase. This is real delegation within a session — not theater — and every council verdict is a committed artifact.

### 3.1 Roles
| Role | Type | Charter |
|---|---|---|
| **Orchestrator** | main session | Runs the phase loop (§2.1); owns branch, merge, report; resolves conflicts strictly via the Decision Register |
| **Backend Builder** | subagent | FastAPI/services/migrations tasks; owns backend tests |
| **Frontend Builder** | subagent | Next.js/components tasks; owns vitest + Playwright specs |
| **Data/ML Builder** | subagent | Ingestion, features, tournament, research-container integration |
| **Council — Quant Skeptic** | review subagent | Attacks statistical validity: leakage, look-ahead, overfitting-guard correctness, calendar correctness; checklist Appendix F.1 |
| **Council — UX Critic** | review subagent | Attacks intuitiveness: can a novice complete ticker→insight with zero instruction? readability, mobile, empty/loading/error states; checklist F.2 |
| **Council — Truthfulness Auditor** | review subagent | Attacks claims: safe-language rules, advice-verb scan, isolation invariants, evidence-behind-every-number; checklist F.3 |
| **Council — Security/Ops Reviewer** | review subagent | Attacks robustness: secrets, injection surfaces on user-supplied tickers, rate-limit behavior, migration reversibility, job-queue failure modes; checklist F.4 |

### 3.2 Council protocol (per phase, mechanical)
1. Builders complete tasks → Orchestrator assembles the candidate diff.
2. Each council member runs its checklist **against the diff + live local run**, producing `DOCS/handoff/council/L<phase>_<role>_VERDICT.md`: PASS, or FAIL with the exact checklist items violated.
3. FAIL → Orchestrator routes fixes to builders. Maximum **3 review cycles**; if a checklist item still fails at cycle 3, apply D26 (minimal scope trim) and record the debt row — never escalate to the operator (QZ-1).
4. Merge requires **4 committed PASS verdicts** in the PR. This is gate **U8**, added to the universal gates.
Council checklists are objective (yes/no per item) precisely so deadlock cannot require human judgment.

---

## 4. Decision Register — v3.0 (D1–D40; D1–D28 carried from v2.0 unchanged unless amended)

Carried unchanged: D1 (price chain), D2, D3 (calendar), D4 (indicators), D6–D8 (staleness, provenance, ingest validation), D11–D12, D14–D15, D18 (RL never promotes to recommendations), D20, D22–D26, D28.
**Amended:** D5 (regime overlay now also feeds dossier regime shading); D9/D10/D13 superseded by D31/D33; D16 (annotations feed the dossier News card); D17 (shadow-RL benchmark machinery becomes the tournament's RL leg); D19 (unchanged: no rename); D21 amended below; D27 (budgets apply to Simple screens first).

**New decisions:**

| ID | Decision | Default | Fallback |
|---|---|---|---|
| D29 | Product modes | Simple Mode is `/` (default, no login required for a basic dossier; full features behind existing auth). Pro Mode = all current surfaces under `/pro/*`, feature-intact, 308s from legacy paths | — |
| D30 | Dossier is research, not recommendation | Dossiers live outside the governed recommendation/publication pipeline (like today's `/analyze`); disclaimer + "research analysis" labeling on every dossier; existing isolation invariants regression-tested | — |
| D31 | The One Screen layout | Hero: single ticker input (autocomplete via existing asset-search endpoint from Phase 20.3). Result: sticky summary bar (ticker, price, freshness, overall research stance with confidence trio) + four verdict cards (Technical / News & Sentiment / Fundamentals / Model Insight) + regime-shaded price chart + expandable evidence per card. One screen; drill-ins are overlays/drawers, never navigation away | <1024px: cards stack; summary bar collapses to two lines |
| D32 | Zero-config principle | No settings, horizons, or model choices exposed in Simple Mode. Sensible defaults are program constants (analysis window 3y daily; news window 30d; comparison max 4). Anything configurable belongs to Pro | — |
| D33 | Pro migration mapping | `/pro/decision`, `/pro/portfolio` (paper/risk/replay tabs), `/pro/research` (comparison/backtests tabs), `/pro/universe`, `/pro/ops` (policies/integrations/templates/operator tabs), `/pro/admin`; Simple↔Pro switcher in TopBar; legacy 308s seeded from the Phase 2 migration CSV | Route breaking >5 e2e specs → thin re-export + debt row |
| D34 | Autopilot pipeline contract | `POST /api/v1/autopilot/research {ticker}` → job id; job stages: `ingest → enrich(news,fundamentals,filings) → features → tournament → dossier`; per-stage progress via polling endpoint (reuse `job_runs.py` pattern); dossier persisted + cache keyed `(ticker, dataset_fingerprint, engine_config_version)`; warm cache serves instantly with freshness stamp | — |
| D35 | Tournament candidates v1 | (a) heuristic pack: momentum, mean-reversion, regime-filtered momentum; (b) ML: gradient-boosted return forecaster (scikit-learn `HistGradientBoostingRegressor`) on the D4 feature set + news-sentiment features — this **implements** the stubbed `ml_return_forecaster`; (c) shadow-RL: PPO + A2C smallest configs via the research-container path | Torch unavailable on the deployment → RL leg reports status `queued_for_research_run` with honest copy; tournament completes with (a)+(b). |
| D36 | Tournament scoring (overfitting guard) | Walk-forward: ≥3 expanding train/validation splits on trading-day windows (D3 calendar); score = validation Sharpe penalized by (train−validation) divergence + a deflated-Sharpe-style multiple-testing penalty across candidates; ties → simpler model wins (heuristic > ML > RL). Winner + full scoreboard + penalty breakdown persist into the dossier | <2y usable data → skip RL leg, label "insufficient history for RL candidates" |
| D37 | Model Insight card honesty contract | Card always shows: selected model, why (scoreboard excerpt), validation-vs-train divergence, overfitting penalty, "past performance ≠ future results" label; never a bare "AI says buy" | — |
| D38 | Background automation | Extend the existing daily DAG (`jobs/daily_dag.py`): refresh dossiers for tickers researched in last 30 days; news-delta trigger re-runs enrich+tournament stages only; material-change notification via existing `notifications.py` (thresholds: regime flip, tournament winner change, sentiment swing beyond policy constant) | Worker budget exceeded → refresh oldest-first within budget; log skipped set |
| D39 | Compute budget | Tournament ≤ 90s warm / ≤ 6 min cold per ticker excluding RL; RL leg ≤ 10 min small-config or degrade per D35 fallback; comparison reuses cached dossiers | — |
| D21′ | Dependency policy (amended) | Python additions allowed: `exchange_calendars`, `scikit-learn`. npm additions: none. Torch/SB3 remain research-container-only | scikit-learn install conflict → in-house ridge regression fallback for the ML leg, labeled |
| D40 | Ticker input safety | Server-side ticker validation against the asset table + strict pattern; unknown ticker → suggest-nearest via existing autocomplete; all user input treated as hostile (no shell/SQL/path interpolation — parameterized everywhere) | — |

---

## 5. Program map v3.0

### 5.1 Structure & dependencies
```
FOUNDATION            F0 ─► F1 ─► F2          F0 ─► F3
                       │     │     │
SIMPLE-MODE            ▼     ▼     ▼
REVOLUTION      S1 ─► S2 ─► S3 ─► S4 ─► S5 ─► S6 ─► S8
                                   │           
                            S7 (Pro migration; needs F0, S1) ─► S5 links to Pro
                            S9 (insights LLM; needs F0; feeds S5 News card)
CLOSE                 C1 (needs all merged)
OPTIONAL              M1–M4 unchanged from v2.0 §7
```
Numeric order F0→F3→S1→…→S9→C1 satisfies the graph.

### 5.2 Session budget: ~40–44 agent-hours ≈ 15 sessions (core), M-track +8.

---

## 6. Phase specifications v3.0

Universal gates U1–U7 (v2.0 Appendix C.1) + **U8 council verdicts (§3.2)** + **U9 question-zero linter** apply to every phase.

### FOUNDATION (carried from v2.0 with v3 adjustments)

**F0 — Bootstrap, guardrails, truth baseline** *(was L0, +additions)*
Tasks as v2.0 L0 (CI gate script, Actions workflow, production sweep delta, secrets scan, STATE_OF_THE_PRODUCT v1) **plus**: `scripts/question_zero_check.py` + CI wiring; council directory + checklist files (Appendix F) committed; agent-topology note in CONTRIBUTING.
Gates: G0.1–G0.4 (v2.0) + QZ linter self-test + council checklists committed. **2–3h.**

**F1 — Price provider chain** *(= v2.0 L1, unchanged)* — Stooq provider, chain resolver, per-bar provenance, quality flags, equity freshness watchdog, staleness UI. Gates G1.1–G1.5. **3h.**

**F2 — Trading calendar** *(= v2.0 L3)* — `trading_calendar.py`, applied at ingestion/watchdog/backtest+replay; property tests; determinism gate. **2h.**

**F3 — A11y verified closure** *(= v2.0 L2)* — residual contrast, Recharts titles, MDX links, 401 short-circuits, first authenticated sweep. Gates G2.1–G2.3. **2h.**

### SIMPLE-MODE REVOLUTION

**S1 — Simple Mode design sprint (spec before pixels)**
*Rationale:* the master plan forbids cosmetic rewrites; the One Screen needs a committed spec the council can audit against.
Tasks: (1.1) UX spec `DOCS/design/SIMPLE_MODE_SPEC.md`: user journey (type ticker → progress → dossier → drill-in → compare), the five master-plan questions mapped to screen regions, empty/loading/error/insufficient-data states, zero-config inventory proving D32; (1.2) low-fi wireframes (HTML, in `design/`) for: hero, progress state, dossier, comparison, mobile stack — using existing tokens only (D14); (1.3) copy deck for all labels/disclaimers passing safe-language scan; (1.4) component inventory: reuse map (ConfidenceBlock, PriceChartCard, PageLoading/Error/Empty, freshness components) vs. 4 new components max (SummaryBar, VerdictCard, EvidenceDrawer, TournamentScoreboard).
Gates: council UX Critic + Truthfulness Auditor PASS on the spec itself (pre-code review cycle); QZ; CI trivially green. **2h.**

**S2 — Autopilot Research Engine (backend orchestration)**
*Rationale:* generalize `single_ticker_analysis.py` (already: fetch_history, fetch_news, compute_features, composite_recommendation, run_strategy) into the staged async pipeline of D34.
Tasks: (2.1) `services/autopilot.py`: stage runner over the D34 contract with per-stage status + timing persisted via `job_runs.py` pattern; (2.2) `POST /autopilot/research` + `GET /autopilot/jobs/{id}` + `GET /autopilot/dossier/{ticker}` API; (2.3) dossier schema (Appendix E.4) + additive migration; cache per D34; (2.4) enrich stage wiring: news (existing), fundamentals (Finnhub path), filings summary (existing EDGAR services), each optional-degrading with per-section availability flags; (2.5) ticker validation per D40.
Gates: GS2.1 pipeline e2e on fixture ticker with all stages green; GS2.2 degradation matrix test (news down / fundamentals absent / filings absent → dossier completes with flagged sections); GS2.3 cache warm-path <2s test; GS2.4 hostile-input tests (D40); U-gates. **3h.**

**S3 — Feature & technical-analysis pack** *(absorbs v2.0 L4)*
Tasks: v2.0 L4 tasks 4.1–4.3 (indicators with golden fixtures, engine-config versioning with byte-identical replay gate, regime service) + (3.4) regime shading data series in the dossier chart payload + (3.5) Technical verdict-card composer: rolls indicator states into a labeled stance with per-indicator evidence rows.
Gates: G4.1–G4.2 (golden + determinism) + GS3.3 verdict composer fixture matrix (bull/bear/mixed/insufficient) + U-gates. **3h.**

**S4 — Model tournament & automatic selection (the "auto-ML/RL" heart)**
Tasks: (4.1) implement the ML leg per D35(b) — real `ml_return_forecaster` with train/predict + persisted model fingerprint; (4.2) tournament runner per D36: walk-forward splitter (calendar-aware), candidate execution harness reusing `run_strategy` mechanics, scoreboard with penalty decomposition; (4.3) RL leg: adapt the L7/8I–8F machinery — dataset export → smallest-config PPO/A2C → artifact import → candidate evaluation inside the tournament, with the D35 fallback path; (4.4) isolation regression tests: tournament writes touch dossier tables only, never recommendations/publication (D18/D30); (4.5) `TournamentScoreboard` payload per D37.
Gates: GS4.1 leakage tests (features at t use data ≤t only; adversarial shifted-fixture must be caught); GS4.2 overfitting guard demonstrably penalizes a deliberately overfit candidate (fixture proof); GS4.3 RL-leg degradation path e2e; GS4.4 isolation regression; GS4.5 runtime within D39 budget on fixture data; council Quant Skeptic checklist in full; U-gates. **4h.**

**S5 — The One Screen (`/` becomes ticker-first)**
Tasks: (5.1) hero + autocomplete (Phase 20.3 endpoint) replacing the current home for simple users; existing Home command-center content relocates to `/pro` landing; (5.2) progress UX bound to pipeline stages (stage names in plain language, elapsed time, partial results streaming in as stages finish); (5.3) dossier screen per D31: SummaryBar, four VerdictCards, regime-shaded chart, EvidenceDrawer per card, freshness stamps, disclaimer strip; (5.4) Model Insight card per D37 with TournamentScoreboard drawer; (5.5) shareable `/s/[ticker]` deep link + export reusing the `/analyze` self-contained HTML pattern; (5.6) telemetry: `leap.simple_ticker_submitted`, `leap.dossier_rendered`, `leap.evidence_expanded`, `leap.compare_started`.
Gates: GS5.1 novice-path e2e: from `/`, type ticker, reach full dossier with **zero other interactions**; GS5.2 all D31 states rendered (loading/partial/error/insufficient/stale) in e2e; GS5.3 mobile sweep clean; GS5.4 axe 0 critical/serious; council UX Critic + Truthfulness Auditor in full; U-gates. **4h.**

**S6 — Comparison mode**
Tasks: (6.1) `/compare?tickers=A,B,C` (≤4, D32): side-by-side SummaryBars + per-dimension rows (technical stance, sentiment, fundamentals snapshot, selected model + validation score) sourced from cached dossiers, triggering autopilot for cold tickers with per-column progress; (6.2) add-to-compare affordance on the dossier; (6.3) divergence highlighting (where tickers disagree most), computed not editorialized.
Gates: GS6.1 mixed warm/cold comparison e2e; GS6.2 mobile: columns → stacked cards; GS6.3 axe clean; U-gates. **2h.**

**S7 — Pro area migration** *(absorbs v2.0 L5 + L6)*
Tasks: (7.1) move all manual surfaces per D33 with re-export-first moves + 308 redirects (CSV-driven); (7.2) Simple↔Pro switcher; Pro landing = today's command-center Home; (7.3) decision-workspace rebuild (v2.0 L6 tasks 6.1–6.6: two-pane, `/pro/decision/[id]`, audit drawer, gate checklist, telemetry) executed inside Pro; (7.4) nav: Simple shows nothing but the product (logo, ticker box, compare, help, account); Pro shows the 9-destination map from v2.0 Appendix D prefixed `/pro`.
Gates: G5.1–G5.3 (redirects/sweep/links, v2.0) + G6.1–G6.3 (decision workspace, v2.0) rebased onto `/pro`; U-gates. **4h.**

**S8 — Background automation & notifications**
Tasks: (8.1) extend `jobs/daily_dag.py` per D38 (refresh window, budget-aware ordering); (8.2) news-delta trigger for enrich+tournament re-run; (8.3) material-change rules + `notifications.py` wiring + per-user notification prefs reusing existing patterns; (8.4) ops visibility: autopilot job table on `/pro/ops` with stage timings and skip log.
Gates: GS8.1 DAG dry-run executes refresh set deterministically on fixtures; GS8.2 material-change rules fixture matrix; GS8.3 no notification without a dossier-linked evidence URL; U-gates. **2–3h.**

**S9 — Sourced "why this matters" insights** *(= v2.0 L8, retargeted)*
As v2.0 L8 (annotation job, contract E.2, adversarial validator, canary, flag) with the output additionally feeding the dossier News card's top items.
Gates: G8.1–G8.3 (v2.0) + dossier-card integration e2e; U-gates. **2h.**

### CLOSE

**C1 — Full regression, truth surfaces, close** *(absorbs v2.0 L9+L10)*
Tasks: relationship-to-FinRL-X help page + "What FINRLX is not" refresh (v2.0 L9.1–9.2); state-drift CI check (L9.3); time-to-first-insight funnel now measured **from ticker submit** (L9.4 retargeted); full auth+unauth sweeps on the final Simple+Pro IA; production smoke; `PROGRAM_LEAP_CLOSE_REPORT.md` with per-phase evidence, deviations ledger, debt register, KPI table filled, **QZ-4 zero-questions certification**; tag `leap-v1`.
Gates: all green; report + tag; QZ-4. **2–3h.**

---

## 7. Program-exit KPIs v3.0

| # | KPI | Baseline | Exit target |
|---|---|---|---|
| K1 | Simple-user contract | Multi-page product, wizard on `/analyze` only | Ticker in → full 360° dossier, **zero other inputs**, e2e-proven |
| K2 | Dossier latency | n/a | Warm <2s; cold ≤6 min ex-RL (D39), progress visible throughout |
| K3 | Automatic model selection | `ml_return_forecaster` stubbed; no tournament | Tournament live: heuristics+ML(+RL) auto-scored with overfitting guard; winner explained on-screen |
| K4 | RL in the product | Isolated research only, invisible | RL candidates compete in tournaments with honest labels; isolation from recommendations regression-tested |
| K5 | Simple/Pro separation | All surfaces mixed | Simple = one screen + compare; 100% of manual surfaces under `/pro/*` with 308s |
| K6 | Comparison | None | ≤4 tickers side-by-side from cached dossiers |
| K7 | Background autonomy | Daily DAG exists, no dossier refresh | Auto-refresh + news-triggered re-analysis + evidence-linked notifications |
| K8 | Axe serious+critical | contrast 25/25 (May) | 0, proven twice, incl. authenticated |
| K9 | Data resilience | 1 provider | 3-leg chain + staleness states |
| K10 | Question-zero | untested | Certified in close report (QZ-4) |
| K11 | Council governance | none | 4 PASS verdicts per merged phase, committed |

---

## 8. Risk register v3.0 (additions to v2.0 §9)

| Risk | L | Mitigation | Residual |
|---|---|---|---|
| Tournament results unstable run-to-run (seed sensitivity) | M | Fixed seeds per (ticker, fingerprint); scoreboard shows seed; ties broken toward simpler model (D36) | Low |
| RL leg impossible on deployment (no torch) | H | D35 fallback designed-in: honest `queued_for_research_run` status; tournament completes without it | Accepted, honest |
| Simple users read dossiers as advice | M | D30/D37 labeling; Truthfulness Auditor checklist blocks advice-verbs; disclaimer strip non-dismissible | Low-Med |
| Autopilot cost/latency on Railway worker | M | D39 budgets as tests; cache-first; budget-aware DAG ordering (D38) | Low |
| Council review cycles loop | L | Objective checklists; 3-cycle cap → D26 scope trim | Low |
| Home replacement disorients existing users | M | Pro switcher prominent; Pro landing = old Home verbatim; help note | Low |

---

## Appendix F — Council checklists (objective, yes/no)

**F.1 Quant Skeptic:** no feature uses data > t; walk-forward splits calendar-correct; penalty math matches D36 spec; deliberately-overfit fixture is rejected; determinism gate green; scoreboard numbers reproducible from persisted inputs.
**F.2 UX Critic:** novice e2e passes with zero non-ticker interactions; every D31 state reachable and rendered; no text <11px equivalent tokens; mobile stacking correct; all drill-ins return without navigation loss; loading states name their stage in plain language.
**F.3 Truthfulness Auditor:** advice-verb scan clean; every displayed number has an evidence drawer or provenance stamp; disclaimer present on dossier/compare/export; RL outputs labeled research-only; isolation regression test present and green; no "guaranteed/ensure/will outperform" strings.
**F.4 Security/Ops:** D40 hostile-input tests present; no secrets in diff or fixtures; migrations additive with tested downgrade; job failures leave no orphaned running states; rate-limit behavior on autopilot endpoint tested; smoke green post-merge.

Appendices A–E of v2.0 (report template, commit/PR conventions, gate commands, Pro route map, data contracts) remain in force; **E.4 (new) Dossier schema:** `{ticker, generated_at, dataset_fingerprint, engine_config_version, freshness, sections: {technical, news_sentiment, fundamentals, filings, model_insight}, tournament: {candidates[], scores[], penalties[], winner, rationale}, availability_flags, disclaimers}`.

---

*End of plan v3.0 — the single source of truth for Program LEAP. Amendments are committed as v3.x with a changelog line.*
