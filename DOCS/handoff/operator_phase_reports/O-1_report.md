# Phase O-1 Report — FINRLX Analyst Custom GPT setup guide

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Write a step-by-step setup guide so the operator can build a "FINRLX Analyst" Custom GPT in chatgpt.com — knowledge-only, against the existing ChatGPT subscription, zero token cost.

## What was added

- `DOCS/operator/CUSTOM_GPT_SETUP.md` — 8-step guide covering: GPT builder navigation, the exact name + description + profile picture, a verbatim 50-line **Instructions** block enforcing source-grounded answers + FINRLX vocabulary + refusal templates, three upload batches covering all 48 help-center MDX files, capability toggles (web browsing OFF, code interpreter ON), 5 starter prompts mirroring the disabled prompts on the FINRLX home page, save + visibility, a 5-question smoke test, and a "refreshing knowledge later" workflow.

## Design decisions

- **Web browsing OFF.** Keeps the GPT strictly source-grounded to the uploaded knowledge. Browsing reintroduces hallucination risk we explicitly avoid in the help center voice.
- **Starter prompts mirror `ResearchAssistantPreview.tsx`.** Continuity between the FINRLX in-app preview and the actual GPT — when the operator clicks "Why might my latest recommendation still be in DRAFT?" in either place, the answer comes back the same way.
- **Three upload batches.** ChatGPT's 20-file-per-batch limit means three trips to the uploader; the guide lists the files in deliberate order (concepts first so the GPT learns terminology before page references).
- **Smoke test included.** Five concrete checks the operator can run after setup to confirm the GPT is behaving correctly. Includes a refusal check (no investment advice) and a context-paste round-trip with the Phase O-0 button.

## What this is NOT

- Not an Actions setup. Actions require exposing FINRLX over HTTPS with bearer-token auth and writing an OpenAPI spec — deferred until the manual context-paste workflow feels tedious. The guide notes this explicitly.
- Not automated. Help-center updates require re-uploading changed files in the GPT editor. A future automation via the OpenAI Assistants API would require API tokens — out of scope.

## Verification

Documentation phase — no code, no tests. Manual review of the markdown for accuracy:

- ✅ All 48 help-center file paths in the upload batches resolve in the current repo (re-checked against `Get-ChildItem` from H-1 — 48 files confirmed).
- ✅ The 5 starter prompts match the ones in `frontend/src/components/home/ResearchAssistantPreview.tsx` lines 32-44.
- ✅ The Instructions block uses FINRLX-specific routes (`/help/concepts/...`, `/help/reference/...`) so citations land on real pages.
- ✅ Refusal language matches the legal disclaimer wording in the existing `DisclaimerBanner` / `DisclaimerModal` components.

## Next step

Commit, push, then proceed to O-5 (provider abstraction stub).
