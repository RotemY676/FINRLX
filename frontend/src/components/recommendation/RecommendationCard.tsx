import { RecommendationSummary } from "@/services/api";
import { ConfidenceBlock } from "./ConfidenceBlock";
import { StatusBadge } from "./StatusBadge";

export function RecommendationCard({ rec }: { rec: RecommendationSummary }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h2 className="text-[15px] font-semibold text-ink">Current Recommendation</h2>
          <p className="text-[12px] text-ink-3 mt-0.5">
            {rec.total_positions} positions
            {rec.published_at && ` · published ${new Date(rec.published_at).toLocaleString()}`}
          </p>
        </div>
        <StatusBadge status={rec.status} />
      </div>

      {rec.rationale_summary && (
        <p className="text-[13px] text-ink-2 mb-4 leading-relaxed">{rec.rationale_summary}</p>
      )}

      <ConfidenceBlock confidence={rec.confidence} />

      {rec.warning_count > 0 && (
        <div className="mt-4 px-3 py-2 rounded-md bg-caution-soft border border-caution/20">
          <p className="text-[12px] text-caution-soft-ink font-medium">
            {rec.warning_count} warning{rec.warning_count > 1 ? "s" : ""} active
          </p>
        </div>
      )}
    </div>
  );
}
