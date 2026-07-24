# FINRLX — Product Survey: the Analyst Desk (`/pro/desk/[ticker]`)

**Date:** 2026-07-24 · **Trigger:** operator review of the live NVDA desk.
**Verdict in one line:** the desk has *honest, real* analytics underneath, but the
**presentation, information architecture, and a handful of data-integrity bugs**
make it read as unprofessional and untrustworthy. None of the problems are fatal;
several are architectural and should be fixed before any new feature work.

This is a **survey + insight document**, not a change. No code was modified to
produce it. Findings are graded and evidence-linked so the next development
phase can be planned and gated (Council, Rule 6).

---

## 1. What the product is trying to be

A **decision-support desk**: point at a ticker, and get a defensible research
read — a stance (buy/hold/trim), the evidence behind it, and the ability to drill
into each lane (technical, model tournament, news/social, fundamentals, sector).
The differentiator is **honesty**: nothing simulated, every number traceable, RL
models shown only when really trained.

That honesty engine mostly works. The **product wrapper around it does not yet.**
A user cannot tell *what the call is, why, how confident, and what to do next* —
which is the entire job of a decision tool.

---

## 2. Severity-graded findings (grounded in the live NVDA desk)

### 🔴 P0 — Credibility-breaking (fix first; these make users distrust everything)

**D1 · Fundamentals are mislabeled by ~2 fiscal years and look stale.**
The XBRL revenue series is labeled `FY2026 → $60.9B`, but that row's period
`end` is **2024-01-28** — it is NVIDIA's *fiscal 2024*. The series tops out at
$60.9B while the provider snapshot (same payload) reports **TTM revenue ≈ $251B**.
So the panel presents ~2.5-year-old figures as "latest," and anyone who knows
NVDA sees numbers that are obviously wrong. Root cause: the `fy` label is derived
inconsistently across XBRL concepts (revenue is offset; `shares_outstanding` is
not), so the fiscal-year column cannot be trusted and series may be misaligned
with each other in ratios.

**D2 · A stock split is reported as 876% shareholder dilution.**
`shares_outstanding` jumps **2.50B → 24.4B** between FY2024 and FY2025, and the
desk prints **"Share dilution YoY 2025: +876.0%."** That is NVIDIA's **10-for-1
split (June 2024)** — not dilution. The pipeline is not split-adjusting share
counts, so it manufactures a catastrophic-looking (and false) signal on the most
famous split of the decade.

**D3 · "MSPR (latest month) −100.0" reads as broken/constant.**
Insider MSPR is shown as a bare `−100.0` with no month label, no history, and no
scale. −100 is a *valid* Finnhub value ("all insider transactions were sells"),
but presented with no date or trend it looks like a stuck/placeholder value —
exactly the "constant −100" the operator flagged. Honest number, dishonest-looking
presentation.

**D4 · Core technical signals say "insufficient history (<1y)" for a mega-cap.**
`relative volume 20d`, `news sentiment 7d`, `news count 7d` render
"insufficient history (<1y) — percentile omitted" for NVDA, which has decades of
data. Either the history window being fetched is too short, or the percentile
distribution is keyed on the wrong series. Users read "insufficient history" on
NVIDIA as "this tool doesn't have the data."

### 🟠 P1 — The desk looks unprofessional and disorganized (architectural)

**V1 · The desk renders on a separate, hardcoded light palette (`deskTokens`),
divorced from the app's themeable design system.**
DeskV2 styles with `tokens.color.neutral.n*` — a fixed set of light hex values
that "never received the WCAG tuning the main tokens did" (the code says so, and
gate G-3 already caught a 4.12:1 contrast failure from it). Consequence: **light
panels bolted onto the dark app shell**, no working dark mode inside the desk, and
inconsistent styling vs every other page. This is the deepest cause of "looks
unprofessional / a panel of clocks on a white background."

**V2 · The verdict band is `position: sticky; top: 0` with a light background, so
it floats over and covers the panels while scrolling.**
`panels.tsx` sets the header `sticky, top:0, z-40, background: neutral.n100`. On
the dark desk it becomes a pale slab that overlaps the news/fundamentals content
underneath as the user scrolls (visible in all three screenshots). It is the
single most damaging *visual* bug.

**V3 · The six engine dials are decoration, not information.**
The prime top slot is six green circles reading "live." When every lane is "live"
(the healthy, common case) they carry ~zero signal and just look like a "panel of
clocks." They earn their space only in the rare degraded case.

**IA1 · No answer-first hierarchy.**
The actual decision — "hold · evidence 6/6" — is a small chip. A decision tool
must **lead with the call**: stance, confidence, the 2–3 reasons that drove it,
and what would change it. Right now the user scrolls a wall of six equally-weighted
analyst panels and has to reverse-engineer the conclusion.

