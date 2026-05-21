import { Icon } from "@/components/icons/Icon";
import { fmtDateTime } from "@/lib/format";

import type { HomeSourceState } from "./homeTypes";

const TONE: Record<HomeSourceState, { dot: string; text: string; bg: string }> = {
  ok: { dot: "bg-pos", text: "text-pos-soft-ink", bg: "bg-pos-soft" },
  stale: { dot: "bg-caution", text: "text-caution-soft-ink", bg: "bg-caution-soft" },
  warning: { dot: "bg-caution", text: "text-caution-soft-ink", bg: "bg-caution-soft" },
  unavailable: { dot: "bg-ink-4", text: "text-ink-3", bg: "bg-surface-3" },
};

interface Props {
  label: string;
  asOf?: string | null;
  state: HomeSourceState;
  warning?: string | null;
  className?: string;
}

/**
 * Reusable freshness/provenance pill. Communicates one of four states only —
 * never invents a "live" status. If `asOf` is missing we say so plainly.
 */
export function DataFreshnessBadge({
  label,
  asOf,
  state,
  warning,
  className = "",
}: Props) {
  const tone = TONE[state];
  const asOfLabel =
    state === "unavailable"
      ? "freshness unavailable"
      : asOf
        ? `as of ${fmtDateTime(asOf)}`
        : "freshness unavailable";

  const stateLabel: Record<HomeSourceState, string> = {
    ok: "OK",
    stale: "Stale",
    warning: "Warning",
    unavailable: "Unavailable",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md ${tone.bg} ${tone.text} px-2 py-1 text-[11px] font-medium ${className}`}
      title={warning ?? `${label} · ${asOfLabel}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${tone.dot}`} aria-hidden="true" />
      <span className="font-semibold uppercase tracking-wide text-[10px]">
        {stateLabel[state]}
      </span>
      <span className="text-[11px] font-normal opacity-90">
        {label} · {asOfLabel}
      </span>
      {warning && state !== "ok" && (
        <Icon name="info" size={11} className="ml-0.5 opacity-70" />
      )}
    </span>
  );
}
