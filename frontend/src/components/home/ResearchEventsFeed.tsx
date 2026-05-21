import { Icon } from "@/components/icons/Icon";
import { fmtDateTime } from "@/lib/format";

import { PanelEmpty, PanelShell } from "./HomePanelStates";

import type { ResearchEventItem } from "./homeTypes";

interface Props {
  items: ResearchEventItem[];
}

const TONE_STYLE: Record<ResearchEventItem["tone"], { bg: string; ink: string; icon: string }> = {
  info: { bg: "bg-primary-soft", ink: "text-primary-soft-ink", icon: "info" },
  warning: { bg: "bg-caution-soft", ink: "text-caution-soft-ink", icon: "alert-triangle" },
  critical: { bg: "bg-breach-soft", ink: "text-breach-soft-ink", icon: "risk" },
  muted: { bg: "bg-surface-3", ink: "text-ink-3", icon: "news" },
};

function kindIcon(kind: ResearchEventItem["kind"]): string {
  if (kind === "incident") return "alert-triangle";
  if (kind === "news") return "news";
  return "history";
}

export function ResearchEventsFeed({ items }: Props) {
  return (
    <PanelShell
      icon="news"
      title="Research events"
      subtitle="Audit + news, decision-context only"
    >
      {items.length === 0 ? (
        <PanelEmpty
          message="No recent research events."
          hint="Audit and news activity will appear here."
        />
      ) : (
        <ul className="space-y-1.5">
          {items.map((it, idx) => {
            const tone = TONE_STYLE[it.tone];
            return (
              <li
                key={`${it.kind}-${idx}`}
                className="flex items-start gap-2.5 py-1 border-b border-line last:border-b-0"
              >
                <span
                  className={`w-6 h-6 rounded-md inline-flex items-center justify-center shrink-0 ${tone.bg} ${tone.ink}`}
                >
                  <Icon name={kindIcon(it.kind)} size={11} />
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-[12.5px] text-ink-2 line-clamp-2">{it.title}</p>
                  <p className="text-[10.5px] text-ink-4 flex items-center gap-1.5">
                    <span className="uppercase tracking-wide">{it.kind}</span>
                    {it.detail && <span>· {it.detail}</span>}
                    {it.whenAgo && <span>· {it.whenAgo}</span>}
                    {!it.whenAgo && it.occurredAt && (
                      <span>· {fmtDateTime(it.occurredAt)}</span>
                    )}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </PanelShell>
  );
}
