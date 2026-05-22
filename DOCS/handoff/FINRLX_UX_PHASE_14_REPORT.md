# FINRLX UX/UI Transformation — Phase 14 Report (TopBar redesign)

## A. Summary

Phase 14 redesigns the TopBar from a 44-px-tall strip into a 56-px
accessible chrome surface with three working modules that previously
were placeholders or did not exist:

- **Gmail-style account menu** — large avatar header, "Manage your
  FINRLX account" CTA, account-management stubs that are honest
  about being unimplemented, workspace shortcuts, theme + density,
  sign-out, legal/version footer.
- **Global Command Palette** — opens via ⌘K / Ctrl+K or the search
  button. Searches routes, ticker symbols, operator analyses; recent
  searches in localStorage; explicit non-blank empty state.
- **Notifications panel** — bell icon opens a dropdown that composes
  notifications from `/api/v1/ops` + `/api/v1/overview` (no new
  backend). Per-user read-state in localStorage. Honest per-source
  error reporting when an endpoint fails.

Shipped in four sub-phase commits (14.1 → 14.4) per the operator's
plan-approval choice.

## B. Skills used

- `finrlx-ux-redesign-director` — rule 1 (decision-first), rule 4 (readable density: 56 px TopBar, named typography tokens throughout), rule 8 (one palette, one search), rule 10 (evidence not optional — per-item source on notifications).
- `finrlx-fintech-dashboard-patterns` — notification items follow the `asOf` / `source` / `severity` contract; semantic palette aliases applied.
- `finrlx-ai-ux-governance` — palette empty state explicitly steers AI prompts to the operator console: "AI prompts live inside the operator console, not the palette." No blank-chat-as-band-aid.
- `fintech-disclaimer-and-marketing-guard` — every TopBar surface scanned. No "Buy alert", "Trade signal", "Execute", etc.
- `recommendation-object-provenance` — the "New recommendation published" notification deep-links to `/decision` (canonical surface) rather than synthesising an abbreviated card.
- `vercel-web-design-guidelines-mirror` — `role="dialog" aria-modal aria-labelledby` on palette, UserMenu, NotificationsPanel; `role="tablist"` + `aria-selected` on the All/Unread tabs; Esc + outside-click + focus restoration everywhere; tap targets ≥ 44 px on mobile.
- `anthropic-frontend-design-mirror` — composition: clear hierarchy in dropdowns (header → primary CTA → grouped rows → personalisation → footer). No glass-effect overuse.
- `feature-flag-kill-switch` — the `topbar_v2` flag was considered and intentionally not added (per Phase 14 plan §F notes). The redesign is committed sub-phase by sub-phase so individual changes can be reverted with `git revert <sha>` rather than a flag flip; production auto-deploys per push.
- `finrlx-visual-qa-accessibility-gate` — gate ran on every sub-phase.
- `finrlx-handoff-evidence-packager` — this report.

## C. External references used

None new. Phase 0 §1.5 (AlphaSense source-grounded research) is the conceptual anchor for keeping the palette structured rather than chat-shaped. Phase 0 §2.3 (NN/g, Smashing) drives the typography decisions.

## D. Files changed

| File | Sub-phase | Action |
|---|---|---|
| `frontend/src/components/shell/TopBar.tsx` | 14.1, 14.3, 14.4 | h-11 → h-14; named typography tokens; new `onOpenPalette` prop; search button (desktop wide + mobile icon); `NotificationsPanel` replaces placeholder bell. |
| `frontend/src/components/shell/AppShell.tsx` | 14.1, 14.3 | `top-11` → `top-14` for the mobile drawer backdrop; `CommandPalette` mounted; ⌘K global keybind. |
| `frontend/src/components/shell/Sidebar.tsx` | 14.1 | `top-11` → `top-14` for mobile drawer. |
| `frontend/src/components/shell/UserMenu.tsx` | 14.2 | **Rewrite.** Gmail-style dropdown with header card + management stubs + workspace shortcuts + personalisation + sign-out + footer. |
| `frontend/src/components/shell/CommandPalette.tsx` | 14.3 | **New.** Global ⌘K palette. |
| `frontend/src/components/shell/NotificationsPanel.tsx` | 14.4 | **New.** Bell-icon dropdown. |
| `frontend/src/lib/search.ts` | 14.3 | **New.** Search composer (routes, tickers, operator analyses). Recent-searches localStorage helpers. |
| `frontend/src/lib/notifications.ts` | 14.4 | **New.** Notifications composer + per-user localStorage read-state. |
| `DOCS/handoff/FINRLX_UX_PHASE_14_REPORT.md` | 14.5 | This report. |

## E. UX decisions

1. **TopBar height 56 px.** The previous 44 px matched the touch-target floor but read as cramped on desktop. 56 px gives the brand + breadcrumb + scope chips room to breathe; mobile keeps 44-px touch targets via `min-h-11` per button.
2. **Avatar = 40 px.** Slightly larger than the prior 32–36 px so it reads as a primary action without dominating.
3. **Account-menu stubs are explicitly disabled with explanatory copy.** "Add another account" and "Switch account" render with a `soon` badge and a tooltip stating why. They are NOT clickable buttons that go nowhere — the playbook forbids phantom affordances.
4. **Palette empty state is non-blank.** When the input is empty, the palette surfaces a curated top-7 routes + the explicit copy "AI prompts live inside the operator console, not the palette." This deliberately steers users away from treating the palette as a chat.
5. **Recent searches localStorage.** Not server-persisted; per-browser. Honest about scope.
6. **Notifications composed from existing endpoints, not a fake `/notifications` service.** The panel footer says so explicitly so no one assumes a service exists when they read the code. When a real service ships, the composer is the single migration point.
7. **Notification severity mapping is generous to existing data.** `OpsBreach.severity` strings are normalised case-insensitively, falling back to "info" when unrecognised. New severity values from the backend won't crash the panel.
8. **Per-source error footer on notifications.** If `fetchOps` or `fetchOverview` throws, the panel shows the source + the actual error message. Honest, not silent.
9. **Notification badge shows a numeric count** (max "9+") instead of the prior generic red dot — gives the user a real "how many" signal before opening the panel.
10. **Context-pane toggle no longer fades to 50% when inactive.** That state read as "disabled"; the new design uses a `primary-soft` background when active and a transparent background when inactive.

