# FINRLX ANALYST DESK — Research Report & Step-Change Blueprint
**Date:** 2026-07-06 · **Trigger:** operator verdict on the deployed v1 dossier ("thin, far from exploiting the system and RL")
**Persona pivot (binding):** the primary user is now an **experienced investor** who wants one very long, dense, dynamic research desk — not a minimalist simple-mode card stack.
**Method:** fact-based external research (all claims cited), repo-grounded feasibility, four council lenses applied. The v1 dossier stays as the *engine*; this report defines what must be built **on top of it**.

---

## 1. Honest diagnosis of what shipped

The v1 One Screen proved the pipeline (ticker → automatic ingestion → features → tournament → dossier) but exposes perhaps 15% of what the backend already computes, and ~0% of what the FinRL ecosystem offers beyond our in-house tournament. Specifically: the technical card shows 3 of 10+ computed features with no chart context; news shows headline+tag with no social dimension; fundamentals are an empty state despite a live EDGAR ingestion subsystem in the codebase; the tournament renders as a text table with no equity curves, no split visualization, no candidate depth; RL appears only as a status string. The operator's verdict is correct: this is an engine wearing a placeholder body.

## 2. Market landscape — what the most advanced tools actually do (facts)

**Explainable AI scoring.** Danelfin assigns every US stock a daily 1–10 AI Score — the probability of beating the S&P 500 over 3 months — computed from **10,000+ daily features across ~600 technical, ~150 fundamental and ~150 sentiment indicators**, with an "Explainable AI / no black boxes" panel showing the ranked alpha signals behind each score, portfolio alerts on score changes, and trade ideas gated on ≥60% historical win rates. Its backtested "Best Stocks" strategy claims +376% vs +166% S&P since 2017 (their own backtest; treat accordingly). Kavout ("Kai Score") and AltIndex (alt-data: Reddit mentions, app downloads, web traffic, job postings, congressional trades → 0–100 score) compete on the same shape.

**Automated technical analysis.** TrendSpider auto-detects trendlines, 150+ candlestick patterns, multi-timeframe overlays, no-code backtesting on up to 50 years of data, an "AI Strategy Lab," and a conversational Sidekick that writes scans/indicators. Trade Ideas' Holly runs 50–70+ strategies nightly over 8,000+ stocks producing entry/exit alerts.

**Source-grounded research AI.** AlphaSense-class platforms anchor every AI answer to filings/transcript passages — the pattern our S9 annotations already implement in miniature.

**The gap none of them fill (our lane):** every one of these sells a *point-in-time score or signal*. **None shows the user out-of-sample validation of competing models per ticker, with overfitting penalties, divergence, and an honest RL research leg.** Danelfin explains *which features* drove a score; nobody explains *how the chosen model survived walk-forward validation against alternatives*. That is exactly what our tournament already computes and barely renders. The experienced investor today assembles Koyfin (fundamentals) + TrendSpider (charts) + Danelfin (AI score) + a sentiment feed + EDGAR reading — 4–6 subscriptions and manual cross-referencing. One desk that fuses those layers **with validation-grade transparency** is the defensible value proposition.

## 3. Exploiting the FinRL ecosystem — concretely (facts)

**3.1 FinRL ensemble strategy → new tournament legs.** The canonical FinRL result (Yang, Liu et al., *Deep RL for Automated Stock Trading: An Ensemble Strategy*, ICAIF 2020; implemented in the FinRL repo) trains **PPO, A2C and DDPG in parallel and selects the best agent per quarter by rolling validation Sharpe, with a turbulence-index circuit breaker** that liquidates in extreme regimes. This maps 1:1 onto our architecture: each ensemble member becomes a tournament candidate; the quarterly-Sharpe selection is a special case of our walk-forward scorer; the turbulence gate is our S3 `turbulence_20d` + regime overlay. **Action:** implement the ensemble trio as research-container candidates and surface the *per-quarter selection history* in the UI — no other retail product shows that.

**3.2 FinRL-X composition.** The weight-centric four-layer architecture (data→strategy→backtest→execution; selection/allocation/timing/risk stages) is already our pipeline's shape (Phase 18J audit). Remaining exploitation: adopt its per-stage attribution reporting into the desk's model section.

**3.3 FinGPT → finance-tuned sentiment we currently lack.** FinGPT (AI4Finance) publishes **LoRA-fine-tuned financial sentiment models (v3 series: Llama2-7B/13B, ChatGLM2-6B bases) that achieve top scores on most financial sentiment benchmarks at low cost**, trained on news+tweets datasets, plus FinGPT-RAG (retrieval-augmented sentiment) and the FinNLP data pipelines; checkpoints are on HuggingFace. Our current `news_sentiment` engine is lexicon-grade. **Action:** add a FinGPT-scored sentiment leg (research-worker inference or hosted endpoint), A/B-logged against the current scorer inside the dossier so the improvement is *measured on screen*, not asserted. FinGPT's own docs caution direct quant use of raw outputs — which our validation framing already handles.

