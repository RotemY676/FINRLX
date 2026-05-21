# Phase H-0 Report — Help Center Scaffold

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Scaffold the in-app Help center under `/help`, wire MDX rendering, expose the global Help button in the TopBar, and ship a deployable empty shell that builds, typechecks, lints, and passes existing tests.

No content yet — the IA skeleton lands in H-1.

## What was added

### Dependencies
- `next-mdx-remote@^5` — server-component MDX rendering (App Router compatible).
- `gray-matter@^4` — frontmatter parser.
- `remark-gfm@^4` — GitHub-flavored markdown extensions (tables, strikethrough, task lists).
- `rehype-slug@^6` — auto IDs on headings.
- `rehype-autolink-headings@^7` — clickable heading anchors.

### Files created

| Path | Purpose |
|---|---|
| `frontend/src/lib/help/types.ts` | Shared TS types: `HelpPage`, `HelpFrontmatter`, `DiataxisKind`, `HelpArea`. |
| `frontend/src/lib/help/toc.ts` | `AREA_META` and `AREAS_IN_ORDER` — the visible IA. |
| `frontend/src/lib/help/content.ts` | Server-only filesystem walker; reads `src/content/help/**/*.md(x)` and parses frontmatter via `gray-matter`. |
| `frontend/src/components/help/Annotated.tsx` | Annotated-screenshot component (SVG numbered callouts + `<ol>` legend in `<figcaption>`, ARIA15-compliant). |
| `frontend/src/components/help/Callout.tsx` | Note / Tip / Warning / Important boxes using existing design tokens. |
| `frontend/src/components/help/Term.tsx` | Inline glossary anchor (dotted underline → `/help/glossary#id`). |
| `frontend/src/components/help/HelpLink.tsx` | The contextual `?` glyph used **outside** `/help` (icon or inline variant). |
| `frontend/src/components/help/DiataxisBadge.tsx` | Renders the frontmatter `diataxis` field as a small chip. |
| `frontend/src/components/help/Updated.tsx` | "Updated YYYY-MM-DD" pill with fresh-within-30-days highlight. |
| `frontend/src/components/help/PageHeader.tsx` | Standard page header (badge, updated, title, summary). |
| `frontend/src/components/help/HelpSidebar.tsx` | Left sidebar TOC, `aria-current="page"`, area-grouped. |
| `frontend/src/components/help/HelpShell.tsx` | Two-column layout shell. |
| `frontend/src/components/help/HelpLandingBody.tsx` | 9-area card grid + tips block (no Pagefind yet — H-6). |
| `frontend/src/components/help/mdxComponents.tsx` | Components map for `MDXRemote` — typed headings, lists, tables, plus custom components. |
| `frontend/src/app/help/layout.tsx` | Metadata + canvas wrapper. |
| `frontend/src/app/help/[[...slug]]/page.tsx` | Catch-all route; uses `generateStaticParams` to prerender every MDX file. |
| `frontend/src/content/help/index.md` | Landing-page seed (frontmatter only — body comes from `HelpLandingBody`). |
| `DOCS/handoff/help_phase_reports/H-0_report.md` | This report. |

### Files modified

| Path | Change |
|---|---|
| `frontend/src/components/icons/Icon.tsx` | Added `help-circle`, `book-open`, `lightbulb`, `compass`, `list-tree` icons. |
| `frontend/src/components/shell/TopBar.tsx` | Added the global Help button (`?` icon) right of the theme toggle on every page; added `/help` to `CRUMB_MAP` and a `pathname.startsWith("/help")` fallback so the crumb reads "Help center" on all `/help/*` pages. |
| `frontend/package.json` / `package-lock.json` | MDX dependency additions. |

## Verification

| Check | Result |
|---|---|
| `npm run typecheck` | ✅ clean |
| `npm run lint` | ✅ clean (existing prisma/sentry warnings unchanged; intentional `<img>` override silenced inline). |
| `npm run build` | ✅ `/help/[[...slug]]` listed as SSG, `/help` prerendered, total page size 6.71 kB / 114 kB First Load JS. |
| `npm run test:ci` | ✅ 41/41 pass — no regression. |

## What lands next (H-1)

Create every MDX file from the strategic plan's IA (§B) with frontmatter and an H1 only. After H-1 the sidebar will populate, the landing-page area cards will count > 0 pages, and every route in the plan will return 200 with the correct Diátaxis badge.

## Open items / risks

- No risks blocking H-1. The prisma/sentry "Critical dependency" warnings are pre-existing and unrelated to this phase.
- Build does include a `<img>` ESLint rule disable for the MDX `img` override — intentional and documented inline.
- No screenshots yet — H-4.
- No search yet — H-6.

## Exit checklist

- [x] Route `/help` returns 200 in build output.
- [x] `MDXRemote` wired with remark-gfm + rehype-slug + rehype-autolink-headings.
- [x] Global Help button visible in TopBar on every page.
- [x] Design tokens used exclusively — no hard-coded hex anywhere in `components/help/`.
- [x] All custom components export from `mdxComponents.tsx` so MDX files can use `<Callout>`, `<Annotated>`, `<Term>`, `<HelpLink>`, `<DiataxisBadge>`.
- [x] Typecheck + lint + build + tests green.
- [x] Phase report committed.

## Next step

Commit, push, verify on Railway deploy, then proceed to H-1.
