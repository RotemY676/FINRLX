# SIMPLE MODE SPEC — The One Screen (Program LEAP S1)

Version 1.0 · 2026-07-06 · Binding for S5/S6 implementation. Backend contracts
already live: `GET /api/v1/autopilot/dossier?ticker=` and
`GET /api/v1/autopilot/compare?tickers=` (see test suites `test_leap_autopilot.py`,
`test_leap_s2_persistence_compare.py` for exact payload shapes).

## 1. The contract with the user
Type a ticker. That is the whole interface. Everything else — ingestion, news
cross-referencing, the technical vocabulary, the automatic model tournament,
regime labeling — happens without a single setting, and every automatic choice
arrives *with its why*. Dossiers are research analysis, never advice, and the
screen says so persistently (D30).

## 2. User journey (states are the spec)
```
[J0 Hero] --submit--> [J1 Progress] --ok--> [J2 Dossier] --add ticker--> [J3 Compare]
                         |--no data--> [J4 Unknown/No-data]
                         |--thin history--> [J2 with Insufficient-history tournament card]
   any state --API down--> [J5 Error]        stale bars --> [J2 + staleness treatment]
```

### J0 — Hero (route `/`)
One centered ticker field with autocomplete (existing asset-search endpoint,
Phase 20.3), placeholder `Try NVDA`, a single primary action **Research** and
one quiet line under it: *Automatic 360° research: prices, news, technicals,
and a model tournament — with the evidence for every conclusion.* Nothing else
competes: no cards, no stats, no marketing. Current command-center Home content
relocates to `/pro` (S7). Keyboard: field autofocused; Enter submits.

### J1 — Progress
The pipeline's real stages, in plain language. **Honesty note (binding):**
`GET /autopilot/dossier` is a single blocking call in v1; per-stage `ms`
arrives only with the finished payload. The progress list therefore renders
in pipeline order as *indicative* (client-timed) — it must not fake live
per-stage completion ticks. Real per-stage progress requires a job-polling
endpoint (debt row DEBT-S5-1, tracked in STATE_OF_THE_PRODUCT). `Fetching price history · Reading recent
news · Computing technical signals · Running the model tournament · Assembling
your dossier`. Elapsed time visible. Never a bare spinner (Master Plan rule).
If total wait exceeds 20s, add one honest line: *First-time research for a
ticker takes longer; results are cached afterward.*

### J2 — Dossier (the One Screen, D31)
Desktop ≥1024px, top to bottom:
1. **SummaryBar** (sticky): ticker · latest close · research stance chip
   (constructive / neutral / cautious). **Stance mapping (binding):** the
   backend payload's `summary.stance` vocabulary is `buy`/`hold`/`sell`
   (engine-ensemble terms consumed by Pro surfaces). Simple Mode NEVER renders
   those words: the UI boundary maps `buy→constructive`, `hold→neutral`,
   `sell→cautious` (and any `trim→cautious`); the S5 wording test asserts the
   raw strings never appear in Simple Mode DOM. · regime chip ·
   freshness stamp (`freshness.latest_bar`, staleness treatment §5) · actions:
   **Compare** and **Export**.
2. **Four VerdictCards** in a 2×2 grid (stack <1024px):
   - *Technical* — stance derived from engine scores; top 3 feature rows
     (value + plain-language read); "All signals" opens the EvidenceDrawer.
   - *News & sentiment* — 7-day counts; top items with sentiment tags and,
     when annotations pass their gates (S9), a "Why it matters" line with
     model + freshness metadata; degraded state per §4.
   - *Fundamentals* — v1 renders the honest unavailable note from the payload.
   - *Model insight* — the tournament winner by name + kind chip
     (`rule-based` / `machine-learning`), its validation score, one-line
     rationale (payload `winner.rationale`), and **How this was chosen**
     opening the TournamentScoreboard drawer: every candidate's train/val
     Sharpe, divergence, penalty, score, plus the RL leg status verbatim
     (`queued_for_research_run` copy from the payload) and the disclaimers.
3. **Price chart** (existing chart component family): closes with regime
   shading bands; range fixed to the payload's 260 sessions (zero-config, D32).
4. **Disclaimer strip** (non-dismissible, quiet, always rendered): payload
   `disclaimers` verbatim.

