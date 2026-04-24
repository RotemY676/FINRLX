import { ReactNode } from "react";

export function StageCard({ title, subtitle, available, children }: {
  title: string; subtitle?: string; available: boolean; children: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-line bg-surface p-pad">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-[13px] font-semibold text-ink">{title}</h3>
          {subtitle && <p className="text-[11px] text-ink-4">{subtitle}</p>}
        </div>
        <span className={`w-2 h-2 rounded-full ${available ? "bg-pos" : "bg-line-strong"}`} />
      </div>
      {available ? children : <p className="text-[12.5px] text-ink-3">Stage data not available.</p>}
    </div>
  );
}
