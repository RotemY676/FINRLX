# FINRLX UX/UI Transformation — Phase 11 Report

## A. Summary

Phase 11 takes the home `ResearchAssistantPreview` from non-interactive
disabled buttons to **real, working entry points** that deep-link to
the operator console with the prompt pre-filled.

The strict architectural fact here: backend `/api/v1/assistant/*`
exists but returns **503** unless `LLM_PROVIDER` is configured. FINRLX
deliberately does not ship a hosted LLM; the canonical assistant flow
is operator-curated (paste GPT/Claude response into the operator
console, attach to a recommendation / replay / news item / manual
surface). Phase 11 wires the home preview into that flow rather than
inventing an in-app LLM that doesn't exist.

## B. Skills used

- `finrlx-ai-ux-governance` — the iron rules: no blank chat, sources required, "FINRLX never tells you to buy or sell", limitations footer, guided prompts.
- `fintech-disclaimer-and-marketing-guard` — the new copy ("the assistant does not trade, approve, or publish recommendations") survives the forbidden-verb sweep.
- `recommendation-object-provenance` — no recommendation surface changed; the operator console already has its own provenance contract.
- `finrlx-ux-redesign-director` — rule 3 (source-grounded AI), rule 7 (no execution language), rule 10 (evidence not optional).
- `finrlx-visual-qa-accessibility-gate` — typecheck / test / build / forbidden-language sweep.
- `finrlx-handoff-evidence-packager` — this report.

## C. External references used

- Phase 0 §1.5 (AlphaSense) — source-grounded answers as a hard requirement.
- Phase 0 §2.2–§2.4 (Reddit r/UXDesign + r/investing) — explicit anti-pattern: blank chat as band-aid for unclear UX. The Phase 11 preview avoids this by shipping five named guided prompts.

## D. Files changed

| File | Purpose |
|---|---|
| `frontend/src/components/home/ResearchAssistantPreview.tsx` | Disabled buttons replaced with `<Link>` entries that deep-link to `/operator?surface=manual&prompt=<encoded>`. Subtitle clarified ("Source-grounded answers via the operator console"). Limitations footer expanded ("FINRLX never tells you to buy or sell"). Typography migrated to Phase 3 named tokens. Chevron-right glyph indicates the prompt links externally. |
| `frontend/src/app/operator/page.tsx` | `OperatorConsoleInner` now reads a `prompt` query param and pre-fills the `prompt` state. Three-line change. Backward-compatible (param is optional). |
| `DOCS/handoff/FINRLX_UX_PHASE_11_REPORT.md` | This report. |

## E. UX decisions

1. **Operator console is the assistant.** Inventing a hosted in-app LLM would be both costly and risky (no backend grounding pipeline yet). The operator console is the canonical FINRLX way to capture LLM context; the home preview now sends users straight there.
2. **Prompts are guided, not blank.** Five named prompts cover the most common decision questions ("Why did this ticker enter the radar?", "Show risk factors for the top position", etc.).
3. **Deep-link with prefill.** Operator console reads `?prompt=…` and pre-fills the prompt textarea. The user still authors the response (pasted from their LLM of choice) — but the round-trip starts faster.
4. **Limitations footer expanded.** "FINRLX never tells you to buy or sell" is the new last line — the most direct expression of the `finrlx-ai-ux-governance` rule.
5. **No backend assistant wiring.** The 503-on-no-`LLM_PROVIDER` contract is preserved. Phase 11 does not ship the embedded chat surface that the master plan §5 Phase 11 also envisions. That ships when the FINRLX team decides to spend tokens (per the assistant.py docstring §1).
6. **No "evidence drawer" component added.** The current shell's `ContextPane` already serves this role for decision/replay surfaces; adding a separate "evidence drawer" component would be either redundant or a parallel system. Defer.

## F. Data / API contract notes

- `GET /api/v1/assistant/status` left unwired on the frontend (would just confirm 503 in current envs). Wiring it once `LLM_PROVIDER` is configured is a one-liner; left as a Phase 11 follow-up.
- `/operator` page contract extended to read `?prompt=…`. Backward-compatible.

## G. Safety / governance notes

- The home preview ships explicit copy: "Answers must be source-grounded. The assistant does not trade, approve, or publish recommendations." and "FINRLX never tells you to buy or sell."
- Forbidden-language sweep: no new hits.
- Operator console retains its existing safety scaffolding (auth-gated under `operator_console` flag; analyses persisted with the analyst's email per the operator API).

## H. Testing evidence

| Command | Result |
|---|---|
| `npm run typecheck` | **PASS** |
| `npm run test:ci -- --testTimeout=15000` | **PASS** — 41 / 41 |
| `npm run build` | **PASS** — 78 routes |
| Forbidden-language sweep | **PASS** |
| `npm run e2e:ci` | **Not run** — no playwright config |

## I. Screenshot evidence

Not captured in this phase. Phase 12 is the multi-page screenshot moment.

## J. Known limitations

1. **No embedded in-app chat surface.** The master plan §5 Phase 11 envisions an embedded source-grounded assistant; that requires backend grounding + an `LLM_PROVIDER` decision. Out of scope for this redesign program.
2. **`/assistant/status` not consumed.** The home preview always reads "via the operator console". When the FINRLX team decides to flip on a provider, the preview will get a live-vs-manual conditional. Two-line follow-up.
3. **No separate evidence drawer.** Existing `ContextPane` is the closest pattern. A dedicated drawer would duplicate state.
4. **No "open evidence" action per assistant answer.** This requires the live chat surface. Until then, the operator console's existing recommendation/replay/news attachment fields serve the same role.

## K. Phase 11 gate compliance

| Gate 11 criterion | Status |
|---|---|
| AI is useful but constrained | **Met** — guided prompts, operator-curated capture, explicit "no buy/sell" |
| Sources are visible | **Met** — operator console already captures source + provider + analyst per analysis |
| Blank-chat UX is avoided | **Met** — no blank text box; five guided prompts |
| AI actions integrate with research/decision workflows | **Met** — prompts deep-link to operator with surface + prompt query params; operator console attaches to recommendations / replays / news items |

**Gate 11 clears (within the operator-console-as-assistant frame).**

## L. Next recommended phase

**Phase 12 — Full-system QA / a11y / visual regression / perf.** The
visual-qa-gate skill defines the command set. Phase 12 will:
1. Re-run typecheck / test:ci / build / forbidden-language sweep
   across the entire repo (not just a phase delta).
2. Attempt the screenshot matrix one more time with a more robust
   server-readiness loop.
3. Run the a11y sweep where possible.
4. Cut a final review-package zip.

If the screenshot matrix still cannot run on this Windows host, Phase
12 will document the gap honestly and the program's UX work will be
considered "ready for Phase 13 (production verification)" with the
test/build evidence as the proof.
