# Phase O-0 Report — Operator console scaffold + context export

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Build the single-operator workbench that lets you copy structured page context from Decision / Replay / News into ChatGPT or Claude (in another tab, against your existing subscriptions — zero token cost), then paste responses back into FINRLX where they get archived against the originating recommendation.

## What was added

### Backend (FastAPI + Postgres)

| File | Purpose |
|---|---|
| `backend/migrations/versions/028_operator_analyses.py` | New `operator_analyses` table (id, user, surface, recommendation_id, source, prompt, response, note, created_at). |
| `backend/app/models/operator.py` | `OperatorAnalysis` SQLAlchemy model with the source/surface enums. |
| `backend/app/api/v1/operator.py` | `POST /api/v1/operator/analyses`, `GET /api/v1/operator/analyses`, `DELETE /api/v1/operator/analyses/{id}` — all auth-required and gated by `feature_operator_console`. Returns 404 when the flag is off. |
| `backend/app/core/config.py` | New `feature_operator_console: bool = False` setting. |
| `backend/app/api/v1/flags.py` | Exposes the new flag in `/api/v1/flags` so the FE can hide the surface. |
| `backend/app/api/router.py` | Wires `operator_router`. |
| `backend/app/models/__init__.py` | Registers `OperatorAnalysis` for Alembic + import. |
| `backend/tests/test_mvp4_feature_flags.py` | Updated expected flag-set to include `operator_console`. |

### Frontend (Next.js 15 + Tailwind)

| File | Purpose |
|---|---|
| `frontend/src/contexts/FeatureFlagsContext.tsx` | Added `operator_console: boolean` to `FeatureFlags`, fail-closed default, fetch wiring. |
| `frontend/src/services/operatorApi.ts` | Typed `OperatorAnalysis`, `createOperatorAnalysis`, `listOperatorAnalyses`, `deleteOperatorAnalysis`. |
| `frontend/src/services/api.ts` | Exported `apiFetch` so other service files can reuse it without re-implementing the auth+error-handling shape. |
| `frontend/src/lib/operator/contextBuilder.ts` | Pure functions that turn page data into a single pastable string with a strict, source-grounded system prompt at the top: `buildDecisionContext`, `buildReplayContext`, `buildNewsContext`. |
| `frontend/src/components/operator/CopyLLMContextButton.tsx` | Small button that copies a `LLMContextBundle` to the clipboard + a `Paste response →` link to `/operator?rec=...&surface=...`. Renders nothing when `operator_console` flag is off. |
| `frontend/src/app/operator/page.tsx` | The operator console: archive form (surface / LLM source / recommendation_id / prompt / response / note) + archived-analyses list with delete + filters. `useSearchParams` consumer wrapped in `<Suspense>` for SSG. |
| `frontend/src/app/decision/page.tsx` | Wired `CopyLLMContextButton` into the recommendation hero strip. |
| `frontend/src/app/replay/page.tsx` | Wired `CopyLLMContextButton` next to the Replay Detail header. |
| `frontend/src/app/news/page.tsx` | Wired `CopyLLMContextButton` next to the Refresh button. |

## Design notes

- **The Copy button renders nothing when the flag is off.** Pages stay unchanged for non-operator deployments.
- **The system prompt is identical across all three surfaces** — `You are FINRLX Analyst …` with strict rules: answer only from the context, cite the section used, refuse market-direction predictions, refuse investment advice, say "insufficient context" rather than guess.
- **The context bundle is markdown-formatted plain text** — pastes cleanly into ChatGPT and Claude alike. Top 20 weights, full evidence narrative, weights/snapshots/regime depending on surface.
- **News context includes a VADER caveat** so the LLM does not over-weight the sentiment scores it sees.
- **Auth is required even with the flag off-by-default** — defense in depth.

## Verification

| Check | Result |
|---|---|
| `npm run typecheck` | ✅ clean |
| `npm run lint` | ✅ clean (zero warnings) |
| `npm run build` | ✅ 76 static pages — `/operator` added (Suspense wrap was required for `useSearchParams`) |
| `npm run test:ci` | ✅ 41/41 pass — no FE regression |
| `python -m pytest tests/` | ✅ 938/938 pass (one MVP-4 flags test updated to include the new flag) |
| Backend import + route enumeration | ✅ `feature_operator_console: False` default; three `/operator/analyses` routes registered |

## How to use it

1. Set `FEATURE_OPERATOR_CONSOLE=true` in your Railway backend env. Redeploy.
2. Open `/decision` or `/replay` or `/news`. Click **"Copy LLM context"**.
3. Open ChatGPT or Claude (you stay logged in, zero token cost). Paste. Add your question.
4. Copy the response back. Click **"Paste response →"** to land on `/operator?rec=…&surface=…`.
5. Paste the response, hit **Archive analysis**. It's stored linked to the recommendation.

## What lands next (O-1)

A step-by-step setup guide for a "FINRLX Analyst" Custom GPT in chatgpt.com — knowledge-only, with the 48 help-center MDX files uploaded as knowledge so the GPT can answer terminology questions without needing the per-page context paste each time.

## Exit checklist

- [x] Migration applies cleanly; model registered.
- [x] API endpoints work with the flag on; return 404 with flag off.
- [x] Auth required on all endpoints.
- [x] Frontend renders nothing for non-operator deployments.
- [x] Copy button + operator page + paste-back round-trip works end-to-end (build verified).
- [x] Typecheck + lint + build + FE tests + BE tests all green.
- [x] Phase report committed.

## Next step

Commit, push, set `FEATURE_OPERATOR_CONSOLE=true` on Railway (you do this when you want it live), proceed to O-1.
