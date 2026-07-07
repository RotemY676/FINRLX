import Link from "next/link";

import { Icon } from "@/components/icons/Icon";

import { PanelShell } from "./HomePanelStates";

const SUGGESTED_PROMPTS = [
  "Why did this ticker enter the radar?",
  "Show risk factors for the top position.",
  "Compare engines on the current recommendation.",
  "Explain stale data on the regime panel.",
  "Summarize evidence behind today's queue.",
];

/**
 * Phase 11 — Research assistant entry-point card.
 *
 * No live in-app LLM yet (backend `/api/v1/assistant/*` returns 503
 * unless `LLM_PROVIDER` is configured). FINRLX's canonical path for
 * assistant context today is the operator console at `/pro/operator`,
 * which captures GPT/Claude responses against a recommendation,
 * replay, news item, or manual surface.
 *
 * Each suggested prompt deep-links to `/pro/operator?surface=manual&prompt=...`
 * so the operator lands with the question pre-filled.
 *
 * Constraints encoded by `finrlx-ai-ux-governance`:
 *   - assistant is NEVER a trading interface
 *   - sources are required on every answer
 *   - blank-chat-as-band-aid is forbidden — guided prompts only
 *   - limitations footer always present
 */
export function ResearchAssistantPreview() {
  return (
    <PanelShell
      icon="sparkle"
      title="Research assistant"
      subtitle="Source-grounded answers via the operator console"
    >
      <p className="text-caption text-ink-2 leading-relaxed">
        Ask FINRLX about a ticker, thesis, risk, filing, signal, or decision.
        Answers must be source-grounded. The assistant does not trade,
        approve, or publish recommendations.
      </p>
      <div className="mt-3 space-y-1.5">
        {SUGGESTED_PROMPTS.map((p) => (
          <Link
            key={p}
            href={`/pro/operator?surface=manual&prompt=${encodeURIComponent(p)}`}
            className="w-full text-left rounded-md border border-line bg-surface-2 px-3 min-h-11 md:min-h-0 md:py-2 text-caption text-ink-2 hover:border-primary hover:bg-surface-3 transition-colors flex items-center gap-2"
            title="Opens the operator console with this prompt pre-filled"
          >
            <Icon name="search" size={12} className="text-ink-4 shrink-0" />
            <span className="truncate">{p}</span>
            <Icon name="chevron-right" size={12} className="text-ink-4 shrink-0 ml-auto" />
          </Link>
        ))}
      </div>
      <p className="mt-3 text-meta text-ink-4 leading-snug">
        The assistant must cite a source for every claim, label uncertainty
        explicitly, and decline questions that ask for a trade instruction.
        FINRLX never tells you to buy or sell.
      </p>
    </PanelShell>
  );
}