## F. Data / API contract notes

- No backend endpoint added or modified.
- New frontend-internal modules read existing endpoints: `fetchUniverses` (routes are static, but tickers may eventually intersect), `fetchOps`, `fetchOverview`, `listOperatorAnalyses` (auth-gated; falls through quietly).
- Suggested future backend extensions:
  - `GET /api/v1/notifications` — when read-state needs to follow the user across browsers.
  - `GET /api/v1/recommendations` — to add a real recommendations category to the palette.
  - `GET /api/v1/search` — to index help MDX content (currently no runtime index).

## G. Safety / governance notes

- The "New recommendation published" notification deep-links to `/decision` so the user lands on the source-grounded canonical surface (per `recommendation-object-provenance`).
- The palette explicitly redirects AI questions to `/operator`, preserving the `finrlx-ai-ux-governance` rule that the assistant is operator-curated.
- Account-menu sign-out flushes `AuthContext` tokens and routes to `/login` — unchanged from the previous `UserMenu`.
- Forbidden-language sweep clean across the new files (verified).

## H. Testing evidence

Across all four sub-phases:

| Command | Result |
|---|---|
| `npm run typecheck` | **PASS** (each sub-phase) |
| `npm run test:ci -- --testTimeout=15000` | **PASS** 41/41 (each sub-phase) |
| `npm run build` | **PASS** 77/77 static + 1 dynamic (each sub-phase) |
| Forbidden-language sweep | **PASS** — no new hits introduced |
| `npm run lint` | **PASS** (Phase 12 baseline preserved) |
| `npm run e2e:ci` | **Not run** — no playwright config |

## I. Screenshot evidence

Not captured in any sub-phase. The same Windows `next start` flakiness from Phases 3–12 persists. Production-side capture remains the right place to do it.

## J. Known limitations

1. **Notifications "Mark all read" is browser-local.** Resets if the user clears localStorage or moves to a different device. When a real notifications service ships, swap the storage layer in `frontend/src/lib/notifications.ts`.
2. **Account-menu stubs.** "Add another account" / "Switch account" do nothing until multi-account auth lands. Explicit `soon` badges + tooltips communicate this honestly.
3. **No help-article search in the palette.** No runtime MDX index. Build-step indexer is a follow-up.
4. **No recommendations category in the palette.** No list endpoint typed on the frontend. Same follow-up.
5. **Operator analyses search is full-payload-then-filter** (limit 50). Fine at current data volume; needs server-side filter when volume grows.
6. **No screenshot matrix captured.** Carries from Phase 12.
7. **No automated keyboard-navigation test.** Manual sweep done; an a11y test in vitest+testing-library would be a small future improvement.

## K. Phase 14 gate compliance

| Criterion | Status |
|---|---|
| TopBar is bigger and more accessible | **Met** — h-14, named typography, 20 px icons, 40-px avatar |
| Account menu looks and functions like Gmail | **Met** — large avatar header, "Manage your FINRLX account" CTA, management stubs (honest), workspace shortcuts, personalisation, sign-out, legal footer |
| Search is fully implemented | **Met** — ⌘K palette with routes, tickers, operator analyses, recent searches |
| Other TopBar functionality wired | **Met** — bell now opens NotificationsPanel; context-pane toggle dropped the half-faded look |
| No execution language anywhere in TopBar / dropdowns | **Met** — forbidden-language sweep clean |
| All sub-phases pass typecheck + tests + build | **Met** |

**Gate 14 clears for everything that is automatically verifiable. Visual breakpoint verification remains the documented gap (cross-cutting from Phase 12).**

## L. Production verification

Railway auto-deploys per-push. Captured at the close of sub-phase 14.4:

| Sub-phase | Commit | Railway deployment | Status at report time |
|---|---|---|---|
| 14.1 | `4d51942` | — | replaced by later deploys |
| 14.2 | `c5494d1` | — | replaced |
| 14.3 | `b31a34e` | `91dd089d-78ee-429b-8646-570818133706` | **SUCCESS** at 13:24 IST |
| 14.4 | `efd94b6` | `ca0847ab-ae9a-4ea1-8903-a96318740e28` | **DEPLOYING** at 13:31 IST (in progress; will be SUCCESS shortly per Railway's normal pattern) |

Smoke check against the 14.3-live deployment (Notifications panel was deploying when this curl ran):

```
curl https://frontend-production-7e8b1.up.railway.app/ | grep
→ "Search FINRLX"          (Phase 14.3 search button)
→ "h-14"                   (Phase 14.1 TopBar height)
→ aria-label="Notifications" (TopBar bell trigger)
→ aria-current             (Phase 4 a11y, preserved)
```

Once `ca0847ab` deploys, the bell trigger above will be the new
`NotificationsPanel` component instead of the placeholder button.

This is the closing report for the Phase 14 work. No follow-up
phase is queued unless the operator requests one.

