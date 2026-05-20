---
name: fintech-disclaimer-and-marketing-guard
description: Lints user-facing copy and templates for prohibited fintech marketing verbs ("guaranteed", "advice", "risk-free", etc.) and enforces disclosure on every Recommendation render. Run on any change to frontend pages, email/marketing copy, or recommendation rendering paths.
type: project
---

# Fintech Disclaimer & Marketing Guard

A FINRLX-internal guard that protects the product from compliance accidents while we are still pre-licensed. Two responsibilities:

1. **Forbidden verbs** — block phrasing that crosses the line from "decision-support tool" to "investment advice".
2. **Disclosure presence** — ensure every surface that renders a `Recommendation` also renders the standard disclaimer banner.

## When to invoke

Run this skill whenever the change touches:
- `frontend/app/**/*.{tsx,ts}` — any page or component
- `frontend/app/**/page.tsx` for marketing / landing surfaces
- Email / outbound templates (`backend/app/templates/**`)
- Any Recommendation card or recommendation detail screen
- Copy reviewed by humans for the beta tester invite pack

Also run before a release tag is cut.

## Forbidden verbs / phrases

These trigger a hard fail. They are language that implies advice, guaranteed outcome, or that the product is a licensed broker/advisor:

| Pattern (case-insensitive) | Why it's banned |
|---|---|
| `guaranteed` | Implies certainty of outcome — banned in marketing finance copy worldwide. |
| `risk[-\s]?free` | Same. There is no risk-free trade. |
| `we recommend (you|that you)` | Crosses from "this is our model's recommendation" to "we (the firm) recommend" — that's advice. |
| `financial advice` | We do not give financial advice. We provide decision-support output. |
| `investment advice` | Same. |
| `(buy|sell) now` as a CTA | Imperative trading direction reads like an investment instruction. |
| `outperform[s]? the market` | Performance claims need backing data + compliance review. |
| `(double|triple|10x) your (money|returns)` | Outcome claims. |
| `proven returns` | Outcome / backtest cherry-picking signal. |
| `expert[- ]?level (advice|recommendations)` | "Advice" again. |

These trigger a **warning** (allowed if a disclaimer is co-located in the same render):

| Pattern | Acceptable when |
|---|---|
| `should buy` / `should sell` | OK inside a Recommendation card that is *clearly* labeled "Model recommendation" and the disclaimer banner is visible. |
| `confidence` | OK when accompanied by the triple (model / data / operational) shown on Decision Workspace. |
| `winning trade` / `winners` | OK on internal analytics / debug surfaces only. |

## Disclosure presence rule

Every component that imports / renders a `Recommendation` object must, in the same render tree, include the `<DisclaimerBanner />` component (or an equivalent `data-disclaimer="true"` element). Acceptable layouts:

- Banner pinned to the bottom of the page (`<RecommendationCard />` + `<DisclaimerBanner />` siblings under one route layout).
- Inline footer below the card (`<RecommendationCard><DisclaimerBanner /></RecommendationCard>`).
- Modal that has already been accepted in the session AND a persistent footer.

A page that renders a Recommendation with no disclaimer anywhere in its tree is a hard fail.

## How to apply

When invoked on a code change:

1. Grep the changed files for the forbidden patterns above (case-insensitive, word-boundary aware where noted).
2. For every changed/new file under `frontend/app/**` that imports a Recommendation type (`from "@/lib/api/recommendations"` or similar), search the same file (and its layout chain) for `DisclaimerBanner` or `data-disclaimer="true"`.
3. Report findings as either:
   - **BLOCK** (forbidden verb hit, or Recommendation rendered without disclaimer)
   - **WARN** (acceptable verb in ambiguous context)
   - **OK**

When finding a BLOCK, propose a concrete replacement. Example:
- ❌ "We recommend buying AAPL with high confidence."
- ✅ "Our model is overweight AAPL at this scan (model confidence 0.82). This is not financial advice — see disclaimer."

## What this skill does NOT do

- Does not run a real regulator-grade compliance review. It is a tripwire, not a lawyer.
- Does not check chart styling, color choices, or trademarks.
- Does not check backend data correctness; that is the backtest-hygiene-gate.

## Reference

- US: FINRA Rule 2210 (Communications with the Public)
- EU: MiFID II Article 24 (fair, clear, not misleading)
- The FINRLX MVP plan explicitly defers any "advisor" framing until we obtain the relevant licenses; until then, every surface MUST read as "decision-support tool".
