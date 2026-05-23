# Phase 19 — Audit follow-up work plan

**Source:** Findings from `DOCS/handoff/PHASE_18J_FINRLX_VS_UPSTREAM_AUDIT.md` (production sweep + upstream FinRL-X parity audit, 2026-05-23).

**Goal:** Close every actionable item from the audit with verified, reverted-deploy-safe PRs. After each sub-phase: commit → push → wait for Railway deploy → verify live before moving on.

**Total estimate:** ~6 working days.

---

## Sequencing

```
19.0  CI cleanup (sweep spec gating)            (15 min)   prerequisite
19A   Quick wins                                (1 day)
  A1  Calmar ratio (backend+frontend)
  A2  /help inline-link styling
  A3  401 fetch gating on /operator,/paper,/replay
19B   Color-contrast design tokens              (½ day)
19C   Recharts <title> injection                (2 h)
19D   SPY/QQQ multi-benchmark overlay           (1-2 days)
19E   Brand/positioning shift                   (1 day)
19F   Authenticated sweep + axe gate hardening  (1 day)
```

---

## Phase 19.0 — CI cleanup (preamble)

**Why:** `_site-sweep.spec.ts` runs in CI without `PLAYWRIGHT_BASE_URL` set and hits the CI-spawned localhost server for ~5.5 min, providing no value and slowing the build. Gate it to no-op unless the env var is set.

**File:** `frontend/tests/e2e/_site-sweep.spec.ts`
**Acceptance:** CI run completes ≥ 1 min faster; sweep spec reports 0 tests in CI.

---

## Phase 19A — Quick wins (1 day)

### 19A.1 — Calmar ratio

| | |
|---|---|
| **Files** | `backend/app/models/validation.py`, `backend/app/services/backtesting.py`, `backend/tests/services/test_backtesting.py`, `frontend/src/components/backtests/MetricsTable.tsx` |
| **Dev skills** | `quant-analyst`, `backtesting-frameworks`, `risk-metrics-calculation` |
| **Test skills** | `tdd-workflows-tdd-cycle`, `backtest-hygiene-gate`, `playwright-skill` |
| **Acceptance** | pytest passes; `BacktestExperiment.calmar_ratio` non-null; UI row renders |
| **Risk** | Low — additive |

### 19A.2 — /help inline-link styling

| | |
|---|---|
| **Files** | MDX renderer in `frontend/src/app/help/` |
| **Dev skills** | `fixing-accessibility`, `tailwind-design-system` |
| **Test skills** | `_site-sweep.spec.ts --grep "/help"`, axe rule check |
| **Acceptance** | `link-in-text-block` count on `/help` → 0 |
| **Risk** | Cosmetic |

### 19A.3 — 401 fetch gating

| | |
|---|---|
| **Files** | `frontend/src/app/{operator,paper,replay}/page.tsx` + any auth-fetch hooks |
| **Dev skills** | `nextjs-app-router-patterns`, `react-best-practices` |
| **Test skills** | `webapp-testing` |
| **Acceptance** | Sweep finds zero 401 in `consoleErrors[]` for those 3 routes |
| **Risk** | Low |

---

## Phase 19B — Color-contrast design tokens (½ day)

| | |
|---|---|
| **Why** | Axe `color-contrast` violated on all 25 routes — site-wide design-system issue |
| **Files** | `frontend/src/app/globals.css` (light + dark), possibly `frontend/tailwind.config.ts` |
| **Approach** | Extract failing fg/bg pairs from sweep JSON → map to CSS vars → adjust failing tokens → re-sweep → iterate |
| **Dev skills** | `tailwind-design-system`, `anthropic-frontend-design-mirror`, `vercel-web-design-guidelines-mirror`, `fixing-accessibility` |
| **Test skills** | `finrlx-visual-qa-accessibility-gate`, `wcag-audit-patterns`, full sweep re-run, before/after screenshot diff |
| **Acceptance** | `color-contrast` violations: 25 routes → 0 |
| **Risk** | **Medium** — site-wide visual change. Mitigation: produce before/after screenshot set. |
| **Rollback** | Single-file revert in `globals.css` |

---

## Phase 19C — Recharts `<title>` injection (1-2 h)

| | |
|---|---|
| **Files** | `frontend/src/components/comparison/{ComparisonBarChart,AlignmentChart,WeightsBarChart,PriceChartCard}.tsx` |
| **Approach** | Add `accessibilityLayer` prop OR wrap chart with visually-hidden `<svg><title>` and set chart's SVG `aria-hidden="true"` |
| **Dev skills** | `react-best-practices`, `frontend-design`, `screen-reader-testing` |
| **Test skills** | Sweep on `/comparison`, optional unit test for `getByRole('img')` |
| **Acceptance** | `svg-img-alt` count on `/comparison` → 0 |

