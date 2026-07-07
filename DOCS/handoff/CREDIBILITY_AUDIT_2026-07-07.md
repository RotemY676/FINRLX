# FINRLX — INDEPENDENT MARKET SURVEY & PRODUCT CREDIBILITY AUDIT
**Engagement style:** management-consulting review (situation → evidence → root cause → options → recommendation)
**Date:** 2026-07-07 · **Trigger:** operator verdict after two production screenshots: "continues to look unprofessional and disappointing" — the operator is right, and this report explains precisely why, without excuses.

---

## 1. Executive summary

**The strategy survives this audit. The execution posture does not.**

The market thesis behind FINRLX — an evidence-first research desk whose every automatic conclusion carries out-of-sample validation — is *more* supported by 2026 market data than when it was formulated: 62% of US retail investors now use AI in investment decisions, yet 54% say they only "somewhat" trust AI output and verify it elsewhere, and the single most-cited fear (38.9%) is incorrect or misleading AI recommendations. Regulators (OSC 2026) name the "black box" problem and data quality as the sector's core risks. A product whose identity is *verifiable transparency* is aimed at the exact center of the market's trust gap.

**But the deployed product currently violates the very trust standard it sells — and the two screenshots prove it:**

- **Finding A — a wall of "—" (em-dashes).** The production Simple dossier for UMC renders *every* technical signal — return_5d through news_count_7d, nine rows — as a dash. A transparency product whose signal panel is 100% empty is not "honest degradation"; to a user it is indistinguishable from *broken*. No benchmark competitor ever shows this state.
- **Finding B — two prices for one ticker on one site.** The Simple dossier says UMC = **25.83**. The Research workspace, one click away, charts UMC at **~200–240** with "vs S&P +13.7%", a "Confidence band", "0 events", "0 news items." That second chart is a **synthetic/demo data path still live in production**. Nothing destroys credibility with an experienced investor faster than a product that cannot agree with itself on the price of a stock. This single defect outweighs every feature shipped in the last two days.
- **Finding C — UI shipped blind.** Three UI waves (Simple Mode, /pro migration, Analyst Desk) were built and merged from an environment with **no browser**. Every merge honestly carried "visual sign-off pending" — which means, bluntly: *the product's look has never once been verified by its builder before the operator saw it.* Structural DOM tests passed; the experience failed. Predictably.
- **Finding D — engineering without design authority.** Default-radius cards, chip-soup headers, no chart on the first screen of Simple Mode, monospace feature keys (`return_5d`) leaking into user-facing UI. Benchmarks (Danelfin's score panels, TrendSpider's charts, Barebone's "visual ratings built for a phone screen") treat visual communication as the product; FINRLX currently treats it as a rendering of JSON.

**Verdict:** stop feature development. The next unit of work is not a feature — it is **credibility**: one price truth, zero demo data, zero dash-walls, and a mandatory see-it-before-ship loop. The strategy deserves an execution posture worthy of it.

---

## 2. Market context (evidence, 2026)

**Adoption & trust.** Investing.com's March-2026 survey (n=938 US investors): 62% use AI for investment decisions; 65% of users report improved performance; usage concentrates on research (62%), news interpretation (35%), idea generation (34%). Critically for FINRLX: **54% trust AI output only "somewhat" and verify against other sources; 38.9% fear incorrect/misleading AI recommendations; 24.2% fear herding.** The Ontario Securities Commission's research program flags black-box opacity and data quality as the sector's structural risks. → The willingness to pay is migrating toward tools that *show their work*. That is FINRLX's declared identity.

**Price architecture of the category.** Entry AI research: $0–19/mo (WarrenAI $19; Magnifi $14). Explainable scoring: Danelfin ~$49/mo tiers. Pro technicals: TrendSpider from ~$39/mo. Scanning: Trade Ideas ~$1,068–2,136/yr. Bot aggregators: $60–250/mo with "win-rate marketing [that] deserves skepticism" (Barebone's 2026 review — note that *reviewers now audit honesty claims*, which favors us if and only if the product itself is impeccable). A validated-transparency desk consolidating 4–6 of these has a defensible $30–80/mo anchor — but only from a product that never shows a dash-wall or a contradictory price.

**What "professional" concretely means in 2026 benchmarks** (synthesis of the reviewed leaders): (1) real data visibly fresh on every element; (2) an opinionated visual system — scores as dials/badges, signals as heat, never raw keys; (3) charts as the centerpiece, not an appendix; (4) empty states that *explain and offer an action*, never a grid of placeholders; (5) mobile-first density; (6) one source of truth per number, everywhere.

---

## 3. Root-cause analysis — why it *keeps* looking unprofessional

This is the consulting core. Four systemic causes, not one bug:

**RC1 — The data layer was never production-proven.** Development validated the *engine* with synthetic bars and mocks (correctly, for logic), but no gate ever asked: *"for a real ticker, on the deployed system, do the signals actually populate?"* The UMC dash-wall means the deployed feature computation returns null/missing across the board (provider chain failing, insufficient history via the production path, or serialization loss). We test what the code does; nobody tests what the user sees with production data. **A "works on fixtures" culture produced a product that demos its own emptiness.**

**RC2 — Demo/synthetic paths shipped to production.** The Research workspace chart (Finding B) is a pre-LEAP surface still rendering fabricated series ("Confidence band", benchmark deltas) with zero events/news. The /pro migration moved these pages without auditing their data honesty. A transparency product may never render a number it cannot source — that rule was enforced on the *new* surfaces and never swept across the *old* ones.

**RC3 — The build loop has no eyes.** This environment cannot run a browser; production hosts are network-blocked from it. Every visual claim was structurally tested and visually unverified — the P3 ledger said so on every merge, accurately and uselessly. **Process conclusion: UI work performed where it cannot be seen will keep disappointing, with probability ~1.** UI development must move to an environment with a browser (Claude Code), where every merge produces screenshots *before* the operator ever loads the page.

**RC4 — No design authority.** The program has a Quant Skeptic, a Truthfulness Auditor, an Ops reviewer — and a "UX Critic" who reviews *markup*, not *pixels* (see RC3). No reference designs, no typographic scale decisions, no chart-first composition rule. Engineering defaults filled the vacuum. Professional look is not emergent from clean code; it is a designed artifact with its own gate.

**RC5 (compounding) — Breadth before bedrock.** The program shipped 12 desk sections, ensembles, and sentiment lanes on top of a data foundation that couldn't reliably show *one* ticker's return_5d in production. Sequencing error: features multiplied the surface area over which the emptiness shows.

---

## 4. Strategic options

| Option | Description | Assessment |
|---|---|---|
| **A. Continue feature roadmap** (V1, polish desk) | More capability on the current foundation | Rejected. Multiplies the credibility deficit; every new empty panel is new evidence against the product |
| **B. Credibility-first recovery** (recommended) | Freeze features; fix truth, data, empty-states, and the visual loop; re-skin core screens against reference designs; only then resume the desk | Directly attacks RC1–RC5; fastest route to a product the operator can show anyone |
| **C. UI rebuild on a purchased template/design system** | Adopt a commercial fintech dashboard kit wholesale | Partial merit (imports design authority) but doesn't fix data truth (RC1/RC2), which the screenshots show is the deeper wound; considered inside B's re-skin step |

---

## 5. Recommendation — "Operation Credibility" (2 phases, features frozen)

**Phase K1 — Truth (before any pixel changes):**
1. **One price, one source.** Single price/series service consumed by *every* surface; a contract test asserts Simple, Desk, Research, Compare render identical closes for the same ticker+date. **Kill or gate every synthetic/demo series in the repo** (audit: Research workspace chart, any "confidence band" generators, placeholder benchmarks). If a surface has no real data, it says so — it never draws fiction.
2. **Production data readiness.** A provider-health matrix (per source: last success, coverage, staleness) surfaced at /pro/ops AND checked by a deploy gate against a 10-ticker real-world QA list (UMC included). Root-cause and fix the UMC dash-wall specifically: trace `return_5d=null` end-to-end on production data.
3. **Empty-state doctrine.** ≥3 missing signals ⇒ collapse the grid into ONE explanatory card ("Signals need N sessions of history from <source>; currently <status>") with a retry/details affordance. A dash may appear for a single missing value; a *wall* of dashes may never render. Enforced by test.

**Phase K2 — Eyes and skin:**
4. **Visual QA loop becomes a merge gate.** All further UI work happens in a browser-equipped environment (Claude Code). Every UI merge attaches screenshots (desktop+mobile) of affected screens; "visual sign-off pending" is abolished as an acceptable end-state — if it can't be seen, it doesn't merge.
5. **Design pass with authority.** Adopt a reference standard (Danelfin score panels / TrendSpider chart density as visual benchmarks): chart-first Simple dossier (price sparkline top-of-card), human signal names ("5-day return", never `return_5d`), score dial for the composite, one accent color system, typographic scale. Scope: Simple dossier + Desk header/chart/matrix — the screens an investor judges in the first 10 seconds.
6. **Then** resume the desk (V1 screenshots close the P3 ledger as part of gate 4).

**Effort estimate:** K1 ≈ 1–2 working sessions; K2 ≈ 2–3 sessions in the browser-equipped environment. Zero new features until both close.

**KPIs for "professional":** (P1) same ticker+date ⇒ identical price on all surfaces (automated); (P2) 10-ticker QA list shows ≥90% signal population in production, zero dash-walls; (P3) every UI merge carries screenshots; (P4) zero synthetic series rendered anywhere; (P5) operator loads UMC and the first screen contains a real chart, populated signals, and no placeholder text.

## 6. What is required from the operator
Only two things gate K1: production environment variables for the data providers (Finnhub key presence/validity on Railway; confirmation SEC egress is permitted from Railway), and moving UI work to Claude Code sessions (K2.4). Everything else is mine to execute.

---
*Sources: Investing.com retail-AI survey (Mar-2026, n=938) and coverage (Traders Magazine, Advisor Magazine); OSC "AI and Retail Investing" research; Barebone AI 2026 apps review (pricing, standards); monday.com 2026 platform comparison (WarrenAI, Danelfin, Composer pricing); prior FINRLX competitive research (Danelfin/TrendSpider/Trade Ideas/AltIndex, 2026-07-06); production screenshots IMG_3938/3939 (2026-07-07); repository state at main d7eca5b→6adbc6d.*
