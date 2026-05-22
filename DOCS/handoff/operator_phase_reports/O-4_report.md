# Phase O-4 Report — Analyst Notes panel on Replay

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Close the round-trip: when the operator pastes a ChatGPT or Claude response back into `/operator` with a recommendation_id, surface it on `/replay` for that recommendation as an "Analyst notes" panel — so the LLM analysis lives in the audit trail context, not in a separate "Operator console" silo.

## What was added

- `frontend/src/components/operator/AnalystNotesPanel.tsx` — `<AnalystNotesPanel recommendationId={...} />`. Calls `listOperatorAnalyses({ recommendation_id })` and renders the results as expandable cards with:
  - Source pill (`GPT` / `CLAUDE` / `OTHER`).
  - Surface tag (`decision` / `replay` / `news` / `manual`).
  - Timestamp.
  - The operator's note (italic, if present).
  - The prompt used (`<details>` accordion, if present).
  - The pasted response (renders as preformatted text with sans-serif font for readability).
  - Delete button (admin-only via the auth-required endpoint).
- An **Add note →** link top-right that deep-links to `/operator?rec={id}&surface=replay` for fast paste-back from a forensic-review session.
- Renders **nothing** when the `operator_console` flag is off, OR when no notes are archived for this recommendation, OR when fetch hits an auth error. This keeps the surface invisible for non-operator deployments and on Replay pages that have no analyst notes yet.

## Wired into the Replay page

`frontend/src/app/replay/page.tsx` — `<AnalystNotesPanel recommendationId={detail.recommendation_id} />` rendered immediately below the Pipeline Stage Snapshots, so the post-trade review flow reads: Replay header → Confidence → Warnings → Positions → Pipeline stages → **Analyst notes** → (end).

## Round-trip verified

1. Operator on `/decision` clicks **Copy LLM context** (Phase O-0). Bundle copied.
2. Operator pastes into ChatGPT (Phase O-1) or Claude (Phase O-2) Project. Asks a question. Gets answer.
3. Operator clicks **Paste response →** on the same Decision page. Lands on `/operator?rec={id}&surface=decision` with the recommendation ID pre-filled.
4. Operator pastes the response, adds an optional one-line note, clicks **Archive analysis**. POST hits `/api/v1/operator/analyses` (Phase O-0).
5. Operator later opens `/replay`, picks the same recommendation. The Analyst notes panel renders the archived response at the bottom of the page — visible to anyone with operator access reviewing this recommendation later.

The LLM analysis is now part of the recommendation's reviewable history — not stuck in a chat log somewhere.

## Verification

| Check | Result |
|---|---|
| `npm run typecheck` | ✅ clean |
| `npm run lint` | ✅ clean (zero warnings) |
| `npm run build` | ✅ 76 static pages, no regression |
| `npm run test:ci` | ✅ 41/41 pass |
| Manual round-trip flow | ✅ verified locally (next-build paths intact) |

## What this is NOT

- Not a full audit-trail row. The notes are scoped to the operator who created them — they don't show up in `/api/v1/ops/audit-trail` (intentional: these are personal analyst notes, not system events).
- Not viewable by other users. Listing is filtered by `user_id` on the backend (Phase O-0 implementation).
- Not exported. If the operator wants to ship an analyst note as evidence (e.g., to a teammate), copy-paste remains the workflow. A future "Export to PDF" link could be added if needed.

## Next step

Commit, push. Project closes here — see `PROJECT_SUMMARY.md` for the full strategy retrospective.
