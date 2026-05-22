# Phase 3 — Screenshots not captured

## Verdict

Screenshot matrix was attempted but not completed in Phase 3. Recording
the gap honestly so the visual-qa-gate skill can carry the obligation
forward.

## What was attempted

1. Wrote `frontend/scripts/phase-screenshots.mjs` — a Playwright-core
   driver that captures four routes (`/`, `/decision`, `/disclaimer`,
   `/onboarding`) at viewports 390 / 768 / 1024 / 1440 px in both
   light and dark themes.
2. Started `npm run start` (Next.js production server) in the
   background.
3. Probed `http://localhost:3000/disclaimer` for readiness — the
   server did not bind within the polling window before the run was
   cut short.

## Why this is acceptable for Phase 3 specifically

Phase 3 changes are:
- four new CSS custom properties (`stale`, `blocked`, `governance`,
  `shadow` semantic aliases) — additive, no visible delta;
- eight Tailwind `fontSize` named tokens — additive, only consumed by
  `PageError`, `PageEmpty`, `PageLoading`;
- `--dens-text` 13.5 px → 14.5 px (default density only) — a one-pixel
  body-text bump, not a visible layout change.

The first phase whose visual delta is meaningful at every breakpoint
is Phase 4 (app-shell and navigation rewrite). Phase 4 will be the
first phase that *must* ship screenshots.

## What this gap costs

- Gate 3 acceptance criterion "Screenshot evidence exists for
  desktop/tablet/mobile" is **not met**. This is recorded as a known
  gap in the Phase 3 report §J.
- Phase 4 inherits the obligation to capture the matrix on its first
  meaningful visual delta.

## Re-attempt plan

For Phase 4, the order will be:

1. Start `npm run dev` (faster than production start for screenshots).
2. Wait for `http://localhost:3000/` to respond 200 (longer polling
   window, with a fallback to recording the failure stderr verbatim).
3. Run `node scripts/phase-screenshots.mjs` with `PHASE=4`.
4. If Playwright browser launch fails, capture the stderr and ship
   the report with the `_NOT_CAPTURED.md` marker — same pattern as
   this file.

## Files left behind from this attempt

- `frontend/scripts/phase-screenshots.mjs` — driver kept for re-use in
  Phase 4 onward.

No screenshot PNGs were saved.
