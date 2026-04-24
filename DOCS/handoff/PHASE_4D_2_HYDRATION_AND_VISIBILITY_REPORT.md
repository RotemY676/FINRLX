# Phase 4D.2: Hydration Fix & Pipeline Visibility — Report

**Date:** 2026-04-24
**Phase:** 4D.2 — Hydration mismatch fix + Overview pipeline draft visibility
**Status:** Complete

---

## 1. Root Causes Found

### Hydration Mismatch (React errors #418, #423, #425)

| Root Cause | Location | Error |
|---|---|---|
| `localStorage` in `useState` initializer | `TopBar.tsx` line 34-38 | #425: server renders "default", client reads localStorage and renders different value |
| `toLocaleString()` on dates | 14 call sites across 6 files | #418/#423: Node.js and browser produce different locale output for the same Date |

### Pipeline Draft Not Visible

| Issue | Location |
|---|---|
| Overview shows "No Published Recommendation" even when pipeline draft exists | `page.tsx` line 82 — only checked `rec` which was null when no published rec |
| API warnings from `/overview` not surfaced to user | `page.tsx` — `meta.warnings` was not read or displayed |

---

## 2. Files Changed

### Created (1)
```
frontend/src/lib/format.ts    — fmtDateTime, fmtDate, fmtTime (UTC, locale-independent)
DOCS/handoff/PHASE_4D_2_HYDRATION_AND_VISIBILITY_REPORT.md
```

### Modified (8)
```
frontend/src/components/shell/TopBar.tsx              — density: useEffect instead of useState initializer
frontend/src/components/recommendation/MetadataBlock.tsx — use fmtDateTime
frontend/src/components/recommendation/RecommendationCard.tsx — use fmtDateTime
frontend/src/app/page.tsx                              — API warnings banner + draft-aware fallback text
frontend/src/app/decision/page.tsx                     — replace toLocaleString
frontend/src/app/replay/page.tsx                       — replace toLocaleString/toLocaleDateString/toLocaleTimeString
frontend/src/app/paper/page.tsx                        — replace toLocaleString/toLocaleDateString
frontend/src/app/backtests/page.tsx                    — replace toLocaleDateString
```

---

## 3. Hydration Fixes

### Density selector (TopBar)
- **Before:** `useState(() => { if (typeof window !== "undefined") localStorage.getItem(...) })` — runs during SSR, produces different value than server render
- **After:** `useState("default")` + `useEffect(() => { ... localStorage ... })` — server and client both render "default" initially, then client updates after mount

### Date formatting (all pages)
- **Before:** `new Date(d).toLocaleString()` — 14 call sites producing locale-dependent output
- **After:** `fmtDateTime(d)` / `fmtDate(d)` / `fmtTime(d)` — UTC-based fixed format `"2026-04-24 14:30"`, identical on server and client
- **Zero remaining `toLocaleString` calls** in the codebase (verified by grep)

---

## 4. Overview Pipeline Visibility

### API warnings banner
- Overview now reads `meta.warnings` from the `/overview` response
- Displays a caution-colored banner at the top with each warning
- When backend returns `"A newer pipeline-generated draft exists but is not published yet."` — this is now visible to the user

### Draft recommendation display
- When no published recommendation exists but a pipeline draft does, the backend returns the draft via `/overview` with a warning
- The Overview page now shows the draft recommendation card (not "No Published Recommendation")
- The fallback text changed from "Run the seed script" to "Run the pipeline to generate one, then publish"

---

## 5. Build Output

```
$ cd frontend && npx next build

✓ Compiled successfully
✓ Generating static pages (10/10)

Route (app)          Size      First Load JS
/                    4.61 kB   94.7 kB
/admin               5.2 kB    95.3 kB
/backtests           2.19 kB   197 kB
/comparison          10 kB     197 kB
/decision            13 kB     207 kB
/paper               2.4 kB    192 kB
/replay              3.5 kB    96.3 kB
```

### Backend tests: 113/113 PASS (unchanged)

---

## 6. Remaining Risks

1. **No E2E test for hydration** — React hydration errors are runtime-only and not caught by `next build`. A browser-based test would be needed for full verification.
2. **UTC dates may confuse users** — all dates now show UTC time. A future improvement could detect timezone client-side after mount.
3. **Draft banner depends on backend state** — if the backend's `/overview` doesn't return warnings (e.g., no pipeline has been run), no banner appears.

---

## 7. Production Pipeline Draft Visibility

After this fix, **production will now show pipeline draft data** if:
1. The backend has been seeded with `python -m seed` (which runs the pipeline and creates a draft recommendation)
2. The old seeded "published" recommendation's status was changed by action buttons (save-thesis → staged, etc.)

If the old seeded "published" recommendation still exists, it takes priority in `/overview` and `/recommendations/current`, but a caution banner warns that a newer pipeline draft exists.

---

## 8. Manual Verification Checklist

- [ ] Deploy backend with latest seed
- [ ] Open Overview page in browser
- [ ] Verify no React hydration errors in browser console
- [ ] Verify dates display in fixed format (2026-04-24 14:30)
- [ ] If pipeline draft exists: verify caution banner appears
- [ ] Toggle dark/light theme: no hydration flash
- [ ] Cycle density selector: no hydration flash
