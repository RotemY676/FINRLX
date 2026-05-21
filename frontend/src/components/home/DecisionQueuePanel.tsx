import Link from "next/link";

import { Icon } from "@/components/icons/Icon";
import { fmtDateTime } from "@/lib/format";

import { PanelEmpty, PanelShell, PanelUnavailable } from "./HomePanelStates";

import type { HomeDecisionItem } from "./homeTypes";

interface Props {
  items: HomeDecisionItem[];
  isUnavailable?: boolean;
  unavailableMessage?: string;
}

const SEVERITY_TONE: Record<HomeDecisionItem["severity"], { bg: string; ink: string; bar: string }> = {
  critical: {
    bg: "bg-breach-soft",
    ink: "text-breach-soft-ink",
    bar: "bg-breach",
  },
  warning: {
    bg: "bg-caution-soft",
    ink: "text-caution-soft-ink",
    bar: "bg-caution",
  },
  info: {
    bg: "bg-primary-soft",
    ink: "text-primary-soft-ink",
    bar: "bg-primary",
  },
};

/**
 * Decision Queue — primary left-column work surface. Mixed-source list of
 * what needs review: ops queue, pipeline notices, recommendation warnings,
 * active incidents, and breaches.
 */
export function DecisionQueuePanel({ items, isUnavailable, unavailableMessage }: Props) {
  return (
    <PanelShell
      icon="decision"
      title="Decision queue"
      subtitle="What needs review today"
      right={
        <span className="text-[11px] text-ink-3 font-mono">{items.length} items</span>
      }
    >
      <div id="decision-queue" className="space-y-2">
        {isUnavailable ? (
          <PanelUnavailable
            message="Decision queue unavailable."
            hint={
              unavailableMessage
                ? `Source error: ${unavailableMessage}`
                : "One or more source endpoints failed. Other panels remain available."
            }
          />
        ) : items.length === 0 ? (
          <PanelEmpty
            message="Nothing requires review right now."
            hint="The pipeline has no pending warnings, breaches, or incidents."
          />
        ) : (
          items.map((item) => <QueueRow key={item.id} item={item} />)
        )}
      </div>
    </PanelShell>
  );
}

function QueueRow({ item }: { item: HomeDecisionItem }) {
  const tone = SEVERITY_TONE[item.severity];
  return (
    <div className="flex items-start gap-3 rounded-md border border-line bg-surface-2 p-3">
      <span
        className={`mt-1 w-1.5 h-8 rounded-full shrink-0 ${tone.bar}`}
        aria-hidden="true"
      />
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[13px] font-semibold text-ink truncate">
            {item.title}
          </span>
          <span
            className={`text-[10px] uppercase tracking-wide font-semibold px-1.5 py-0.5 rounded ${tone.bg} ${tone.ink}`}
          >
            {item.severity}
          </span>
          <span className="text-[10px] uppercase tracking-wide text-ink-4">
            {item.decisionState}
          </span>
        </div>
        <p className="text-[12px] text-ink-2 mt-1 leading-snug">{item.reason}</p>
        <div className="mt-1.5 flex items-center gap-2 text-[10.5px] text-ink-4">
          <Icon name="info" size={10} />
          <span>source · {item.source}</span>
          {item.lastUpdated && (
            <>
              <span>·</span>
              <span>{fmtDateTime(item.lastUpdated)}</span>
            </>
          )}
        </div>
      </div>
      <Link
        href={item.href}
        className="inline-flex items-center justify-center min-h-11 md:min-h-0 md:py-1.5 px-3 rounded-md bg-surface hover:bg-surface-3 border border-line text-[12px] font-medium text-ink-2 shrink-0 transition-colors"
      >
        {item.actionLabel}
        <Icon name="chevron-right" size={12} className="ml-1" />
      </Link>
    </div>
  );
}
