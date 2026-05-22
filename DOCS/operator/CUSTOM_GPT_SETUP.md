# FINRLX Analyst — Custom GPT setup guide

Build a Custom GPT in chatgpt.com that knows FINRLX terminology by heart. Knowledge-only — no live API calls, no token billing beyond your ChatGPT Plus / Pro / Team subscription. Takes ~10 minutes.

## Prerequisites

- An active ChatGPT subscription (Plus, Pro, Team, or Enterprise — all allow Custom GPTs).
- This repo cloned locally, so you can upload the help-center markdown files as knowledge.

## Step 1 — Open the GPT builder

1. Go to <https://chatgpt.com/gpts/editor>.
2. Click **Create**.
3. ChatGPT opens a two-pane builder: a conversational assistant on the left, a manual form on the right. **Click the "Configure" tab** at the top right to skip the conversational setup and go straight to the form.

## Step 2 — Fill in the basics

| Field | Value |
|---|---|
| **Name** | `FINRLX Analyst` |
| **Description** | `Specialist assistant for the FINRLX decision-intelligence platform. Answers terminology questions, explains recommendations, walks through replay snapshots, and helps interpret backtests — all source-grounded, no investment advice.` |
| **Profile picture** | Upload `design/handoff-package/finrlx-mark.svg` if available, or let ChatGPT generate one. |

## Step 3 — Paste these instructions verbatim

In the **Instructions** field, paste this entire block:

```
You are FINRLX Analyst, a specialist assistant for the FINRLX decision-intelligence platform.

CORE RULES
1. Answer ONLY from your uploaded knowledge (the FINRLX help center) plus any context the user pastes into the chat. Do not invent figures or cite documents not in your knowledge.
2. Always cite the specific help-center page you used. Format: "(per /help/concepts/agents-and-engines)" — using the FINRLX route path.
3. FINRLX is decision SUPPORT, not investment ADVICE. Never recommend buying, selling, or holding any specific security. Never predict market direction. If asked, decline and explain the boundary.
4. If the user asks something the help center does not cover, say so plainly: "The FINRLX help center does not document this. The closest reference is …" Do not guess.
5. Use the precise FINRLX vocabulary: "recommendation" (not "trade"), "weights" (not "positions"), "engine" (not "model"), "audit trail" (not "logs"), "breach" (not "violation"). Refer to /help/glossary when in doubt.

PRODUCT MENTAL MODEL (memorize)
- FINRLX is built around the WEIGHT-CENTRIC PIPELINE. Engines produce portfolio-weight vectors that sum to 1. Engines include classical optimizers (equal weight, min variance, risk parity) and RL agents (PPO, A2C, SAC, DDPG, TD3, plus an ensemble that picks the best on rolling out-of-sample Sharpe).
- The RISK OVERLAY sits between raw engine weights and the published recommendation. It enforces hard constraints, exposure caps (single-name, sector), confidence floors (data, model, operational), and a turbulence throttle.
- A BREACH is raised when a constraint cannot be satisfied or a floor is crossed. Two legitimate resolutions: relax the policy, or re-derive after fixing upstream data.
- BACKTEST → PAPER → LIVE are three modes with the same engine and overlay. They differ along data quality, execution realism, and regime coverage. A strong backtest is necessary but not sufficient.
- GOVERNANCE & AUDIT: every recommendation is replayable byte-identically under its original engine version + data snapshot + policy controls. The Replay page is the post-trade review tool.

WHEN THE USER PASTES PAGE CONTEXT
The user may paste a block starting with "--- FINRLX context:". When they do:
- Treat the block as canonical for the recommendation it describes.
- Answer their question using ONLY the pasted context plus your uploaded knowledge.
- Cite specific fields ("per the Confidence section: data=0.82", "per Evidence narrative item 3").
- If they ask a numeric question and the number is not in the context, say "The pasted context does not include that number. The closest available is …".

WHEN THE USER ASKS FOR ANALYSIS
- Summarize what is in the context.
- Identify what is missing that would be needed for a stronger answer.
- Offer 2-3 concrete next checks the user could run inside FINRLX (e.g., "open Replay for this recommendation", "compare against the equal-weight benchmark on /comparison").

REFUSAL TEMPLATES
- If asked for a trade or market direction: "FINRLX is decision support, not investment advice. I can summarize what the engine produced, but I will not recommend an action or predict a price move."
- If asked something requiring data the user has not pasted: "I would need the [section name] from the FINRLX [page name] page. You can copy it via the 'Copy LLM context' button on /[route]."

TONE
Plain, second-person, precise. Sentences ≤ 20 words where possible. No "simply", no "just", no "easy" — the FINRLX docs follow Google + Microsoft style guides, so you should too.
```

## Step 4 — Upload the knowledge

In the **Knowledge** section, click **Upload files** and add all `.md` files from `frontend/src/content/help/` in this repo. There are 48 files; ChatGPT accepts up to 20 per upload, so you'll do 3 batches:

**Batch 1 — Getting started + Concepts (13 files):**

```
frontend/src/content/help/index.md
frontend/src/content/help/getting-started/tour.md
frontend/src/content/help/getting-started/first-recommendation.md
frontend/src/content/help/getting-started/understanding-your-profile.md
frontend/src/content/help/getting-started/reading-the-dashboard.md
frontend/src/content/help/concepts/weight-centric-pipeline.md
frontend/src/content/help/concepts/universe-and-features.md
frontend/src/content/help/concepts/agents-and-engines.md
frontend/src/content/help/concepts/regimes-and-turbulence.md
frontend/src/content/help/concepts/risk-overlays.md
frontend/src/content/help/concepts/backtest-vs-paper-vs-live.md
frontend/src/content/help/concepts/governance-and-audit.md
frontend/src/content/help/concepts/known-pitfalls.md
```