**3.4 Constraint that stays true:** torch remains research-container-only on the current deployment. RL/FinGPT legs therefore run on a **dedicated research worker** (new Railway service or scheduled local runs) feeding artifacts through the existing 8E import path. This is E-item E7 (operator: one service + budget); with it absent, legs degrade honestly exactly as today.

## 4. Data-layer expansion (facts, with caveats)

| Source | What it adds | Facts / caveats |
|---|---|---|
| **Finnhub social sentiment** | Reddit + Twitter sentiment per ticker — the social/forum dimension the operator asked for | Documented endpoint (`/stock/social-sentiment`); third-party comparisons report it is **not unlocked on the free tier** — assume paid tier; verify before committing UI |
| **Finnhub insider sentiment (MSPR)** | Monthly insider buy/sell pressure, −100..+100 | Documented; practitioner analysis (Robot Wealth) finds the raw signal noisy — render as context gauge, never as a signal claim |
| **Finnhub filings NLP** | Filing sentiment (Loughran–McDonald word lists) + **10-K/10-Q similarity index** (year-over-year language-change detection — a documented change-in-disclosure signal) | Documented endpoints; complements our in-house EDGAR extraction |
| **SEC XBRL `companyfacts`** | Free, official, structured fundamentals (revenue, margins, debt, share counts) for ratio trends | data.sec.gov JSON API, no key, rate-limited by user-agent policy |
| **Keyless social fallbacks** | ApeWisdom (mentions/buzz, free, no key), StockGeist free tier | Mentions-only vs scored sentiment — label the difference honestly |
| Already in-house | News ingestion, EDGAR filings text, Finnhub fundamentals pattern, S9 sourced annotations | Wire into the desk, most is dark today |

## 5. The Analyst Desk — one long, dense, dynamic screen (UX blueprint)

Design language: the **Pro design system** (GlassCard/AdminShell aesthetics, existing tokens), framer-motion (already a dependency) for section transitions and number animation, Recharts for all series, **each section streamed independently** from its own endpoint with skeletons — the page assembles progressively, which is both the "dynamic" feel and the degradation model. Route: `/desk/[ticker]` (Pro namespace; Simple Mode stays as the light entry that upsells into the desk). Command palette (⌘K, already built) jumps between sections. Sticky mini-map rail tracks scroll position across sections.

Top-to-bottom sections (each with its evidence drawer and provenance stamps):

1. **Command header (sticky):** ticker, live-ish price, stance/regime chips, composite gauges animating on change, freshness, Export, Add-to-compare, section mini-map.
2. **Master chart:** price with regime shading bands (requires DEBT-S5-2 band series), volume, drawdown subpane, **event markers** — news items, filings, insider clusters, tournament rebalances — hoverable to their evidence; range/indicator toggles.
3. **Signal matrix:** every computed feature (all of S3+legacy, not 3) as a heat-tile grid: value, percentile vs its own history, sparkline, plain-language read; click → methodology drawer. This is our answer to Danelfin's alpha-signals panel — but each tile links to *how it's computed*, not just that it exists.
4. **Model tournament arena:** animated leaderboard; per-candidate equity curves overlaid vs buy-and-hold; **walk-forward split visualization** (train/validation windows drawn on the timeline); penalty decomposition bars; winner rationale; selection-history strip (which model won each period — the FinRL-ensemble view).
5. **RL research lab:** ensemble members' status; when the research worker runs: training reward curves, per-quarter selection, turbulence circuit-breaker events — all under the existing isolation labeling. When absent: the honest queued state with what would appear.
6. **News & social tape:** dual-lane stream (media vs social) with per-item sentiment chips from both scorers (lexicon vs FinGPT) side-by-side, S9 "why it matters" lines, 7/30-day sentiment ribbons, divergence flag when media and social disagree.
7. **Filings intelligence:** XBRL ratio trend sparklines (revenue, margins, leverage, dilution); latest 10-K/10-Q with the **similarity-index delta** ("disclosure language changed materially vs last year") and Loughran–McDonald tone; links into our EDGAR extracts.
8. **Insider & flow panel:** MSPR gauge with the explicit noisy-signal caveat; recent transactions table.
9. **Peers & relative:** auto-selected comparables (sector/GICS — debt item), relative performance and signal-matrix deltas; one-click into `/compare`.
10. **Risk & scenarios:** volatility/turbulence percentile dials, drawdown history, regime timeline.
11. **Decision journal hooks (Pro):** capture-analyst-note, deep-link to `/pro/decision`.
12. **Disclaimer strip** (non-dismissible) + full provenance drawer.

Dynamics rules: numbers count-in once on load (no perpetual animation noise); sections lazy-mount on scroll; every color has a text label (F3 discipline); nothing renders without a source; degraded sections state what's missing and why.

## 6. Value proposition — market analysis for the experienced investor

