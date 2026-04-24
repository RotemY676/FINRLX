"use client";

import { ConfidenceTriplet } from "@/services/api";

function ConfRing({ value, color }: { value: number | null; color: string }) {
  const pct = value != null ? Math.round(value * 100) : null;
  const circumference = 2 * Math.PI * 18;
  const offset = pct != null ? circumference * (1 - pct / 100) : circumference;

  return (
    <div className="relative w-12 h-12 shrink-0">
      <svg viewBox="0 0 40 40" className="w-full h-full -rotate-90">
        <circle cx="20" cy="20" r="18" fill="none" stroke="var(--line)" strokeWidth="3" />
        {pct != null && (
          <circle
            cx="20" cy="20" r="18" fill="none"
            stroke={color} strokeWidth="3"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        )}
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[12px] font-mono font-semibold text-ink">
        {pct ?? "—"}
      </span>
    </div>
  );
}

function ringColor(value: number | null): string {
  if (value == null) return "var(--ink-4)";
  if (value >= 0.75) return "var(--pos)";
  if (value >= 0.55) return "var(--caution)";
  return "var(--breach)";
}

export function ConfidenceBlock({ confidence }: { confidence: ConfidenceTriplet }) {
  const items = [
    { label: "Model confidence", value: confidence.model_confidence },
    { label: "Data quality", value: confidence.data_confidence },
    { label: "Operational readiness", value: confidence.operational_confidence },
  ];

  return (
    <div className="flex flex-col gap-3">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <ConfRing value={item.value} color={ringColor(item.value)} />
          <div>
            <div className="text-[12px] text-ink-3">{item.label}</div>
            <div className="text-[13px] text-ink font-medium">
              {item.value != null
                ? `${item.value >= 0.75 ? "High" : item.value >= 0.55 ? "Mixed" : "Low"}`
                : "Unavailable"}
              {item.value != null && (
                <span className="text-ink-4 font-normal ml-1.5">
                  · {(item.value * 100).toFixed(0)}
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