---

## Phase 19D — SPY/QQQ multi-benchmark overlay (1-2 days)

### 19D.1 — Backend (1 day)

| | |
|---|---|
| **Files** | `backend/app/services/backtesting.py`, `backend/app/models/validation.py`, new Alembic migration |
| **Dev skills** | `quant-analyst`, `backtesting-frameworks`, `backtest-hygiene-gate` |
| **Test skills** | `tdd-workflows-tdd-cycle`, `replay-determinism-harness` (your skill) |
| **Acceptance** | Same-window same-fee benchmark metrics computed; migration clean on prod DB |

### 19D.2 — Frontend (½ day)

| | |
|---|---|
| **Files** | `frontend/src/components/backtests/MetricsTable.tsx`, `EquityCurveChart.tsx` (or equivalent) |
| **Dev skills** | `finrlx-fintech-dashboard-patterns` (your skill), `frontend-design`, `react-best-practices` |
| **Test skills** | `playwright-skill`, `webapp-testing`, `e2e-testing-patterns` |
| **Acceptance** | Multi-column table + overlay chart render desktop + mobile |
| **Risk** | Medium — schema change; need backfill plan for old experiments |

---

## Phase 19E — Brand / positioning shift (1 day, content)

| | |
|---|---|
| **Why** | Don't compete with FinRL-X on algorithms — lead with governance + decision intelligence |
| **Files** | `frontend/src/app/help/` content, onboarding wizard copy, landing + disclaimer copy, possibly README |
| **Dev skills** | `fintech-disclaimer-and-marketing-guard` (your skill), `finrlx-ai-ux-governance` (your skill), `copy-editing` |
| **Test skills** | Existing disclaimer vitest passes |
| **Acceptance** | New `/help/what-finrlx-is-not.md` page exists; onboarding step 1 reflects governance framing |

---

## Phase 19F — Authenticated sweep + axe gate hardening (1 day)

| | |
|---|---|
| **Approach** | Sandboxed test user → `storageState` setup in Playwright → reuse session for auth-gated routes → tighten `KNOWN_PREEXISTING_RULES` to empty |
| **Files** | `frontend/tests/e2e/_site-sweep.spec.ts`, `frontend/tests/e2e/_helpers/axe.ts`, `frontend/playwright.config.ts` (`globalSetup`) |
| **Dev skills** | `e2e-testing`, `e2e-testing-patterns`, `playwright-skill` |
| **Test skills** | `accessibility-compliance-accessibility-audit` |
| **Acceptance** | Sweep covers ~35 routes with auth, zero critical + zero serious, axe gate fails any future serious regression |
| **Risk** | Medium — needs clean test user |

---

## Cross-cutting verification (every PR)

| Step | When | Skill |
|---|---|---|
| `npm run typecheck` | always | built-in |
| `npm run test:ci` (vitest) | always | built-in |
| `_site-sweep.spec.ts` re-run against production after deploy | after each push | `finrlx-visual-qa-accessibility-gate`, `webapp-testing` |
| Update `KNOWN_PREEXISTING_RULES` (remove what was fixed) | each a11y PR | `wcag-audit-patterns`, `fixing-accessibility` |
| `/ultrareview` on the PR | before merge of 19B, 19D, 19F | user-triggered |

---

## Railway deploy detection (operating procedure)

After every push:
1. Capture pushed SHA (`git rev-parse HEAD`).
2. Poll `gh api repos/rotemyoeli/FINRLX/deployments?per_page=5` until a deployment row appears with that SHA.
3. Then poll `gh api repos/rotemyoeli/FINRLX/deployments/{id}/statuses` until `state == "success"`.
4. Run targeted sweep on the routes touched by the PR (use `--grep` filter).
5. If sweep fails → fix and re-push; do NOT advance to next sub-phase.

---

## Out of scope (per project memory + audit Section 6)

- Real PPO/SAC training (Phase 8A research-only)
- Alpaca/broker integration ("no broker" — Phase BETA)
- Regime detection / stop-loss / cooldown
- Cross-browser sweep (Chromium-only is fine for now)
- Lighthouse perf pass (no evidence of breakage)

---

## Issues

One GitHub issue per sub-phase:
- `[19.0]` CI cleanup — gate sweep spec
- `[19A.1]` Calmar ratio
- `[19A.2]` /help inline-link styling
- `[19A.3]` 401 fetch gating
- `[19B]` Color-contrast design tokens
- `[19C]` Recharts svg-img-alt
- `[19D]` SPY/QQQ multi-benchmark overlay
- `[19E]` Brand/positioning shift
- `[19F]` Authenticated sweep + axe gate hardening