**Consolidation economics:** replicating this desk today costs roughly Danelfin Pro (~$49/mo) + TrendSpider (from ~$39/mo) + a fundamentals platform + a sentiment feed + manual EDGAR work — $100–200+/mo across 4–6 tabs with **zero shared provenance** between them. One desk with one provenance model is, by itself, the product.

**The transparency edge (unique):** Danelfin's explainability stops at "these features drove the score." Our desk goes one layer deeper — *"these competing models were validated out-of-sample on this ticker; here are the splits, the divergence, the penalties, and why this one won; here is the RL leg's real status."* No retail product exposes validation-grade model selection; that is institutional-desk material made legible.

**RL made honest and usable:** FinRL's ensemble is famous in the literature but unusable by non-programmers. Shipping it as visible tournament candidates with per-quarter selection history and turbulence gates gives an experienced investor the substance of the ICAIF ensemble paper **as a product surface** — with the overfitting discipline the literature demands baked into the scoring (our deflated penalties), rather than the optimistic backtests the field is criticized for.

**Positioning sentence:** *the only research desk where every automatic conclusion — technical, sentiment, fundamental, and machine-learned including RL — arrives with its out-of-sample evidence attached.*

## 7. Roadmap addendum — Track A (Analyst Desk), council-run, zero-questions

| Phase | Objective | Key work (repo-grounded) | Gates (beyond U1–U9 + council) | Est. |
|---|---|---|---|---|
| **A1** Data expansion | Filings + insider + XBRL live | SEC `companyfacts` client (keyless) + ratio series; Finnhub insider-sentiment + filings-sentiment + similarity-index adapters behind provider flags; dossier sections `fundamentals`, `filings`, `insider` become real with per-section availability | Contract tests per adapter; keyless paths always work; caveat copy wired | 3h |
| **A2** Sentiment duality | Social lane + FinGPT leg | Social-sentiment adapter (Finnhub paid-tier flag; ApeWisdom keyless fallback labeled "mentions"); FinGPT scorer on research worker with A/B logging vs lexicon scorer into the dossier | Divergence computation tested; A/B numbers rendered, never asserted | 3h |
| **A3** FinRL ensemble | PPO/A2C/DDPG legs + selection history | Research-container ensemble runner per ICAIF recipe (quarterly Sharpe selection, turbulence gate) → 8E import → tournament candidates + selection-history artifact | Isolation regression; budget caps; honest degradation (E7 absent) | 4h |
| **A4** Dossier v2 payload | Everything §5 needs in one contract | Regime band series (closes DEBT-S5-2); event-marker feed (news/filings/insider/rebalances); full signal-matrix payload with percentiles+sparklines; split-visualization data; section-level endpoints for streaming | Payload schema tests; byte-stable engine-config versioning | 3h |
| **A5** The Desk UI | §5 sections 1–12 at `/desk/[ticker]` | Pro design system + framer-motion; streamed sections; master chart with event markers; tournament arena; signal matrix; tapes; mini-map | Structural DOM tests per section; wording tests extended; **screenshot evidence mandatory before any visual claim** (standing rule) | 6h |
| **A6** Live dynamics | The desk feels alive | Section revalidation on freshness change; score-change animations; alert hooks into S8 notifications; compare-from-desk | No-perpetual-animation rule tested; perf budget M1 gates | 2h |
| **E7** (operator, once) | Research worker | One Railway worker service (torch) or scheduled local runs; optional Finnhub paid tier for social | — | — |

## 8. Council notes on this report
**Quant Skeptic:** every performance number above is a vendor's own backtest and is labeled as such; nothing here relaxes the deflated-penalty scoring; FinGPT/insider signals enter as *displayed context or A/B-measured legs*, never as unvalidated inputs to stances. **Truthfulness Auditor:** the desk renders no signal without provenance; MSPR and social lanes carry explicit noise caveats; social endpoint tier caveat retained until verified. **UX Critic:** density with progressive disclosure, not density as clutter; the mini-map + streamed sections are the mechanism. **Security/Ops:** all new adapters behind flags with keyless fallbacks; SEC UA policy respected; no new frontend deps.

## 9. References
Danelfin — how-it-works & product pages (AI Score, 10k+ features, explainable panel, backtest claims) · TrendSpider / Trade Ideas / Kavout / AltIndex feature documentation via 2026 tool roundups (prospero.ai, chartinglens, steadyincomeinvestments) · Yang et al., *Deep RL for Automated Stock Trading: An Ensemble Strategy*, ICAIF 2020 + AI4Finance FinRL repo · FinRL-X arXiv:2603.21330 · FinGPT: arXiv:2306.06031 + AI4Finance-Foundation/FinGPT (v3 LoRA sentiment models, FinGPT-RAG, HuggingFace org) · Finnhub API docs (social sentiment, insider MSPR, filings sentiment, similarity index) + Robot Wealth MSPR analysis + Adanos 2026 sentiment-API comparison (free-tier caveat) · SEC EDGAR XBRL companyfacts API · Internal: PHASE_18J audit, PROGRAM_LEAP close report, deployed dossier v1.
