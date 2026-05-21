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
 * Research assistant preview — non-interactive. There is no live assistant
 * backend on the home page, so this card is honest about its scope: it
 * shows the kinds of questions you can ask, and the rules the assistant
 * follows when one ships.
 */
export function ResearchAssistantPreview() {
  return (
    <PanelShell
      icon="sparkle"
      title="Research assistant"
      subtitle="Source-grounded answers. Preview only."
    >
      <p className="text-[12px] text-ink-2 leading-relaxed">
        Ask FINRLX about a ticker, thesis, risk, filing, signal, or decision.
        Answers must be source-grounded. AI does not trade, approve, or publish
        recommendations.
      </p>
      <div className="mt-3 space-y-1.5">
        {SUGGESTED_PROMPTS.map((p) => (
          <button
            key={p}
            type="button"
            disabled
            aria-disabled="true"
            className="w-full text-left rounded-md border border-line bg-surface-2 px-3 min-h-11 md:min-h-0 md:py-2 text-[12px] text-ink-2 hover:border-primary hover:bg-surface-3 transition-colors flex items-center gap-2"
            title="Preview only — assistant ships in a later phase"
          >
            <Icon name="search" size={12} className="text-ink-4 shrink-0" />
            <span className="truncate">{p}</span>
          </button>
        ))}
      </div>
      <p className="mt-3 text-[10.5px] text-ink-4 leading-snug">
        The assistant must cite a source for every claim, label uncertainty
        explicitly, and decline questions that ask for a trade instruction.
      </p>
    </PanelShell>
  );
}
