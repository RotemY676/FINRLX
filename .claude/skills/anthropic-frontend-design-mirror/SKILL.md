---
name: anthropic-frontend-design-mirror
description: Repo-local mirror of the Anthropic frontend-design skill principles. Activates when designing FINRLX components, pages, or visual surfaces where additional taste/aesthetic guidance is wanted. Use alongside finrlx-ux-redesign-director, which takes precedence on any conflict. Frozen snapshot — re-fetch source on Phase 3 / Phase 12 gates.
type: project
---

# Anthropic Frontend Design — repo-local mirror

This is a **frozen mirror** of the Anthropic `frontend-design` skill, captured
on 2026-05-22 in Phase 1 of the FINRLX UX redesign program. The original
skill ships under [`anthropics/skills/skills/frontend-design/SKILL.md`](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md).
We mirror it rather than `npx skills add` to keep it version-pinned and
auditable.

## Why a mirror

The remote skill is high-quality guidance, but the FINRLX redesign program
requires that what governs our code today does not silently change tomorrow.
A mirror version-pins the principles. Re-fetch and diff at the start of
Phase 3 and at the close of Phase 12 (`finrlx-visual-qa-accessibility-gate`
explicitly calls this step out).

## When to invoke

- When picking typography, palette, motion, or composition for a FINRLX surface.
- Whenever the temptation to "ship a clean default" is strong — that is exactly the AI-generic look this skill is built to push against.
- Always in addition to `finrlx-ux-redesign-director`, which carries final authority on FINRLX-specific constraints (governance, disclaimers, six-area IA, density). If the two skills conflict, the FINRLX director wins.

## Principles (captured 2026-05-22)

1. **Commit to a direction.** Pick a clear aesthetic — institutional fintech in FINRLX's case — and execute with discipline. Do not default to "clean SaaS".
2. **Typography matters more than you think.** Choose fonts deliberately. FINRLX uses `Inter Tight` (body), `Fraunces` (display), `JetBrains Mono` (numeric). Do not collapse to a single system font.
3. **Color cohesion over color noise.** Pick a dominant palette with a small number of sharp accents. FINRLX's OKLCH palette already encodes this — extend, don't add new hues without a semantic reason.
4. **Motion with intent.** CSS animations should serve perception (loading, state change, focus). Avoid scattered hover micro-interactions that distract.
5. **Asymmetry and weight.** Unexpected composition reads as designed; perfectly centered everything reads as generated. Vary the visual weight inside cards and KPI strips.
6. **Custom details.** Subtle texture, accents, considered borders. FINRLX already has a `glass` utility — use it sparingly, do not make every card a glass card.
7. **Match code complexity to ambition.** Don't ship maximalist motion on a minimalist surface — and vice versa.

## What this skill is NOT

- Not a replacement for `finrlx-ux-redesign-director`.
- Not a permission to break the typography / density / forbidden-language rules in the FINRLX skills.
- Not a brief for marketing maximalism — FINRLX is institutional fintech, not a brand site.

## License note

The upstream skill ships with its own `LICENSE.txt`. We mirror principles
(facts about what good frontend design looks like) rather than verbatim
text, so this file is original FINRLX-team work informed by the upstream
skill. If we ever copy upstream text verbatim, we will add an explicit
attribution block.

## Source URL (re-fetch on Phase 3 / Phase 12 gates)

`https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md`
