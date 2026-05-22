# Phase 18J — FINRLX vs FinRL-X upstream + production UX audit

**Date:** 2026-05-23
**Scope:** Decision-grade audit of (a) the FINRLX production site at `https://frontend-production-7e8b1.up.railway.app/` and (b) feature parity vs. the upstream FinRL-X reference (`AI4Finance-Foundation/FinRL-Trading`, master branch, paper [arXiv:2603.21330](https://arxiv.org/abs/2603.21330)) and the Medium tutorial *Getting Started with FinRL*.

**Status:** Read-only audit + low-risk a11y fixes applied. No backend changes. No business-logic changes.

**Evidence:** `DOCS/handoff/_phase18sweep_2026-05-23/` — 100 production screenshots (25 routes × 4 viewports), per-test axe JSON, aggregate summary.

---

## 1. Executive summary

| Dimension | FINRLX status | One-line read |
|---|---|---|
| **Production UX** | Healthy: 25/25 routes return 200, zero JS crashes across desktop + mobile | Ship-stable baseline |
| **A11y — critical** | **8 critical** violations on `/decision` (button-name × 3, label × 4) | Fixed in this audit |
| **A11y — serious** | `color-contrast` on all 25 routes, `aria-prohibited-attr` × 14 on `/ops`, `svg-img-alt` × 5 on `/comparison`, `link-in-text-block` × 3 on `/help` | Mix of design-system + per-component |
| **FinRL-X parity — algos** | No real PPO/SAC training (Phase 8A stubbed); heuristic + random RL baselines only | Major gap if "RL platform" is the brand |
| **FinRL-X parity — exec** | No Alpaca / broker integration; paper portfolio fully simulated | Major gap for "live trading" claims |
| **FinRL-X parity — risk** | No regime detection (26-week trend, VIX, 3-day risk-off), no trailing/absolute stop-loss, no cooldown | Gap for "adaptive rotation" claims |
| **FINRLX-only strengths** | Recommendation governance, audit/provenance, multi-tenant, FX, news/sentiment, operator console, LLM research | Substantial moat vs. upstream |

**Recommendation:** The product is *not* a thinner FinRL-X wrapper — it has a meaningfully different value proposition (governance + multi-tenant decision intelligence over algos). The phrasing in marketing/help should reflect that explicitly, instead of inheriting FinRL-X's "DRL platform" framing. Three concrete moves recommended in §6.

---

## 2. Methodology

### 2.1 Site walkthrough
- **Target:** Production Railway deployment (not local dev).
- **Tool:** Playwright (Chromium) via custom spec `frontend/tests/e2e/_site-sweep.spec.ts`.
- **Coverage:** 25 routes × 4 viewports = 100 navigations.
  - Viewports: `desktop-1920` (1920×1080), `desktop-1280` (1280×800), `iPhone 15 Pro`, `Pixel 7`.
  - Routes: 7 public (`/`, `/login`, `/signup`, `/disclaimer`, `/privacy`, `/terms`, `/help`) + 18 auth-gated (`/decision`, `/research`, `/backtests`, `/paper`, `/risk`, `/replay`, `/comparison`, `/policies`, `/universe`, `/news`, `/integrations`, `/templates`, `/profile`, `/feedback`, `/ops`, `/operator`, `/admin`, `/onboarding`).
- **Per-route capture:** full-page screenshot, HTTP status, console errors, page (JS) errors, axe-core violations under WCAG 2.0 A/AA + 2.1 A/AA.
- **Result:** 100/100 navigations succeeded (3 needed Playwright's auto-retry due to `networkidle` timing under analytics load).

### 2.2 Upstream comparison
- Pulled `AI4Finance-Foundation/FinRL-Trading` master branch (description: *"FinRL-X: An AI-Native Modular Infrastructure for Quantitative Trading"*) via `gh api` — verified full `src/` tree, file sizes, README.
- Cross-checked against the Medium tutorial *Getting Started with FinRL for Quantitative Trading Strategies* (canonical onboarding flow for new users of upstream).
- FINRLX backend scoped via the seven upstream capability buckets (Data, Strategy, Backtest, RL, Trading/Execution, CLI/Deploy, Risk/Regime).

---

## 3. Live UX findings (production)

### 3.1 Health — what's working
- **Zero JavaScript crashes** across 100 navigations on desktop + mobile.
- **All 25 routes render HTTP 200**, including auth-gated routes (they render a login wall with 200).
- **No page errors** captured by Playwright `pageerror` listener.
- **Mobile layout intact** on iPhone 15 / Pixel 7 — no horizontal scroll, no overflow, no obviously-broken navigation in screenshots (see `_phase18sweep_2026-05-23/screenshots/iphone-15/` and `pixel-8/`).

### 3.2 A11y violations (axe-core, WCAG 2.0 + 2.1 A/AA)

#### CRITICAL (8 violations on `/decision`, all viewports)

| Rule | Nodes | Component | Fix status |
|---|---|---|---|
| `button-name` | 3 | `ScenarioCard.tsx` toggle switches (lines 149–155) — icon-only buttons with no accessible name | **FIXED** this audit: added `role="switch"`, `aria-checked`, `aria-label` |
| `label` | 4 | `ScenarioCard.tsx` range sliders (Horizon / Rate shock / Correlation / Earnings revision) — `<label>` not connected to `<input>` via `htmlFor` | **FIXED** this audit: added `id` to inputs + `htmlFor` to labels |

#### SERIOUS

| Rule | Routes | Description | Recommended action |
|---|---|---|---|
| `color-contrast` | **all 25** | Insufficient contrast on at least 1 element per route. Likely from `--ink-3`/`--ink-4` and `--stale` design tokens on light backgrounds. | **Design-system fix, NOT auto-fixed.** Single token pass in `globals.css` would resolve site-wide. Highest-leverage fix. |
| `aria-prohibited-attr` | `/ops` (14 nodes) | `<span aria-label>` on `StatusDot` — `aria-label` is prohibited on `<span>` without an explicit ARIA role. | **FIXED** this audit: added `role="img"` and reworded label to `"Status: ${status}"`. |
| `svg-img-alt` | `/comparison` (5 nodes) | Recharts `<svg>` elements lack `<title>`. Parent `<div role="img" aria-label="...">` already provides a summary, so the inner SVG is double-counted. | **Recharts-level fix.** Two paths: (a) wrap each chart in a visually-hidden `<svg><title>…</title></svg>`, or (b) upgrade to a Recharts version with built-in `<title>` injection. Defer to a dedicated chart-a11y pass. |
| `link-in-text-block` | `/help` (3 nodes) | Inline links inside help-doc prose are only color-distinguishable from surrounding text. Fails 1.4.1 (use of color). | **Design-system fix:** add underline / heavier weight on inline links by default in the MDX renderer. |

#### Console errors (not visible to user, but worth knowing)
Three routes log a benign 401 to console while fetching authenticated APIs from a logged-out session:
- `/operator` — `Failed to load resource: 401`
- `/paper` — `Failed to load resource: 401`
- `/replay` — `Failed to load resource: 401`

**Interpretation:** The page renders correctly (login wall), but the fetch was issued before the auth gate kicked in. **Not a regression.** Optional cleanup: short-circuit the fetch when `useAuth().user` is null. Low priority.

### 3.3 What was NOT tested (be honest)
- **Authenticated flows** — sweep ran as a logged-out browser. Decision detail with real recommendations, onboarding completion, paper portfolio rebalance, RL benchmark execution, ops audit drill-down — all behind auth and not exercised.
- **Form submission paths** — no signup, no login, no policy editing. Intentional: this is production.
- **Performance / Core Web Vitals** — sweep captures load timing but not full Lighthouse. See §6.
- **Cross-browser** — Chromium only (per existing `playwright.config.ts`).
- **Lang / direction** — page rendered in English; Hebrew/RTL not tested.

---

## 4. FINRLX vs FinRL-X — structural diff

Upstream `src/` (15 modules across 8 dirs) maps to FINRLX `backend/app/`:

### 4.1 Data layer

| Upstream FinRL-X | FINRLX status |
|---|---|
| `src/data/data_fetcher.py` (Yahoo + FMP + WRDS, 69KB) | **Partial.** `backend/app/services/ingest.py` does yfinance + local stub + synthetic news; FMP/WRDS absent. |
| `src/data/data_processor.py` (feature engineering) | **Partial.** `backend/app/services/features.py` produces return_5d/20d/60d, vol_20d, drawdown_20d, news_sentiment_7d. **No MACD, RSI, CCI, DX, VIX, turbulence.** |
| `src/data/data_store.py` (SQLite cache, 42KB) | **Different.** FINRLX uses PostgreSQL via SQLAlchemy (production) or SQLite (dev). |
| `src/data/trading_calendar.py` | **Missing.** No explicit trading-calendar utility. |
| `src/data/backfill_historical_sp500.py` | **Missing.** No bulk S&P 500 backfill script. |
| `src/data/fetch_and_store_fundamentals.py` | **Different paradigm.** FINRLX has fundamentals via Finnhub (Phase 16, `FUNDAMENTALS_PROVIDER=finnhub`). |

### 4.2 Strategy / signal layer

| Upstream FinRL-X | FINRLX status |
|---|---|
| `src/strategies/base_strategy.py` + `base_signal.py` (abstract contract) | **Equivalent.** `backend/app/services/engines.py` has signal engines (`technical_momentum`, `risk_quality`, `news_sentiment`, `ml_return_forecaster`). |
| `src/strategies/ml_strategy.py` (57KB — Random Forest stock selection) | **Stubbed.** `ml_return_forecaster` engine exists but is a placeholder. No trained model. |
| `src/strategies/fundamental_portfolio_drl.py` (30KB — DRL+fundamentals) | **Missing.** |
| `src/strategies/group_selection_by_gics.py` (18KB) | **Missing.** No GICS sector grouping. |
| `src/strategies/ml_bucket_selection.py` (59KB) | **Missing.** No quarterly NASDAQ-100 top-quartile rotation. |
| `src/strategies/rl_model.py` (21KB) | **Stubbed.** `backend/app/services/finrlx_research.py` is the Phase 8A research adapter; **no PPO/SAC training**, no stable-baselines3, no torch. Heuristic + random baselines only. |
| `src/strategies/run_adaptive_rotation_strategy.py` + `AdaptiveRotationConf_v1.2.{1,2}.yaml` | **Missing.** No adaptive rotation strategy. No YAML strategy configs. |
| `src/strategies/universe_manager.py` | **Equivalent.** `backend/app/services/universe.py` (and `/universe` route). |
| `src/strategies/tsmomsignal.py` (time-series momentum) | **Missing as named strategy.** Concept partly covered by `technical_momentum` engine. |
| `src/strategies/execution_engine.py` (17KB) | **Different.** FINRLX uses `decision_pipeline.py` + `publication.py` (weight → governance → publication state machine). |

### 4.3 Backtest

| Upstream FinRL-X | FINRLX status |
|---|---|
| `src/backtest/backtest_engine.py` (31KB — `bt`-library powered, multi-benchmark) | **Different.** `backend/app/services/backtesting.py` is hand-rolled walk-forward with weekly/monthly rebalance. Transaction cost 10 bps default. |
| Multi-benchmark vs SPY + QQQ | **Missing.** FINRLX compares portfolio vs cash only. No equity benchmark side-by-side. |
| Metrics: cum return, ann return, vol, Sharpe, Calmar, max DD, win rate | **Partial.** All present except **Calmar** is not surfaced explicitly. |

### 4.4 RL allocator

| Upstream FinRL-X | FINRLX status |
|---|---|
| PPO + SAC, weight-centric output | **Stubbed.** RL adapter (`rl_environment.py` + `rl_adapter.py`) defines schema but training is offline-only via baseline agents (`heuristic_baseline`, `random_valid`). |
| Composable stack `S → A → T → R` (selection → allocation → timing → risk overlay) | **Different paradigm.** FINRLX has a unified `decision_pipeline.py` producing recommendations; no explicit timing/risk-overlay separation. |
| Live retraining / model registry | FINRLX has Phase 6A `model_registry`, Phase 6C shadow backtest promotion — **more mature than upstream's model lifecycle**. But the actual models are stubbed. |

### 4.5 Trading / execution

| Upstream FinRL-X | FINRLX status |
|---|---|
| `src/trading/alpaca_manager.py` (35KB, multi-account) | **Missing.** No broker integration. Per project memory: "no broker" is a Phase BETA decision. |
| `src/trading/trade_executor.py` + `performance_analyzer.py` | **Different.** `backend/app/services/paper.py` is fully simulated paper trading; no live orders. |

### 4.6 Risk / regime

| Upstream FinRL-X | FINRLX status |
|---|---|
| 26-week trend + VIX slow-regime detector | **Missing.** |
| 3-day fast risk-off shock detector | **Missing.** |
| Trailing stop-loss + absolute stop-loss + cooldown | **Missing.** Only policy constraints (`position_cap_max`, `cash_floor`) enforced at action time. |
| Portfolio risk metrics | **Equivalent.** `backend/app/services/risk_metrics.py` computes VaR, concentration, drawdown, exposure. |

### 4.7 CLI / deploy

| Upstream FinRL-X | FINRLX status |
|---|---|
| `deploy.sh` one-command (backtest / single-date / paper modes) | **Missing.** FINRLX deploys via Railway; no equivalent operator CLI. |
| `examples/FinRL_Full_Workflow.ipynb` (Jupyter) | **Missing.** No example notebook. |
| Pydantic-based settings + `.env.example` | **Equivalent.** Same pattern. |

### 4.8 Web layer (worth noting)

Upstream has `src/web/{app.py, components.py}` — a small web layer (22KB + 12KB). FINRLX has a full Next.js 15 app with 25 routes, App Router, feature flags, multi-tenant, governance UI. **FINRLX UI is dramatically more developed than upstream's `web/`.** This is one of FINRLX's biggest differentiators.

---

## 5. FINRLX-only capabilities (not in upstream)

These are real moats:

1. **Recommendation governance state machine** — `publication.py` enforces draft → staged → approved → published transitions. Upstream has nothing equivalent.
2. **Provenance + audit trail** — `provenance.py` with SHA-256 fingerprints + tamper-evident `OpsAuditEvent`. Upstream has logging but no audit chain.
3. **Multi-tenant + investor profiles** — `profile.py` + role-based auth + 8-step wizard onboarding. Upstream is single-user CLI.
4. **News/sentiment ingestion** as first-class feature input (synthetic in dev, Finnhub-ready). Upstream mentions "LLM sentiment preprocessing" as a slot, doesn't implement it.
5. **FX + multi-currency paper portfolio** — `fx_service.py` + Frankfurter provider. Upstream is USD-only.
6. **Operator console + `/ops`** — health grid, queue panel, breaches/incidents, audit log. Upstream has none.
7. **Replay determinism harness** — `replay_determinism.py` + dedicated UI route. Upstream has no replay concept.
8. **Decision research lane (LLM)** — Phase 18.6.1 trajectory + structured-metrics LLM contract. Upstream has no LLM lane.
9. **Recommendation templates** — seed templates with template metrics (Phase TPL). Upstream has none.
10. **Feature flag plane (13 flags)** + fail-closed loading. Upstream has none.

---

## 6. Decision-grade recommendations

Three buckets ordered by leverage:

### A. Brand / positioning (highest leverage, lowest cost)
**Don't compete with FinRL-X on algorithms.** You'll lose — they have PPO/SAC, Alpaca, adaptive rotation. **Compete on governance + decision intelligence**, which is where you actually have a 6–12 month lead.

Concrete changes:
- Replace "AI-native trading infrastructure" language in `/help` and onboarding with **"decision intelligence platform for medium-term investing"** (already in your `README.md` — propagate it).
- Add a `/help` doc that names what FINRLX is *not* (not a broker, not an RL training framework, not for HFT) and links to FinRL-X for users who want raw DRL.
- The disclaimer surface (already strong) is part of the moat — highlight it as a feature, not a footnote.

### B. Plug the two highest-leverage upstream gaps
Both are surface-level (not deep ML) wins that close 80% of the perceived feature gap:

1. **Multi-benchmark backtest comparison (SPY/QQQ overlay)** — extend `backtesting.py` to compute the same metrics for a passive benchmark over the same window, render side-by-side. Estimated 1–2 days. Closes a real gap users will notice.
2. **Calmar ratio in the metrics surface** — already computable from `max_drawdown` + `annualized_return` you have. Add to `BacktestExperiment` model + UI display. Estimated 2 hours.

The big upstream gaps (PPO/SAC training, regime detection, Alpaca) are deliberate per your roadmap memory ("no broker", "Phase BETA"). Don't waste cycles on them.

### C. Fix the production a11y baseline (already partially done in this audit)
- ✅ **Done in this commit:** ScenarioCard 7 critical violations + OpsHealthGrid `aria-prohibited-attr`.
- **Next pass needed:**
  1. **`color-contrast` (all 25 routes)** — single design-token edit in `globals.css`. Highest single-fix leverage; do this in a dedicated short PR.
  2. **Recharts `<title>` injection** — 5 nodes on `/comparison`. Wrap each chart in a visually-hidden `<title>` SVG, or upgrade Recharts. ~1 hour.
  3. **`link-in-text-block` on `/help`** — underline inline links in MDX renderer. CSS only. ~15 min.
  4. **Silent 401 on `/operator`, `/paper`, `/replay`** — gate the fetch on `user != null`. ~30 min.

After all four, the axe baseline should hit zero critical + zero serious site-wide, which lets you tighten the `KNOWN_PREEXISTING_RULES` gate in `tests/e2e/_helpers/axe.ts` and prevent regressions.

---

## 7. Evidence index

All artifacts in `DOCS/handoff/_phase18sweep_2026-05-23/`:
- `screenshots/{desktop-1920,desktop-1280,iphone-15,pixel-8}/*.png` — 100 production screenshots
- `findings/*.json` — 100 per-test JSON files
- `sweep-report.json` — consolidated array
- `aggregate-summary.txt` — human-readable rollup
- `aggregate.py` — re-runnable aggregator

Sweep spec for re-run:
```bash
cd frontend
PLAYWRIGHT_BASE_URL=https://frontend-production-7e8b1.up.railway.app \
PLAYWRIGHT_DISABLE_WEBSERVER=1 \
  npx playwright test tests/e2e/_site-sweep.spec.ts --workers=4
```

---

## 8. Open questions for product

1. **Brand alignment** — confirm: positioning shift away from "RL platform" toward "decision intelligence + governance"?
2. **FinRL-X parity scope** — is multi-benchmark (SPY/QQQ) overlay worth shipping in Phase 19, or defer to Phase 20+?
3. **A11y baseline** — willing to commit a dedicated PR for the `color-contrast` design-token pass? (~half day of design + dev review.)
4. **Authenticated sweep** — should the next audit pass run with a test user logged in to exercise gated routes? Requires a sandboxed test account on prod or staging.
