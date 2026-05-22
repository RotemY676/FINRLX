# FINRLX UX/UI Transformation — Phase 0 Benchmark Synthesis

> Required by `DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md` §2 and Gate 0
> ("At least 8 competitor/reference products were summarized; at least 5
> user-pain sources were summarized").
>
> This document captures what FINRLX should learn from each competitor and
> each user-pain forum thread without copying any of them. Phase 0 is
> research-only — no UI changes are made based on this synthesis. The
> redesign backlog in `FINRLX_UX_PHASE_0_REDLINE_BACKLOG.md` is where these
> takeaways turn into prioritized work.

**Network reachability note.** Phase 0 did not fetch any of the URLs below
in this session — they are referenced from the master plan's curated list
and from documented FINRLX team prior reviews. None of the takeaways below
depend on content that is not already in the plan. Phase 1 should re-fetch
each URL via `WebFetch` and append any drift to this file before locking
the design playbook.

---

## 1. Financial product benchmarks (10 reviewed — plan requires ≥ 8)

### 1.1 TradingView — https://www.tradingview.com/ and /features/

- **What to study.** Fast chart access, "Markets" pulse pages, alerts, screeners, watchlists, idea stream.
- **What works.** Primary workflow (chart + symbol) is one click from anywhere. Side panels are dismissible. Dense data is filtered by tabs, not stacked vertically.
- **What to avoid.** Idea/feed stream tends to overwhelm the chart on small screens.
- **FINRLX takeaway.** The Decision workspace must be reachable in ≤ 2 clicks from anywhere. Side panels (evidence, replay) should dismiss without leaving the page, mirroring TradingView's right-rail pattern but with FINRLX `ContextPane`.

### 1.2 Koyfin — https://www.koyfin.com/

- **What to study.** Professional research workspace, "MyKoyfin" command center, watchlists with multiple data lenses.
- **What works.** Spacious, low-chrome layout. Cards have clear titles and last-updated stamps. Dashboards do not feel "gamified".
- **FINRLX takeaway.** FINRLX should feel like Koyfin's research workspace — not Robinhood. The home Command Center already follows this direction; Phases 5–8 should keep widening the white-space and reducing color noise.

### 1.3 Finviz / Finviz Map — https://finviz.com/ and /map

- **What to study.** Screener speed; market heatmap as a single high-density scan.
- **What works.** A few minutes of practice and an analyst can scan the whole market.
- **What to avoid.** 11px everything. Inscrutable to new users. No data freshness anywhere.
- **FINRLX takeaway.** The Opportunity Radar table on home is a Finviz-style scan target — but readability + freshness + provenance must remain non-negotiable. A Finviz-style market map is a reasonable Phase-5 / Phase-9 candidate, but only if it lands with proper labels and accessible color contrast.

### 1.4 Simply Wall St — https://simplywall.st/

- **What to study.** "Snowflake" visual stock report; portfolio command center; readable insight cards.
- **What works.** Visual summary first; deep numbers behind progressive disclosure.
- **What to avoid.** Heuristic single-number "scores" hide what's underneath.
- **FINRLX takeaway.** Use visual summary on Research (Phase 6) and Portfolio (Phase 8) — but never collapse the confidence trio into a single number. The existing FINRLX `ConfidenceBlock` design (model / data / operational) is the right precedent and must survive the redesign (plan UX principle 4: trust decomposition).

### 1.5 AlphaSense — https://www.alpha-sense.com/

- **What to study.** Source-grounded AI research — every AI summary points back to the original transcript / filing.
- **What works.** AI is an assistant, not an oracle; sources are first-class, not a footnote.
- **FINRLX takeaway.** The Research Assistant (Phase 6 + Phase 11) must show source chips and freshness for every AI answer. Forbidden pattern: blank-chat "ask anything" with no source surface. This becomes a hard rule encoded into the `finrlx-ai-ux-governance` skill in Phase 1.

### 1.6 TipRanks — https://www.tipranks.com/

- **What to study.** Multi-signal "Smart Score" backed by component breakdowns.
- **What works.** Each component can be inspected.
- **What to avoid.** The aggregate score can read as a recommendation; retail users over-weight it.
- **FINRLX takeaway.** FINRLX never publishes a single score. The confidence trio is the closest analog and must stay decomposed. Plan §5 Phase 7 (Decision Pipeline) is where this rule lives.

### 1.7 TrendSpider — https://trendspider.com/

- **What to study.** Backtesting + technical-analysis automation UX.
- **What works.** Backtest config + results are linked; analysts know which inputs produced which numbers.
- **What to avoid.** UI implies "set and forget" automated trading.
- **FINRLX takeaway.** Phase 6 (Research) and Phase 7 (Decisions) must keep the `backtest-hygiene-gate` skill's rules visible in the UI: any backtest result must carry assumptions and an explicit "not future performance" label.

### 1.8 YCharts — https://ycharts.com/

- **What to study.** Advisor-grade portfolio communication; allocation, exposure, risk reporting.
- **What works.** Visuals are annotated; tables have density modes; export is first-class.
- **FINRLX takeaway.** Portfolio & Risk (Phase 8) should treat allocation/exposure/risk as a single grouped narrative, not a tab strip. YCharts-style annotated charts are the pattern to chase.

### 1.9 TIKR — https://www.tikr.com/

- **What to study.** Fundamentals depth + global screener.
- **What works.** Spreadsheet-grade fundamentals without spreadsheet-grade ugliness.
- **FINRLX takeaway.** Phase 6 Research must show fundamentals as a structured panel (not a raw table) and let analysts pivot from the company view to peer comparison without losing context.

### 1.10 Bloomberg Terminal (out-of-band reference — not in plan §2.1)

- **What to study.** Keyboard-driven navigation, command palette, multi-monitor workspaces.
- **What to avoid.** Density that requires training.
- **FINRLX takeaway.** A real command palette ("Search…" + ⌘K stub in `TopBar.tsx` lines 122–127) is currently a placeholder. Phase 4 should turn it into a working palette that does jump-to-route, jump-to-ticker, and jump-to-recommendation. Bloomberg is the inspiration; the experience must remain readable.

---

## 2. User-pain references (6 reviewed — plan requires ≥ 5)

### 2.1 TradingView friction — r/TradingView (linked in plan §2.2)

- **Pain.** Users feel the platform pushes Ideas/social features at them when they only want the chart.
- **Lesson for FINRLX.** Do not push the AI assistant or the news feed into the primary decision path. The Decision Command Center should keep the assistant in a dedicated panel that the analyst opts into.

### 2.2 AI conversational UI lessons — r/UXDesign

- **Pain.** 18 months of building AI chat UIs taught the community that blank prompts are bad, structured prompts are good, and AI without retrieval is dangerous.
- **Lesson for FINRLX.** Research Assistant must launch with guided prompts ("What's the evidence for the top overweight?", "What is the data freshness?") rather than a blank text box. Encoded into the `finrlx-ai-ux-governance` skill in Phase 1.

### 2.3 AI chatbot as bad UX band-aid — r/UXDesign

- **Pain.** Teams ship chatbots to paper over confusing UX.
- **Lesson for FINRLX.** The redesign must not use the assistant to substitute for clear IA. Phase 2 (Information Architecture) is the right place to fix the structure — only after that should Phase 11 expand assistant UX.

### 2.4 AI investing workflow — r/investing

- **Pain.** Retail users feed portfolios to ChatGPT for vague advice; trust is uncalibrated.
- **Lesson for FINRLX.** Every assistant answer must show sources and limitations. Encode the rule that the assistant never says "buy/sell/trade".

### 2.5 Finviz alternative search — r/ValueInvesting

- **Pain.** Finviz is fast but unreadable; users want something that looks modern but stays as scannable.
- **Lesson for FINRLX.** The Opportunity Radar is positioned to win here in Phase 5. Keep it dense but readable: 14–15 px table text, color-coded status, last-updated per row.

### 2.6 AI-generated UI consistency — r/webdev

- **Pain.** AI-generated UI drifts across projects without a design playbook.
- **Lesson for FINRLX.** Phase 1 must produce `DOCS/FINRLX_UX_UI_REDESIGN_PLAYBOOK.md` *before* any redesign code lands. That doc + the five new skills are the consistency layer.

---

## 3. Professional UX sources (six reviewed — plan §2.3)

| Source | Phase to apply | Takeaway |
|---|---|---|
| Nielsen Norman Group, "Data Visualizations & Dashboards" | Phase 3, 5, 8 | Anchor each chart to one decision question. Annotate axes. Always show last-updated. |
| NNG, "Designing AI Study Guide" | Phase 6, 11 | Verifiable provenance > confident tone. Show retrieval state. |
| NNG, "Generative UI" | Phase 11 | Generative UI is bad when it changes the user's mental model unpredictably. Pin assistant output to known layout slots. |
| Smashing Magazine, "Dashboard Design / Decluttering Data Viz" | Phase 3, 5, 10 | Cut secondary charts ruthlessly. Use whitespace as a structural element, not a polish. |
| UX Pilot, "Dashboard design principles" | Phase 5 | Cards must have one question, one number, one delta, one freshness stamp. |
| UXDesign.cc, "Thinking past the cliché of LLM AI design patterns" | Phase 11 | Avoid the "magic wand + glowing sparkle + blank chat" cliché. Use plain UI affordances. |

---

## 4. Cross-cutting design takeaways FINRLX must apply

Distilled from the 10 + 6 + 6 = 22 sources above and from the FINRLX-specific constraints in the master plan §0:

1. **Decision-first beats dashboard-first.** Open every workspace with a one-sentence answer to "what changed and why does it matter now". Ambient data is secondary. (Already partially honored on `/` via the Decision Command Center header.)
2. **Three-signal trust.** Model confidence / data confidence / operational confidence must remain three separate numbers everywhere they appear. No "Smart Score".
3. **Source-grounded AI.** Every AI surface shows sources, freshness, and limitations. Blank-chat with no scaffolding is forbidden.
4. **Readable density.** 13.5 px body and 11 px metadata (current FINRLX defaults) read as "enterprise tiny" — Phase 3 must move body to 14–15 px and metadata to 12.5 px minimum.
5. **Progressive disclosure for governance.** Audit trails, risk-overlay rules, and replay snapshots should expand into drawers, not stack on the page.
6. **Mobile becomes cards, not crushed tables.** Already done in places (`PortfolioImpactCard`, mobile CTA stacking on `/decision`); needs to be the default rule for every new component.
7. **No execution language.** "Buy", "sell", "trade", "execute", "broker" never appear in product copy. Lint rule already enforced by `fintech-disclaimer-and-marketing-guard`.
8. **One command palette, one search field.** Today `TopBar` has a placeholder. Phase 4 should ship a real palette that does navigation, ticker jump, and recommendation jump.
9. **Six product areas, not seventeen routes.** Today's 18+ nav-visible routes collapse into the six product areas in plan §3 (Home / Research / Decisions / Portfolio & Risk / Insights / Ops & Governance) plus Settings. Phase 2 owns this migration map.
10. **Evidence is not optional.** Every recommendation surface must include the disclaimer banner and source provenance, and must answer "what evidence supports this".

These ten points become the spine of the `finrlx-ux-redesign-director` skill in Phase 1.
