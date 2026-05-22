---
name: vercel-web-design-guidelines-mirror
description: Repo-local mirror of the Vercel web-design-guidelines skill plus its frozen runtime rule set. Activates when auditing a FINRLX UI file for accessibility, forms, focus states, typography, motion, performance, navigation, touch, dark mode, i18n, or hydration safety. Frozen on 2026-05-22 — re-fetch source at Phase 3 and Phase 12 gates.
type: project
---

# Vercel Web Design Guidelines — repo-local mirror

This is a **frozen mirror** of the Vercel
[`web-design-guidelines`](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md)
skill. The upstream skill fetches its rules at runtime from
`vercel-labs/web-interface-guidelines/main/command.md`, which the FINRLX
redesign program treats as a security and reproducibility hazard. We freeze
the rule set here so reviews use the same rules from one phase to the next.

Captured: 2026-05-22, Phase 1.
Re-fetch: Phase 3 gate, Phase 12 gate.

## When to invoke

- During Phase 3 (design system foundation) review of a UI primitive.
- During Phase 12 (full-system QA) review of every redesigned page.
- On any standalone "audit this component" request.

Use **after** `finrlx-fintech-dashboard-patterns` and
`finrlx-visual-qa-accessibility-gate`. Those skills define the FINRLX
contract. This mirror provides the broader web-interface lens.

## Review process

1. Identify the file(s) under review.
2. Walk every rule category below.
3. Emit findings in the form `path:line — issue` (terse, file-first).
4. Mark a clean file as `✓ pass`.
5. Group findings by file.

## Rule categories (frozen, 2026-05-22)

### Accessibility
- Use semantic HTML for buttons, links, headings, lists, navigation.
- Icon-only buttons MUST carry `aria-label`.
- Modal / drawer focus is trapped while open and restored on close.
- Live regions (`role="status"` / `aria-live`) for async feedback.
- Color is never the only signal for state.

### Focus states
- Every interactive element shows a visible focus ring (`:focus-visible`).
- The ring must not be hidden by `outline: none` without a replacement.

### Forms
- Every input has a label (`for`/`id` or `aria-label`).
- Sensible `autocomplete` attributes on real-world fields (email, password, address).
- Inline error text appears with `aria-describedby`.
- Submit buttons disable while in-flight and show progress.

### Animation & motion
- Respect `prefers-reduced-motion`.
- Long-running progress (>300ms) shows a visible indicator.
- Avoid layout-thrash transitions (`top`/`left`); prefer `transform`/`opacity`.

### Typography
- Use proper Unicode for quotes ("/") and ellipsis (…), not three dots.
- Tabular figures for numeric columns.
- Line-height ≥ 1.4 for body copy.

### Content handling
- Truncate with `text-overflow: ellipsis` AND `title=…` for full string on hover.
- Empty states always state what to do next.
- "0" is rendered explicitly, not as a blank cell.

### Images
- `width` and `height` attributes on every `<img>` to reserve space.
- Lazy-load below-the-fold images.
- `alt` text describes content, not decoration.

### Performance
- Virtualize long lists (> 100 rows) where possible.
- Subset fonts; preload the primary face.
- Avoid layout shift after initial paint.

### Navigation
- Selected nav item carries `aria-current="page"`.
- Active state matches the URL.
- Breadcrumbs reflect actual hierarchy.

### Touch
- Tap targets ≥ 44 px on touch viewports.
- No tap-zoom on input focus (font-size ≥ 16 px on mobile inputs).

### Dark mode
- Tokens drive both themes; no hardcoded color literals in components.
- Contrast ≥ 4.5:1 for body text in both themes.

### i18n
- Use `Intl.NumberFormat` / `Intl.DateTimeFormat` for locale-aware output.
- Currency, dates, and numbers respect locale.

### Hydration safety
- `suppressHydrationWarning` only on elements whose mismatch is intentional (theme attribute, locale-dependent timestamps).
- Avoid `useState(localStorage.getItem(…))` in initial render without an explicit gate.

### Anti-patterns to flag
- `div onClick={…}` instead of a `<button>`.
- Color as the only signal for status.
- Missing `aria-label` on icon-only controls.
- Modal without focus trap.
- Tap targets < 44 px on touch viewports.
- Body text < 14 px on default density.

## Output format

```
## path/to/file.tsx

path/to/file.tsx:42 — icon button missing aria-label
path/to/file.tsx:58 — animation missing prefers-reduced-motion

## path/to/other.tsx

✓ pass
```

## Source URLs (re-fetch on Phase 3 / Phase 12 gates)

- Skill wrapper: `https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/web-design-guidelines/SKILL.md`
- Runtime rules: `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`

## License note

The upstream skill is published under whatever terms the
`vercel-labs/agent-skills` repository sets. We mirror functional review
guidance (facts about what a usable, accessible web interface looks like)
rather than copyrighted text. If a future re-fetch surfaces verbatim
material we want to preserve, we will add an explicit attribution block.
