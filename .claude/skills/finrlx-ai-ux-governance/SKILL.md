---
name: finrlx-ai-ux-governance
description: Governs every AI/LLM/RL/research-assistant surface in FINRLX. Activates on changes to the home Research Assistant Preview, the future /assistant page, the operator console (frontend/src/app/operator/page.tsx), any chat-like component, any RL/FinRL/backtest surface that shows model output, and any imported-research-candidate UI. Enforces source chips, retrieval status, limitations, guided prompts, and the no-execution rule.
type: project
---

# FINRLX — AI/RL UX Governance

The assistant is a research aide, not a decision-maker. This skill keeps it that way.

## When to invoke

- Any change to `frontend/src/components/home/ResearchAssistantPreview.tsx`.
- Any new component under a hypothetical `frontend/src/components/assistant/**` or `frontend/src/app/assistant/**`.
- Any change to `frontend/src/app/operator/page.tsx` (operator console: LLM-context capture).
- Any change to RL/backtest UI under `frontend/src/app/admin/**` that surfaces model output.
- Any UI that consumes `/assistant`, `/rl/**`, `/rl_benchmark/**`, `/rl_finrlx/**`, `/model-validation`, or `/model-promotion` endpoints.

## Hard rules (these are not negotiable)

The assistant — and any AI/RL surface — must **never**:

- Tell the user to buy, sell, trade, or execute.
- Imply broker execution or live trading.
- Present a backtest as future performance.
- Present an RL or imported research candidate as a production recommendation without explicit governance approval (publication queue gate).
- Hide missing source context. "I don't know" with sources cited beats a confident guess.
- Render as a blank text box as the *only* affordance.

## Required scaffolding on every AI surface

1. **Guided prompts.** At least three contextual prompts surfaced by default. Examples for Home: "What's the evidence behind today's top overweight?", "Why is the regime score caution today?", "Which sources are stale?".
2. **Source chips** under every answer: dataset name + freshness chip. Reuse `DataFreshnessBadge`.
3. **Retrieval status.** Show whether retrieval ran, succeeded, or fell back to model-only. Three-state pill: `retrieved | partial | model-only`. `model-only` carries a caution tone and a one-sentence warning.
4. **Limitations footer.** Every answer carries a one-line limitations strip ("This is research output, not advice"). Driven by `fintech-disclaimer-and-marketing-guard`.
5. **Open evidence action.** Every answer offers "Open evidence" that navigates to the supporting recommendation / replay / news item / backtest.
6. **Distinct from global search.** TopBar search is for navigation; the AI surface lives elsewhere (right pane / dedicated page / home panel).

## Shadow / research-only state

Anything from RL, FinRL-X, imported research artifacts, or any candidate not approved through the publication queue must render with:

- A `accent-2` ribbon labelled "Research-only — not published".
- A disabled-by-default "Promote" affordance behind a governance permission check.
- A link to the governance audit trail that explains the gate.

This rule is co-owned with `recommendation-object-provenance` and `backtest-hygiene-gate`.

## Copy rules

- The assistant refers to itself as "FINRLX research assistant" — never "agent", never "advisor".
- Use "evidence" / "research" / "rationale" — never "advice" / "tip" / "pick".
- Use "review" / "consider" / "may be relevant" — never "you should" / "we recommend you" / "do X".
- Use "Promote to paper" / "Save as thesis" / "Defer" for action verbs — never "Trade" / "Buy" / "Sell".

## Anti-patterns

- AI sparkle icon next to an empty input.
- Streaming chat reply with no source chip.
- "Confidence: 92%" as the only signal under an answer.
- A "Generate trade idea" CTA.
- Hiding the operator console's "this is operator-only, manually captured LLM context" framing.

## Inputs to read before changing AI surfaces

- `DOCS/FINRLX_UX_UI_REDESIGN_PLAYBOOK.md` (Phase 1).
- `backend/app/api/v1/assistant.py` (request/response contract).
- The `recommendation-object-provenance`, `backtest-hygiene-gate`, and `replay-determinism-harness` skill bodies.
