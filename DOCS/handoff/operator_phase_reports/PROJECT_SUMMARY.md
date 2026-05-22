# Hybrid LLM Strategy — Project closing summary

**Project:** Hybrid Claude + ChatGPT integration for a single-operator product, zero token cost
**Completed:** 2026-05-22
**Branch:** main (every phase committed and pushed)

## The constraint that shaped the project

- **One user (you, the operator).** No public rollout in scope.
- **Existing subscriptions to both ChatGPT and Claude.** No willingness to pay per-token API fees right now.
- **Don't ship a worse experience for the lack of API access.** The single-user product should still be smarter for having LLM tools available.

These constraints made an obvious-but-easy-to-miss observation true: **the right LLM UX for a single operator is not "embedded chat in the product." It's "make the product the best possible data source for the LLM tabs you already have open."** That is the entire strategy in one sentence.

## What shipped

### 4 active phases + 1 stub phase

| Phase | What | Touch points |
|---|---|---|
| **O-0** | Operator console scaffold + Copy-LLM-Context buttons on Decision, Replay, News + pasteback form | Backend: migration 028, OperatorAnalysis model, /api/v1/operator/analyses endpoints, feature_operator_console flag. Frontend: contextBuilder lib, CopyLLMContextButton, /operator route, wiring on Decision / Replay / News. |
| **O-1** | "FINRLX Analyst" Custom GPT setup guide | `DOCS/operator/CUSTOM_GPT_SETUP.md` — 8 steps, verbatim 50-line Instructions block, three upload batches for the 48 help-center MDX files, 5-question smoke test. |
| **O-5** | LLM provider abstraction (stub-wired) | Backend: `app/services/llm/` (Anthropic / OpenAI / Local providers, router, types), `/api/v1/assistant/*` endpoints (chat / narrative / news-explain / status), 10 unit tests. All providers stub-raise; endpoints return 503 with friendly detail pointing at `/operator`. |
| **O-2** | Claude Project setup guide | `DOCS/operator/CLAUDE_PROJECT_SETUP.md` — 5 steps, mirrored Instructions block, single-batch upload of the 48 MDX files, file pinning guidance, Claude-vs-ChatGPT decision matrix. |
| **O-4** | Analyst Notes panel on Replay | Frontend: `AnalystNotesPanel` component fetching `listOperatorAnalyses({ recommendation_id })`, rendered below Pipeline Stage Snapshots on the Replay page. Round-trip closed. |

### Skipped (per your explicit decision)

- **O-3 Local Ollama** — skipped. Deferred until batch sentiment classification becomes a real need; the infrastructure for it (provider abstraction in O-5) ships ready to receive it.

## End-to-end round trip in the live product

Once `FEATURE_OPERATOR_CONSOLE=true` is set on Railway:

1. Open `/decision`. Click **Copy LLM context**.
2. Open ChatGPT (FINRLX Analyst GPT) or Claude (FINRLX Analyst Project). Paste.
3. Ask any question. Get a source-grounded answer with citations.
4. Click **Paste response →** on the same Decision page. Lands on `/operator?rec=…&surface=decision`.
5. Paste the LLM response, add a note, **Archive analysis**.
6. Later on `/replay` for the same recommendation, the **Analyst notes** section shows the archived analysis with source / surface / timestamp / prompt / response.

Total token cost: **$0**. (Counts against your existing ChatGPT and Claude subscriptions.)

## When you decide to spend tokens

Activation runbook for the in-app Research Assistant (no FE changes needed):

1. `pip install anthropic` (or `openai`) — add to `backend/requirements.txt`.
2. Open `backend/app/services/llm/anthropic.py` (or `openai.py`). Replace the `chat()` stub body with the real SDK call from the module docstring (it's already there, fully written).
3. Set Railway env: `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=...`, optionally `LLM_MODEL=claude-sonnet-4-6`.
4. Redeploy.

Every `/api/v1/assistant/*` endpoint that returned 503 starts returning real responses. The FE Research Assistant panel can be wired to call them when you're ready to ship the in-app chat experience.

## What I'd watch for in the next 30 days of use

- **Pasteback friction.** If the Copy-context → paste-into-chat → paste-back loop feels tedious after ~50 uses, the Custom GPT Actions setup (deferred from O-1) becomes the next obvious investment — it skips the manual context paste.
- **Drift between the GPT and Claude analysts.** If the two start giving meaningfully different answers to the same FINRLX-terminology question, that's a signal the help-center docs they're trained on need clarification — fix the docs, re-upload to both, drift closes.
- **Notes accumulating without re-read.** If you write a lot of analyst notes but never go back to read them on Replay, the panel is solving the wrong problem. Either drop the archive step or surface notes more aggressively (sidebar badge, home-page highlight).
- **The skipped Phase O-3.** If you find yourself wanting per-ticker social-sentiment scores often enough to consider automation, that's when O-3 (local Ollama or the OpenAI Batch API mentioned earlier) earns its setup cost.

## Phase reports

Detailed per-phase reports under `DOCS/handoff/operator_phase_reports/`:

- `O-0_report.md` — operator console scaffold.
- `O-1_report.md` — Custom GPT setup guide.
- `O-5_report.md` — provider abstraction stub.
- `O-2_report.md` — Claude Project setup guide.
- `O-4_report.md` — Analyst Notes panel on Replay.

## Strategic-plan adherence

Every element of the strategy I proposed earlier was delivered, in the order you approved (O-0 → O-1 → O-5 → O-2 → O-4):

- ✅ Operator console with Copy-LLM-Context on Decision, Replay, **and News** (your specific scope decision).
- ✅ Knowledge-only Custom GPT setup guide (your specific scope decision — no Actions for now).
- ✅ Skipped Phase O-3 entirely (your specific scope decision).
- ✅ Provider abstraction stubbed for the future-spend path.
- ✅ Both ChatGPT and Claude given setup parity.
- ✅ Round-trip closed via the Analyst Notes panel on Replay.
- ✅ Each phase pushed only after `typecheck + lint + build + tests` green; no surprises in the audit trail.

## Verification numbers (cumulative)

- **Code:** 1 backend module (`app/services/llm/`), 1 new migration, 2 new model files, 2 new API files, 4 new frontend components, 1 new lib, 1 new service, 1 new route, edits to 7 existing files.
- **Tests:** 10 new backend tests (all 948/948 pass), 41/41 frontend tests stay green.
- **Docs:** 2 setup guides (CUSTOM_GPT_SETUP.md, CLAUDE_PROJECT_SETUP.md), 5 phase reports, this summary.
- **Build:** 76 prerendered pages (`/operator` added), no first-load-JS regression on existing pages.
- **Live deploy:** ready to ship — set `FEATURE_OPERATOR_CONSOLE=true` on Railway when you want the surface live.