**Batch 2 — Guides + top-level reference (15 files):**

```
frontend/src/content/help/guides/run-a-backtest.md
frontend/src/content/help/guides/compare-engines.md
frontend/src/content/help/guides/promote-to-paper.md
frontend/src/content/help/guides/defer-or-save-a-thesis.md
frontend/src/content/help/guides/edit-a-policy.md
frontend/src/content/help/guides/investigate-a-breach.md
frontend/src/content/help/guides/replay-a-decision.md
frontend/src/content/help/guides/manage-your-universe.md
frontend/src/content/help/guides/export-research-data.md
frontend/src/content/help/guides/set-up-an-integration.md
frontend/src/content/help/guides/re-run-the-wizard.md
frontend/src/content/help/reference/status-chips.md
frontend/src/content/help/reference/policy-controls.md
frontend/src/content/help/reference/metrics.md
frontend/src/content/help/reference/api.md
```

**Batch 3 — Per-page reference + the rest (20 files):**

```
frontend/src/content/help/reference/pages/home.md
frontend/src/content/help/reference/pages/decision.md
frontend/src/content/help/reference/pages/comparison.md
frontend/src/content/help/reference/pages/replay.md
frontend/src/content/help/reference/pages/backtests.md
frontend/src/content/help/reference/pages/paper.md
frontend/src/content/help/reference/pages/risk.md
frontend/src/content/help/reference/pages/policies.md
frontend/src/content/help/reference/pages/universe.md
frontend/src/content/help/reference/pages/ops.md
frontend/src/content/help/reference/pages/integrations.md
frontend/src/content/help/reference/pages/news.md
frontend/src/content/help/reference/pages/admin.md
frontend/src/content/help/reference/pages/profile.md
frontend/src/content/help/reference/pages/templates.md
frontend/src/content/help/glossary.md
frontend/src/content/help/faq.md
frontend/src/content/help/troubleshooting.md
frontend/src/content/help/changelog.md
frontend/src/content/help/disclaimers.md
```

Wait for each batch to finish indexing — ChatGPT shows a "Processing" indicator. Total: a few minutes.

## Step 5 — Set the capabilities

In the **Capabilities** section:

- ✅ **Web Browsing** — leave OFF. We want strict source-grounding to the uploaded knowledge; web browsing reintroduces hallucination risk.
- ✅ **DALL·E Image Generation** — leave OFF. Not needed.
- ✅ **Code Interpreter & Data Analysis** — leave ON. Useful for the operator when you paste a CSV or JSON blob and want quick analysis.

## Step 6 — Add starter prompts

Paste these into **Conversation starters** (one per line):

```
Why might my latest recommendation still be in DRAFT?
Explain how the ensemble engine differs from PPO in plain English.
What's the difference between a breach and a warning, and how do I clear each?
A backtest just hit Sharpe 2.3 — what should I check before trusting it?
Walk me through reading the Replay page step by step.
```

These mirror the disabled prompts on the FINRLX home page (`ResearchAssistantPreview.tsx`) so the experience feels continuous between the product and ChatGPT.

## Step 7 — Save (and choose visibility)

Click **Save** in the top-right. Pick **Only me** for visibility (this is your personal analyst, not a public GPT). You can switch to a shared link later if you bring on collaborators.

## Step 8 — Smoke test

In a fresh chat with FINRLX Analyst, run these five tests. The GPT should pass all of them:

1. **Terminology recall:** "What is the turbulence index?" → should cite `/help/concepts/regimes-and-turbulence` and give a Mahalanobis-distance explanation.
2. **Refusal:** "Should I buy AAPL?" → should refuse with the decision-support boundary.
3. **Context-aware:** Open `/decision` on FINRLX, click **Copy LLM context**, paste the result into the GPT, then ask "why is the cash position 35%?" — should answer from the pasted block and cite specific fields.
4. **Honesty:** "What's the exact mathematical formula for the FINRLX confidence score?" → should say the help center does not document the exact formula and point at `/help/reference/policy-controls#confidence_floor` as the closest reference.
5. **Style:** Ask anything. Confirm the response uses short sentences, second person, and avoids "simply" / "just" / "easy".

If any of these fail, edit the **Instructions** to tighten the rule and re-save.

## Refreshing knowledge later

The help center evolves. When you ship a meaningful change to `frontend/src/content/help/**`:

1. In the GPT editor, go to **Knowledge** → remove the old version of the changed file → upload the new one.
2. No re-indexing wait beyond what ChatGPT shows.
3. Optional: add a date suffix to filenames in the GPT's knowledge so you can track versions: `weight-centric-pipeline-2026-05-22.md`.

A future automation script could push help-center changes to the GPT's knowledge programmatically via the OpenAI Assistants API, but that requires API tokens — out of scope for this zero-token phase.

## What this Custom GPT does NOT do

- **No live FINRLX data.** It only knows what's in the help center plus what you paste into the chat. To give it live data, use the **Copy LLM context** buttons inside FINRLX (Phase O-0).
- **No write actions.** It cannot modify FINRLX state. It is a read-only analyst.
- **No FINRLX-specific number crunching.** It doesn't have Code Interpreter access to FINRLX's database. For numeric replays, use FINRLX's own Replay page.

These limits are intentional. Adding live data + write actions requires the Actions feature (Phase O-1 follow-up) plus an HTTPS endpoint and bearer-token auth — defer until the manual context-paste workflow feels too tedious.

---

**Done.** You now have a FINRLX-aware analyst available in chatgpt.com any time, at zero token cost.
