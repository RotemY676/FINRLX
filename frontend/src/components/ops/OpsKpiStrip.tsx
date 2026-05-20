import { OpsSystemKpi } from "@/services/api";

const TONE_TEXT: Record<string, string> = {
  pos: "text-pos",
  caution: "text-caution",
  breach: "text-breach",
  neutral: "text-ink",
};

export function OpsKpiStrip({ kpis }: { kpis: OpsSystemKpi[] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-gap">
      {kpis.map((k) => (
        <div key={k.key} className="rounded-lg border border-line bg-surface p-3 shadow-sm">
          <p className="text-[11px] text-ink-4">{k.key}</p>
          <p className={`text-[20px] font-display font-semibold mt-0.5 ${TONE_TEXT[k.tone] ?? TONE_TEXT.neutral}`}>
            {k.value}
          </p>
          {k.sub && <p className="text-[11px] text-ink-4 mt-0.5">{k.sub}</p>}
        </div>
      ))}
    </div>
  );
}
