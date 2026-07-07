# Council verdicts — S7a visual fix (operator report: "looks very bad")
Date: 2026-07-06 · Root cause honestly stated: the S7a flip mounted Simple
Mode INSIDE the full Pro chrome (Sidebar + AppBar search + ContextStrip),
producing two competing inputs, a bare injected "Pro" text link beside the
logo, and nested <main> elements — violating SIMPLE_MODE_SPEC J0/S7.4, which
this program itself wrote. The implementation was merged without any visual
verification; gates (tsc/vitest/build) cannot catch composition problems.

## Fix reviewed
- SimpleShell: minimal chrome for /, /simple, /compare only (wordmark ->
  home; Compare · Help · Pro button); AppShell branches by pathname; Pro
  routes untouched; shell owns the single <main>.
- Injected TopBar/AppBar links reverted.
- All Simple surfaces moved from arbitrary var() classes to the house
  Tailwind token classes (design-system consistency, D14); recharts stroke
  props legitimately keep CSS-var color strings.

## Verdicts
Quant Skeptic — PASS (no analytical change). UX Critic — PASS on structure:
one input on the front door, chrome minimal per spec; NOTE: this council
cannot see pixels in this environment either — visual sign-off remains with
the operator or a Playwright screenshot run. Truthfulness Auditor — PASS
(copy unchanged; this file records the miss). Security/Ops — PASS (static
links; no behavior change).

## Process lesson (binding for remaining phases)
Any phase that changes page composition must ship a rendered-DOM structural
test (single main, absence of Pro chrome on Simple routes) — added below —
and visual claims stay out of reports until a screenshot exists.
VERDICT: **PASS with operator visual sign-off pending.**
