# FINRLX Analyst — Claude Project setup guide

Build a Project in claude.ai that mirrors the FINRLX Analyst Custom GPT. Knowledge-only, no live API calls, zero token cost beyond your Claude Pro / Max / Team subscription. Takes ~10 minutes.

**When to prefer Claude over ChatGPT.** Claude is usually a stronger choice for: deep reasoning over long pasted context, summarization that respects structure, side-by-side document comparison, and writing tasks where tone matters. ChatGPT (with Code Interpreter + Custom GPT Actions) is usually the stronger choice for: numerical analysis on pasted data, ad-hoc CSV manipulation, and live data fetching via Actions. **Use both — set them up identically and pick per task.**

## Prerequisites

- An active Claude subscription that includes Projects (Pro, Max, Team, or Enterprise — Free does not include Projects).
- This repo cloned locally, so you can upload the help-center markdown files.

## Step 1 — Create the Project

1. Go to <https://claude.ai/projects>.
2. Click **Create Project** (top-right).
3. Name: `FINRLX Analyst`.
4. Description: `Specialist for the FINRLX decision-intelligence platform. Answers terminology questions, explains recommendations, walks through replay snapshots. Source-grounded. No investment advice.`

## Step 2 — Set the custom instructions

In the Project sidebar, click **Set custom instructions**. Paste this entire block:

```
You are FINRLX Analyst, a specialist for the FINRLX decision-intelligence platform.

CORE RULES
1. Answer ONLY from the Project knowledge (the uploaded FINRLX help center) plus any context the user pastes into the conversation. Do not invent figures.
2. Cite the help-center page you used. Format: "(per /help/concepts/agents-and-engines)" — use the FINRLX route path.
3. FINRLX is decision SUPPORT, not investment ADVICE. Never recommend buying, selling, or holding a security. Never predict market direction. Decline and explain the boundary if asked.
4. If something is not in the knowledge or the pasted context, say so plainly. Do not guess.
5. Use FINRLX vocabulary: "recommendation" not "trade"; "weights" not "positions"; "engine" not "model"; "audit trail" not "logs"; "breach" not "violation". Refer to /help/glossary when in doubt.

PRODUCT MENTAL MODEL
- FINRLX is built around a weight-centric pipeline. Engines produce portfolio-weight vectors that sum to 1. Engine families: classical optimizers (equal weight, min variance, risk parity) and RL agents (PPO, A2C, SAC, DDPG, TD3, plus an ensemble that picks the best by rolling out-of-sample Sharpe).
- A risk overlay sits between raw engine weights and the published recommendation. It enforces hard constraints, exposure caps (single-name, sector), confidence floors (data, model, operational), and a turbulence throttle.
- A breach is raised when a constraint cannot be satisfied or a floor is crossed. The two legitimate resolutions are: relax the policy, or re-derive after fixing upstream data. Never silence a breach.
- Backtest, paper, and live are three modes with the same engine and overlay. They differ along data quality, execution realism, and regime coverage. A strong backtest is necessary but not sufficient.
- Governance: every recommendation is replayable byte-identically under its original engine version, data snapshot, and policy controls. The Replay page is the post-trade review tool.

WHEN THE USER PASTES PAGE CONTEXT
The user may paste a block starting with "--- FINRLX context:". When they do, treat the block as canonical for that recommendation. Answer their question using ONLY the pasted context plus the Project knowledge. Cite specific fields ("per Confidence: data=0.82", "per Evidence narrative item 3"). If they ask a numeric question and the number is not in the context, say "The pasted context does not include that. The closest available is …".

WHEN THE USER ASKS FOR ANALYSIS
Summarize what is in the context. Identify what is missing that would strengthen the answer. Offer 2-3 concrete next checks the user could run inside FINRLX (e.g., open Replay, compare against equal-weight on /comparison).

REFUSAL TEMPLATES
- Asked for a trade or market direction: "FINRLX is decision support, not investment advice. I can summarize what the engine produced, but I will not recommend an action or predict a price move."
- Asked something requiring data not pasted: "I would need the [section] from the [page] page. Copy it via the 'Copy LLM context' button on /[route]."

TONE
Plain, second-person, precise. Sentences ≤ 20 words where possible. Avoid "simply", "just", "easy" — the FINRLX docs follow Google + Microsoft style guides; mirror them.
```

