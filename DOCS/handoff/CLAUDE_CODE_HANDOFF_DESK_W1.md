# CLAUDE CODE HANDOFF — Desk W1 Verification & Fix Phase

**Audience:** Claude Code running in PyCharm on the operator's machine (browser-equipped,
production-network-capable — the two capabilities the build sandbox verifiably lacked).
**Baseline:** branch `main` including the `desk/w1-core` merge (this file ships with it).
**Specs of record:** `DOCS/specs/SPEC-00..04` + `DOCS/handoff/FINRLX_Unified_Research_Desk_Report_2026-07-07.docx`.
**Prime directive:** Question-Zero. Every decision you need is in the specs; if a
reference does not resolve, that is a defect — fix it and record it, do not ask.

---

## 0. What was built where you are NOT starting from zero

Built and merged from the sandbox, all structural gates green
(backend full suite + `tests/test_desk_w1.py` 27/27; vitest 86/86; tsc; ruff+mypy;
`next build` 262KB < 300KB budget):

| Layer | Delivered | Files |
|---|---|---|
| API-4 dial aggregator | `GET /api/v1/autopilot/desk/{ticker}/status` — closed enum `live|degraded|unavailable` + `detail_code`, ETag, 20/min limiter, persisted-dossier-only (never builds) | `app/services/desk_status.py`, wired in `app/api/v1/autopilot.py` |
| API-7 elevation | pure, disclosed, fixture-tested; ships as `elevation` inside the `signals` section | `app/services/desk_elevation.py` |
| API-6 method blocks | `method` object on every drawer-bearing D42 section | `app/services/desk_methods.py` |
| DEC-7 flag | `feature_desk_v2` (env `FEATURE_DESK_V2`), default **OFF**, exposed as `desk_v2` in `/api/v1/flags` | `config.py`, `flags.py` |
| Desk v2 frontend core | tokens, copy deck, EngineDial (exhaustive), 3-grammar StateCards, ForensicDrawer (anatomy+provenance+ESC), VerdictBand (n/6 DEC-5), SignalMatrixV2 (elevation+collapse doctrine), TournamentArenaV2 (divergence/penalty columns + E7 queue card), DeskV2 page behind the flag; panels C/E reuse A5 sections, F renders the benchmark-scope copy | `src/design/deskTokens.ts`, `src/lib/deskCopy.ts`, `src/components/deskv2/*`, flag switch in `src/app/pro/desk/[ticker]/page.tsx` |
| Tests | `backend/tests/test_desk_w1.py` (27), `frontend/src/__tests__/deskv2.test.tsx` (17) | — |

**Honest deltas deliberately left for THIS phase** (recorded, not hidden):
- No pixel has ever been seen. All 14 screenshot states exist in code paths but zero
  frames exist. P3′ is entirely yours.
- Panels C–F wear A5 skins, not v2 skins (SPEC-03 CMP-8/9/10 restyling pending).
- Drawer focus-trap is ESC/scrim-close only — full trap + focus-restore (CMP-7 a11y)
  needs a browser to implement honestly.
- Deep links cover `?drawer=`; `?panel=` scroll-restore not yet implemented (DEC-6 half).
- Skeletons are `loading…` placeholders, not dimension-reserving SkeletonKit (CMP-12) —
  CLS budget cannot pass until you replace them.
- `useDeskStatus` does not yet send `If-None-Match` (server ETag works; client SWR piece
  is trivial in-browser work).

## 1. Environment bring-up (do this first, verify each)

```bash
# repo root
cd backend && python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt ruff==0.8.6 mypy==1.14.1
pytest -q            # expect: full green; read ONLY the summary line
cd ../frontend && npm ci            # ci, NOT install (lockfile law)
npx playwright install --with-deps  # works on your network, not in the sandbox
npx vitest run && npx tsc --noEmit && npx next build
```
Also confirm production env per **W0**: on Railway — `FINNHUB_API_KEY` present/valid,
SEC egress allowed, and `GET /api/v1/ops/data-health` returns per-source truth. W0 is
the precondition for gate **G-6**; if data-health shows a failing source, fix the env
before judging any pixel (RSK-1).

## 2. Local flag-on for development

Backend: `FEATURE_DESK_V2=true uvicorn app.main:app --reload` (or set in your run
config). Frontend: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev`,
open `http://localhost:3000/pro/desk/UMC`. Production stays OFF until §6.

## 3. The verification matrix you must EXECUTE (not skim)

Run the SPEC-01 Gherkin rows as Playwright specs — create
`frontend/tests/deskv2.spec.ts` covering, at minimum, in this order:

1. **US-1.2/2.1** warm load: band renders ticker+price+freshness; stance chip shows
   `evidence n/6`; exactly 6 dials; states derive ONLY from `/status` (assert via route
   interception — kill a section endpoint, dial must NOT change).
2. **US-2.1 AC-4 (DEC-5)** with a fixture/env where E7 is gated: Model dial `degraded`,
   chip lists `tournament` as gated, Arena shows the dashed queue card with
   “2 of 3 legs” + “never simulated”.
3. **US-3.1** matrix: human names only; `rsi` row shows the insufficiency note;
   elevation caption contains “not a prediction”; force ≥3 nulls (route-mock the
   signals payload) → exactly ONE collapse card, **zero ‘—’ walls** (count nodes).
4. **US-3.2** scoreboard shows divergence + penalty columns with tabular numerals.
5. **US-4.1** drawers: `?drawer=A` deep-link restores open state on reload; anatomy
   order summary→factors→detail; provenance footer shows chain + fp + timestamp;
   ESC closes. THEN implement the missing focus-trap/restore and re-test.
6. **US-5.1** fault isolation: intercept `fundamentals` with 500 → only panel E shows
   the broken-grammar card; siblings render; `/status` down → dials hidden + the
   “hidden rather than guessed” notice.
7. **API-4 abuse:** loop 21 status calls < 60s → 429 with `Retry-After`.

## 4. P3′ — the 84-frame screenshot matrix (SPEC-03 §6)

Write `frontend/tests/screenshots.spec.ts` that route-mocks each of the 14 named
states (fixture JSONs — mirror `backend/tests/test_desk_w1.py::_dossier_full` and its
mutations) × viewports 1440/1280/390 × light/dark. Commit frames under
`DOCS/handoff/screenshots/deskv2/`. **You have eyes — use them:** after generating,
actually LOOK at every frame against the three reference standards (Danelfin panel
legibility, TrendSpider chart density, Koyfin hierarchy). Fix what looks wrong —
spacing, density, dial legibility at 390px, dark-mode contrast — then regenerate.
This judgment step is the entire reason this phase exists (RC3/RSK-2).

## 5. Remaining W1 build items (in priority order, each = one commit with tests)

1. CMP-12 SkeletonKit with reserved dimensions → Lighthouse CLS <0.1 (NFR-5).
2. CMP-7 focus-trap + focus-restore; then axe run over ALL 14 states → zero
   violations (NFR-4, gate G-3). Keyboard-path screen recording attached to the PR.
3. v2 skins for panels C/D/E/F per CMP-8/9/10 (LaneTape+DivergenceFlag with the
   divergence fixture; SparkTable; sector benchmark line) — reuse payloads already
   served; no backend changes expected.
4. `If-None-Match` on `useDeskStatus` + 30s SWR (SPEC-02).
5. `?panel=` scroll-restore completing DEC-6.
6. TickerLaunch (CMP-1) staged-progress states against `POST /autopilot/research`
   (attach semantics already server-side — verify US-1.1 AC-4 live).

## 6. Exit gate & flag flip (SPEC-04 §3 — ALL of G-1…G-7, in one CI run)

- G-1 e2e green (all §3 specs) · G-2 84 frames committed + reviewed · G-3 axe+keyboard
- G-4 Lighthouse budgets on the prod build · G-5 zero-fiction & drawer-coverage suites
- G-6 ten-ticker production reality: with prod data-health green, load the QA list
  (UMC included) — ≥90% signal population, zero dash-walls, dial distribution logged
- G-7 rollback rehearsal: flip `FEATURE_DESK_V2` off on Railway, confirm legacy desk
  in <1 min, flip back
Then and only then set `FEATURE_DESK_V2=true` in production. The flip commit message
must link the gate evidence. Watch 72h per SPEC-04 §5; regression → flag OFF.

## 7. Standing laws (unchanged, non-negotiable)

- Every remote-state claim ships with `git ls-remote origin main` in the same block.
- `npm ci` only. Full pytest with `-q`, read the summary line.
- Zero synthetic data anywhere, including screenshot fixtures’ *labels* — fixtures are
  fine, fake “live” claims are not. The wording scan and dash-wall doctrine are gates.
- Any engine-math diff in this phase is out of scope (feature freeze) — file it.
- Operator items you may hit: E1 (rotate the PAT — it was exposed in the build
  channel again; treat as compromised), E7/E8 remain Blocked Reports, not questions.

*Prepared 2026-07-07 by the sandbox build session; every “green” above was executed,
not assumed — see the merge commit body for the exact gate outputs.*
