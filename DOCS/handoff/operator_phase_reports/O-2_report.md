# Phase O-2 Report — FINRLX Analyst Claude Project setup guide

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Mirror the Phase O-1 ChatGPT Custom GPT guide for claude.ai Projects so the operator can pick whichever tool fits the task per question.

## What was added

- `DOCS/operator/CLAUDE_PROJECT_SETUP.md` — 5-step guide covering: Project creation, custom instructions block (tuned to Claude's style), one-batch knowledge upload (all 48 help files), file pinning for the most-referenced docs (glossary, weight-centric-pipeline, known-pitfalls, policy-controls), the same 5-question smoke test as the GPT guide, a Claude vs ChatGPT decision matrix, and a "refreshing knowledge later" workflow.

## Design decisions

- **Same Instructions block as O-1, slightly tuned.** The product-mental-model section is identical so the two assistants give consistent answers. Tone guidance is identical (Google + Microsoft style). Refusal templates are identical.
- **One-batch upload (vs O-1's three batches).** Claude Projects accepts a multi-file upload, so the operator drops all 48 files at once instead of three trips. Faster setup than ChatGPT.
- **Pinning the four most-referenced files.** Claude's retrieval window prioritizes pinned files when the conversation grows long, which matters more on Claude than on ChatGPT (longer typical context windows but the same retrieval-pressure problem).
- **A Claude-vs-ChatGPT decision matrix.** The guide explicitly recommends using both: Claude for reasoning + summarization + comparison, ChatGPT for numeric analysis (Code Interpreter) + live data (Custom GPT Actions, future). The operator picks per task.

## What this is NOT

- Not a way to call FINRLX live from Claude. Claude Projects do not have an Actions equivalent yet.
- Not a way to run code or pull live data. For numeric work, the guide explicitly directs the operator to ChatGPT's Code Interpreter.
- Not automated. Knowledge refresh is manual until the Anthropic API is wired up — which requires tokens, out of scope.

## Verification

Documentation phase. Manual review:

- ✅ The 48 file paths in the upload section resolve in the current repo.
- ✅ The 5 starter prompts and 5 smoke-test questions mirror Phase O-1 for cross-tool consistency.
- ✅ The Instructions block reuses the same product mental model and refusal templates as the GPT guide.

## Next step

Commit, push, proceed to O-4 (final phase — wire archived analyses into the Replay page as "Analyst notes").
