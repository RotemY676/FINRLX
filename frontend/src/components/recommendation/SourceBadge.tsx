const STYLES: Record<string, string> = {
  pipeline_backtest: "bg-pos-soft text-pos-soft-ink",
  pipeline: "bg-pos-soft text-pos-soft-ink",
  recommendation_paper: "bg-pos-soft text-pos-soft-ink",
  real: "bg-pos-soft text-pos-soft-ink",
  seed_demo: "bg-caution-soft text-caution-soft-ink",
  test_paper: "bg-caution-soft text-caution-soft-ink",
  unknown: "bg-surface-3 text-ink-3",
  shadow: "bg-caution-soft text-caution-soft-ink",
  experimental: "bg-caution-soft text-caution-soft-ink",
  needs_more_data: "bg-surface-3 text-ink-3",
  eligible_for_review: "bg-primary-soft text-primary-soft-ink",
  promising_shadow: "bg-caution-soft text-caution-soft-ink",
};

const LABELS: Record<string, string> = {
  pipeline_backtest: "Pipeline",
  recommendation_paper: "From recommendation",
  seed_demo: "Seed / Demo",
  test_paper: "Test paper",
  unknown: "Unverified",
  shadow: "Shadow",
  experimental: "Experimental",
  needs_more_data: "Needs more data",
  eligible_for_review: "Eligible for review",
  promising_shadow: "Promising shadow",
};

export function SourceBadge({ source, label }: { source: string; label?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium ${
      STYLES[source] || "bg-surface-3 text-ink-3"
    }`}>
      {label || LABELS[source] || source.replace(/_/g, " ")}
    </span>
  );
}
