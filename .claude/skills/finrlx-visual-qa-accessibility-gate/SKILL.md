---
name: finrlx-visual-qa-accessibility-gate
description: End-of-phase quality gate for every FINRLX UX/UI phase. Runs typecheck, tests, build, e2e (when available), captures the screenshot matrix (390 / 768 / 1024 / 1440 in both themes), and runs accessibility / forbidden-language sweeps. Activates at the close of every phase from Phase 3 onward, and on demand for any meaningful UI change. Records failures verbatim; never marks a gate "passed" with a failing command.
type: project
---

# FINRLX — Visual QA & Accessibility Gate

This is the gate that protects production from sloppy phase completions.

## When to invoke

- At the close of every phase from Phase 3 onward.
- After any meaningful UI change that touches `frontend/src/components/**` or `frontend/src/app/**`.
- Before pushing to `origin/main` if the change is larger than a one-line fix.

## Required commands

Run in this order. Stop at the first failure and report it.

### 1. Frontend static checks

```bash
cd frontend && npm run typecheck
cd frontend && npm run lint --if-present
cd frontend && npm run test:ci
cd frontend && npm run build
```

### 2. Frontend e2e (only if `frontend/playwright.config.*` exists)

```bash
cd frontend && npm run e2e:ci
```

If Playwright is configured but the browser launch fails on the host machine, record the exact stderr and continue to step 3 — do not mark the gate "failed" for a tooling issue, but also do not mark it "passed".

### 3. Backend (only if any `backend/**/*.py` changed)

```bash
cd backend && python -m pytest -q
```

### 4. Forbidden-language sweep

```bash
rg -n "\b(buy now|sell now|trade now|execute trade|connect broker|guaranteed return|risk-free|beat the market|sure profit)\b" frontend DOCS backend
```

Zero hits required. If the only hits are the forbidden-list itself in skill files, mention that in the report.

### 5. Screenshot matrix

Take screenshots of every page that changed in the phase, at these viewports and themes:

| Viewport | Theme | Filename pattern |
|---|---|---|
| 390 × 844 (mobile) | light | `phase{N}_{route}_390_light.png` |
| 390 × 844 (mobile) | dark | `phase{N}_{route}_390_dark.png` |
| 768 × 1024 (tablet) | light | `phase{N}_{route}_768_light.png` |
| 1024 × 768 (sm desktop) | light | `phase{N}_{route}_1024_light.png` |
| 1440 × 900 (desktop) | light | `phase{N}_{route}_1440_light.png` |
| 1440 × 900 (desktop) | dark | `phase{N}_{route}_1440_dark.png` |

Save under `DOCS/handoff/screenshots/phase{N}/`. Use Playwright when available:

```js
// scripts/screenshot-matrix.mjs (created on demand)
import { chromium } from 'playwright';
// for each route, viewport, theme: page.goto, page.screenshot
```

If a route is gated by a feature flag, set the env var before the screenshot run.

### 6. Accessibility sweep

If `frontend/node_modules/@axe-core/playwright` exists, run axe on each route at 1440 px in both themes. Otherwise record the gap honestly: "no automated a11y check; manual contrast spot-check performed". Manual checklist:

- Body text contrast ≥ 4.5:1 against its background.
- Caption / metadata text contrast ≥ 4.5:1.
- Focus ring visible on every interactive control.
- No keyboard trap (Tab from TopBar to footer without getting stuck).

### 7. Vercel web-design-guidelines mirror

If touched files match the mirror skill's scope, run a manual review against `.claude/skills/vercel-web-design-guidelines-mirror/SKILL.md` rules.

## Gate criteria (the report must state each pass/fail honestly)

The phase passes the gate when:

- All commands above either pass or have a recorded, justified exception.
- Zero forbidden-language hits.
- Screenshot matrix captured (or the tooling failure recorded verbatim).
- No new TypeScript errors.
- No new failing tests.
- No regression in axe violations vs the previous phase's snapshot (when an axe run is available).

## Anti-patterns

- Marking a gate "passed" with TypeScript errors. Don't.
- Stating "tests pass" without quoting the actual command output. Don't.
- Skipping the screenshot matrix because it's slow. Don't — record the tool failure if it fails, but always attempt.
- Quietly excluding a route from screenshots because it has a feature-flag-off state. Document the flag state in the report.

## Output

The gate report must be appended to the phase report at section H "Testing Evidence" and section I "Screenshot Evidence", and must include the verbatim command output (truncated to the first/last 40 lines if very long).
