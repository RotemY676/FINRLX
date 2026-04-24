const STYLES: Record<string, string> = {
  fresh: "bg-pos-soft text-pos-soft-ink",
  published: "bg-pos-soft text-pos-soft-ink",
  provisional: "bg-caution-soft text-caution-soft-ink",
  published_with_warning: "bg-caution-soft text-caution-soft-ink",
  pending: "bg-primary-soft text-primary-soft-ink",
  staged: "bg-primary-soft text-primary-soft-ink",
  suppressed: "bg-breach-soft text-breach-soft-ink",
  stale: "bg-surface-3 text-ink-3",
  draft: "bg-surface-3 text-ink-3",
  completed: "bg-pos-soft text-pos-soft-ink",
  failed: "bg-breach-soft text-breach-soft-ink",
  running: "bg-primary-soft text-primary-soft-ink",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium ${
      STYLES[status] || "bg-surface-3 text-ink-3"
    }`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
