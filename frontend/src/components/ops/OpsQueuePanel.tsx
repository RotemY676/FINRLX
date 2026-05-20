"use client";

import { useState } from "react";

import { OpsQueueItem, approveQueueItem, deferQueueItem, challengeQueueItem } from "@/services/api";
import { Icon } from "@/components/icons/Icon";

const PRIORITY_STYLE: Record<string, string> = {
  high: "bg-breach-soft text-breach-soft-ink",
  mid: "bg-caution-soft text-caution-soft-ink",
  low: "bg-surface-3 text-ink-3",
};

interface Props {
  items: OpsQueueItem[];
  onActionDone: (id: string, message: string) => void;
}

export function OpsQueuePanel({ items, onActionDone }: Props) {
  const [busyId, setBusyId] = useState<string | null>(null);

  const runAction = async (
    item: OpsQueueItem,
    action: "approve" | "defer" | "challenge",
  ) => {
    if (!item.id) return;
    setBusyId(item.id);
    try {
      const fn = action === "approve" ? approveQueueItem : action === "defer" ? deferQueueItem : challengeQueueItem;
      const res = await fn(item.id);
      onActionDone(item.id, res.data.message);
    } catch (err) {
      onActionDone(item.id ?? "?", err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  };

  if (items.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <h3 className="text-[13px] font-semibold text-ink mb-2">Publication queue</h3>
        <p className="text-[12.5px] text-ink-3">Queue is empty.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <div className="flex items-baseline justify-between mb-3 gap-2">
        <h3 className="text-[13px] font-semibold text-ink">Publication queue</h3>
        <span className="text-[11px] text-ink-4">{items.length} pending</span>
      </div>
      <ul className="space-y-2" role="list">
        {items.map((item) => {
          const id = item.id ?? item.recommendation_id;
          const isBusy = busyId === id;
          return (
            <li
              key={id}
              className="rounded-md border border-line/60 p-3 flex flex-col md:flex-row md:items-center md:justify-between gap-2"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center flex-wrap gap-2">
                  <span className="font-mono font-semibold text-ink text-[13px]">{item.ticker}</span>
                  <span className={`px-2 py-0.5 rounded-md text-[11px] font-medium ${PRIORITY_STYLE[item.priority] ?? PRIORITY_STYLE.low}`}>
                    {item.priority}
                  </span>
                  <span className="text-[11px] text-ink-3">
                    {item.stance} · {item.weight} · conf {(item.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-[11px] text-ink-4 mt-1">
                  {item.submitter} · {item.submitted_ago}
                  {item.flags.length > 0 && (
                    <span className="text-caution"> · {item.flags.join(", ")}</span>
                  )}
                </p>
              </div>
              <div className="flex items-center flex-wrap gap-2 shrink-0">
                <button
                  type="button"
                  disabled={isBusy || !item.id}
                  onClick={() => runAction(item, "approve")}
                  className="inline-flex items-center gap-1 min-h-11 md:min-h-0 md:h-9 px-3 rounded-md bg-pos text-primary-ink text-[12.5px] font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  <Icon name="check" size={13} /> Approve
                </button>
                <button
                  type="button"
                  disabled={isBusy || !item.id}
                  onClick={() => runAction(item, "defer")}
                  className="inline-flex items-center gap-1 min-h-11 md:min-h-0 md:h-9 px-3 rounded-md bg-surface-3 text-ink-2 text-[12.5px] font-medium hover:bg-line transition-colors disabled:opacity-50"
                >
                  <Icon name="clock" size={13} /> Defer
                </button>
                <button
                  type="button"
                  disabled={isBusy || !item.id}
                  onClick={() => runAction(item, "challenge")}
                  className="inline-flex items-center gap-1 min-h-11 md:min-h-0 md:h-9 px-3 rounded-md bg-caution-soft text-caution-soft-ink text-[12.5px] font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  <Icon name="alert-triangle" size={13} /> Challenge
                </button>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