**IA2 · Everything is expanded at once; no progressive disclosure.**
A→F all render full-depth simultaneously. There is no summary→detail path, so the
page is a long, undifferentiated data dump. Expert density (Bloomberg-style) is
fine *when deliberate and structured*; this is density by default.

### 🟡 P2 — Legibility, relevance, polish

- **C1 · Raw floats to 6 decimals** (`0.006557`, `52.9248`, `1.00091`) everywhere.
  Unprofessional; needs sensible rounding, units (%, σ), and consistent formatting.
- **C2 · Tables show raw + percentile + jargon with no "so what."** Each metric
  needs a one-line plain-language read ("momentum: mildly positive, middle of its
  own range").
- **C3 · The news lane shows non-ticker-relevant headlines** (Microsoft, Bitcoin,
  YouTube, Vanguard ETFs) for NVDA. A market feed masquerading as NVDA news erodes
  trust; it needs relevance filtering or an explicit "market context, not NVDA-
  specific" label.
- **U1 · No "how to read this."** First-time users get no orientation to what the
  desk is or how to use it.
- **U2 · Responsive breakage.** In a narrow column the news lane wraps to roughly
  one word per line; column min-widths and the multi-column grid need rework.
- **(verify) content may render twice** — worth confirming the desk isn't
  double-mounting sections.

---

## 3. Benchmark: what best-in-class decision tools do that we don't

| Principle | Leading products | Our desk today |
|---|---|---|
| **Answer first** | Lead with the call + confidence, reasons on demand | Verdict is a small chip; reasons buried |
| **Progressive disclosure** | Summary card → expand for depth | Everything expanded at once |
| **Plain-language rationale** | "Momentum is weak; valuation stretched" | Raw floats + percentiles, no prose |
| **One coherent design system** | Single themeable token set, dark/light | Desk on a foreign hardcoded light palette |
| **Trust & freshness** | Every number dated + sourced; split-adjusted | Mislabeled FY, split-as-dilution, undated MSPR |
| **Relevance** | Ticker-specific news, ranked | Generic market feed |

The gap is **not** the analytics (those are real and defensible). The gap is
**product craft**: hierarchy, theming, formatting, and data hygiene.

---

## 4. Recommended direction (for approval — not yet built)

**Phase R0 — Data hygiene (P0, ~small, highest trust ROI)**
1. Fix XBRL fiscal-year derivation so `fy` matches the period end consistently
   across all concepts; surface the *actual latest* fiscal periods (reconcile
   with the TTM snapshot so the two can't disagree by 4×).
2. Split-adjust share counts; compute dilution on adjusted shares (NVDA → ~0%,
   not 876%). Add a regression test on the NVDA 10:1 split.
3. Give MSPR a month label + a small sparkline/history and a −100…+100 scale.
4. Fix the technical history window so a mega-cap doesn't report "insufficient
   history"; if a signal genuinely lacks data, say which and why.

**Phase R1 — Desk visual foundation (P1, architectural)**
5. Migrate DeskV2 off `deskTokens` onto the themeable `globals.css` CSS-variable
   system so it inherits dark mode + WCAG-tuned colors and matches the app.
6. Fix the sticky verdict band: solid themed background, correct stacking, and
   either non-sticky or a slim always-legible sticky that never overlaps content.
7. Rework the top: replace the six "live" dials with an **answer-first verdict
   card** (stance, confidence, 2–3 drivers, "what would change this"); demote the
   lane-health dots to a compact strip that only draws attention when degraded.

**Phase R2 — Legibility & relevance (P2)**
8. Formatting pass: rounding, units, plain-language one-liners per metric.
9. Progressive disclosure: each lane = summary card, expand for the full table.
10. News relevance filtering / explicit market-context labeling.
11. Responsive grid fixes + a first-run "how to read this desk" affordance.

**Sequencing rationale:** R0 first because *wrong data* is the fastest way to lose
a user's trust, and it's cheap. R1 next because the theming/sticky bug is what
makes the whole thing "look unprofessional" at a glance. R2 is the long tail of
craft.

---

## 5. What is genuinely good (keep, don't regress)

- The honesty spine: no simulated numbers; RL shown only when really trained; the
  tournament is a real walk-forward selection with a deflation penalty.
- The fundamentals *snapshot* (P/E, margins, 52-week) is real and rich — it's the
  XBRL *series* labeling that's broken, not the data source.
- The regime overlay and evidence markers are a strong, differentiated idea —
  they just need visual restraint and a legend that isn't overwhelming.

---

## 6. Open boundary

The **authenticated** operator surfaces still can't be reviewed from here
(production signup is invite-only). This survey covers the anonymous desk, which
is where the reported problems live. A parallel authed-surface survey is owed once
access exists.