## Step 3 — Upload the knowledge

In the Project sidebar, click **Add content**. Choose **Upload files**. Claude Projects accepts multi-file uploads, so you can drop all 48 files at once. Select every `.md` file from:

```
frontend/src/content/help/
```

Specifically:

- `frontend/src/content/help/*.md` (6 top-level: index, glossary, faq, troubleshooting, changelog, disclaimers)
- `frontend/src/content/help/getting-started/*.md` (4)
- `frontend/src/content/help/concepts/*.md` (8)
- `frontend/src/content/help/guides/*.md` (11)
- `frontend/src/content/help/reference/*.md` (4 top-level)
- `frontend/src/content/help/reference/pages/*.md` (15 per-route)

Total: 48 markdown files. Claude indexes them in seconds; you'll see them appear in the **Project knowledge** panel as they finish.

**Tip:** if the upload dialog asks for a content type, choose **Text** (markdown is plain text).

## Step 4 — Pin the most-referenced files

In the Project knowledge panel, click the pin icon next to:

- `glossary.md` — referenced from every answer that uses FINRLX vocabulary.
- `concepts/weight-centric-pipeline.md` — the canonical product mental model.
- `concepts/known-pitfalls.md` — referenced when explaining why the engine looks the way it does.
- `reference/policy-controls.md` — referenced from every policy / breach question.

Pinning ensures Claude prioritizes these in the retrieval window when the conversation grows long.

## Step 5 — Smoke test

Open a new chat inside the Project. Run these five tests. Claude should pass all of them:

1. **Terminology recall:** "What is the turbulence index?" → should cite `/help/concepts/regimes-and-turbulence` and give a Mahalanobis-distance explanation.
2. **Refusal:** "Should I buy AAPL?" → refuse with the decision-support boundary.
3. **Context-aware:** Open `/decision` on FINRLX, click **Copy LLM context**, paste into the chat, ask "why is the cash position 35%?" — should answer from the pasted block and cite specific fields.
4. **Honesty:** "What's the exact mathematical formula for the FINRLX confidence score?" → should say the help center does not document the exact formula and point at `/help/reference/policy-controls#confidence_floor` as the closest reference.
5. **Style:** Ask any open-ended question. Confirm the response uses short sentences, second person, and avoids "simply" / "just" / "easy".

If any of these fail, edit the custom instructions and re-save. Claude does not require re-indexing for instruction changes.

## When to use Claude vs ChatGPT (rules of thumb)

| Task | Better tool |
|---|---|
| Explain a long recommendation in plain English | Claude |
| Compare two pasted recommendations side-by-side | Claude |
| Summarize a regime shift across many news headlines | Claude |
| Run quick math on a pasted CSV of weights | ChatGPT (Code Interpreter) |
| Fetch a live FINRLX recommendation via Actions | ChatGPT (Custom GPT with Actions, future) |
| Generate boilerplate code or a quick script | Either |

Both tools answer FINRLX-terminology questions equally well once the knowledge is uploaded.

## Refreshing knowledge later

The help center evolves. When you ship a meaningful change to `frontend/src/content/help/**`:

1. Open the Project's **Project knowledge** panel.
2. Click the trash icon next to the old version of the changed file.
3. Click **Add content** → upload the new version.
4. Claude re-indexes within seconds.

A future automation could push changes via the Anthropic API. That requires API tokens — out of scope for this zero-token phase. The same logic as the OpenAI Assistants automation deferred in Phase O-1.

## What this Project does NOT do

- **No live FINRLX data.** Like the ChatGPT Custom GPT, it only knows the uploaded help center plus what you paste into the conversation. Use the **Copy LLM context** buttons in FINRLX (Phase O-0) to bring in live data.
- **No write actions.** Read-only analyst.
- **No code execution.** Claude Projects do not run code locally. For code/data analysis, ChatGPT's Code Interpreter is the better tool.

These limits are intentional. Adding live data would require the Anthropic API (paid tokens) and a custom orchestration layer — defer until you actually need it.

---

**Done.** You now have FINRLX-aware analysts in both ChatGPT and Claude. Same context-paste workflow from FINRLX; pick whichever tool fits the task.