The Master Plan's five questions map to fixed regions: What changed → SummaryBar
freshness + News card; Why it matters → annotation lines + card stances; What
requires action → nothing is ever *required*: the stance chip carries explicit
`research stance — not advice` hover/label; What evidence → EvidenceDrawer +
Scoreboard drawer; What's uncertain → confidence values, divergence/penalty
columns, and degraded-section notes.

### J3 — Compare (route `/compare?tickers=A,B`)
2–4 columns (D32 max), one row per shared dimension (stance, regime, composite
score, news counts, selected model + validation Sharpe, freshness). Divergence
highlights from the payload render as row-level markers with the measured
values — never editorial ("X is better"). Cold tickers: v1's compare call is also blocking, so the whole grid shows
one combined J1-style progress state (per-column live progress joins with
DEBT-S5-1's job endpoint); per-ticker failures render in-column with the API
error, other columns unaffected (payload `errors`).

### J4 — Unknown ticker / no data
Empty-state card: *No price data found for "XYZ".* One suggestion row from
autocomplete when available; the input stays focused for correction. No
apology, no jargon (502 detail text is logged, not shown raw).

### J5 — API error
*Research is temporarily unavailable. Your ticker is kept — retry when ready.*
Retry button re-submits the same ticker.

## 3. Zero-config inventory (D32 proof)
| Would-be setting | Fixed value | Where defined |
|---|---|---|
| History window | ~3y daily (HISTORY_DAYS_DEFAULT) | backend constant |
| News window | 7d surfaced, 30d fetched | backend constants |
| Rebalance cadence for tournament | weekly | backend constant |
| Walk-forward splits | 3 expanding | backend constant |
| Chart range | 260 sessions | payload |
| Compare max | 4 tickers | COMPARISON_MAX_TICKERS |
Nothing above appears in Simple Mode UI. All knobs live in Pro (S7).

## 4. Degradation matrix (every section is optional except prices)
| Condition | Payload signal | Rendering |
|---|---|---|
| News source down | `news_sentiment.available=false` + note | Card renders the note; no fake emptiness |
| Annotations gated off | `annotations_status != ok` | Items render without "why" lines; no gap UI |
| Fundamentals absent | `fundamentals.available=false` | Honest note, card stays |
| Thin history | tournament `winner=null` + rationale | Model card renders the rationale; other cards unaffected |
| RL unavailable | `rl.status=queued_for_research_run` | Scoreboard shows the status + note verbatim |
| Stale bars | freshness vs. today | §5 treatment |

## 5. Staleness treatment (F1.6 tie-in)
`fresh`: date stamp only. `stale` (2–5 sessions): caution-soft chip *Data
through {date}*. `degraded` (>5): breach-soft banner above the cards: *Price
data ends {date}; conclusions may be outdated.* Tokens: existing
`--caution-soft`/`--breach-soft` families only (D14 — zero new colors).

## 5b. Export (binding)
**Export** reuses the `/analyze` self-contained offline-HTML pattern and MUST
embed the full disclaimer strip, freshness stamp, and the tournament
scoreboard's penalty columns — an exported dossier carries the same honesty
surface as the live one.

## 6. Component plan (D14: reuse-first, ≤4 new)
Reuse: PageLoading/PageError/PageEmpty triad, chart component family, chip/badge
primitives, freshness components (F1.6), HelpLink, drawer primitive if present
(else new EvidenceDrawer is one of the four). New (max): `TickerHero`,
`SummaryBar`, `VerdictCard`, `TournamentScoreboard` (drawer content).
`EvidenceDrawer` reuses the existing drawer primitive; if none exists it
replaces `TickerHero` on this list and the hero composes from primitives.

## 7. Telemetry (D25)
`leap.simple_ticker_submitted{cold}` · `leap.dossier_rendered{ms, cached}` ·
`leap.evidence_expanded{card}` · `leap.scoreboard_opened` ·
`leap.compare_started{n}` · `leap.export_clicked`. No PII.

## 8. Accessibility & mobile floor
Every chip has a text label (never color-only); drawers trap focus and restore
it; progress announces stage changes via `aria-live=polite`; chart carries an
svg `<title>` (F3 lesson); mobile: cards stack in the §2 order, SummaryBar
collapses to two lines, drawers become full-height sheets. Type floor per
Master Plan rule 6; all colors from `globals.css` tokens.

## 9. Explicitly out of scope for Simple Mode
Portfolio actions, publication/governance surfaces, universes, policies,
backtest configuration, any RL training controls — all Pro (S7). Simple Mode
never links a user into an action with financial consequence.
