import type { DiataxisKind } from "@/lib/help/types";

const META: Record<DiataxisKind, { label: string; tone: string; hint: string }> = {
  tutorial:    { label: "Tutorial",    tone: "bg-primary-soft text-primary-soft-ink",  hint: "Learn by doing — a concrete walk-through." },
  "how-to":    { label: "How-to",      tone: "bg-pos-soft text-pos-soft-ink",          hint: "A recipe for a specific task." },
  reference:   { label: "Reference",   tone: "bg-surface-3 text-ink-2",                hint: "Facts and structure, lookup-oriented." },
  explanation: { label: "Explanation", tone: "bg-accent/10 text-accent",               hint: "Background and rationale — the 'why'." },
};

export function DiataxisBadge({ kind }: { kind?: DiataxisKind }) {
  if (!kind) return null;
  const m = META[kind];
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium uppercase tracking-wider ${m.tone}`}
      title={m.hint}
    >
      {m.label}
    </span>
  );
}
