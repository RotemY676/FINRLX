const COLORS: Record<string, string> = {
  published: "bg-qp-green-500 text-white",
  published_with_warning: "bg-qp-amber-500 text-white",
  draft: "bg-qp-border text-qp-text-secondary",
  staged: "bg-qp-blue-100 text-qp-blue-700",
  suppressed: "bg-qp-red-500 text-white",
  stale: "bg-qp-amber-400 text-qp-text-primary",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-block px-qp-2 py-0.5 rounded-qp-sm text-qp-small font-medium ${
        COLORS[status] || "bg-qp-border text-qp-text-secondary"
      }`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
