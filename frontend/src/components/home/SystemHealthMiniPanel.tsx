import { PanelEmpty, PanelShell } from "./HomePanelStates";

import type { HomeSourceState, SystemHealthRow } from "./homeTypes";

interface Props {
  rows: SystemHealthRow[];
}

const STATE_TONE: Record<HomeSourceState, { dot: string; ink: string }> = {
  ok: { dot: "bg-pos", ink: "text-pos" },
  stale: { dot: "bg-caution", ink: "text-caution" },
  warning: { dot: "bg-caution", ink: "text-caution" },
  unavailable: { dot: "bg-ink-4", ink: "text-ink-3" },
};

const STATE_LABEL: Record<HomeSourceState, string> = {
  ok: "OK",
  stale: "Stale",
  warning: "Warning",
  unavailable: "Unavailable",
};

export function SystemHealthMiniPanel({ rows }: Props) {
  return (
    <PanelShell icon="ops" title="System health" subtitle="Pipeline + integrations">
      {rows.length === 0 ? (
        <PanelEmpty message="No system health data." />
      ) : (
        <ul className="space-y-1.5">
          {rows.map((r) => {
            const tone = STATE_TONE[r.state];
            return (
              <li
                key={r.label}
                className="flex items-center justify-between text-[12px]"
              >
                <span className="text-ink-2">{r.label}</span>
                <span className={`inline-flex items-center gap-1.5 ${tone.ink}`}>
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${tone.dot}`}
                    aria-hidden="true"
                  />
                  <span className="text-[11.5px] font-medium">{STATE_LABEL[r.state]}</span>
                  {r.detail && (
                    <span className="text-[10.5px] text-ink-4">· {r.detail}</span>
                  )}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </PanelShell>
  );
}
