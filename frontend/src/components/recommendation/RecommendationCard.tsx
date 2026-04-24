import { RecommendationSummary } from "@/services/api";
import { ConfidenceBlock } from "./ConfidenceBlock";
import { StatusBadge } from "./StatusBadge";

export function RecommendationCard({
  rec,
}: {
  rec: RecommendationSummary;
}) {
  return (
    <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-6">
      <div className="flex items-start justify-between mb-qp-4">
        <div>
          <h2 className="text-qp-h2">Current Recommendation</h2>
          <p className="text-qp-small text-qp-text-muted mt-1">
            {rec.total_positions} positions
            {rec.published_at &&
              ` \u00B7 published ${new Date(rec.published_at).toLocaleString()}`}
          </p>
        </div>
        <StatusBadge status={rec.status} />
      </div>

      {rec.rationale_summary && (
        <p className="text-qp-body text-qp-text-secondary mb-qp-4">
          {rec.rationale_summary}
        </p>
      )}

      <ConfidenceBlock confidence={rec.confidence} />

      {rec.warning_count > 0 && (
        <div className="mt-qp-4 p-qp-3 bg-qp-amber-400/10 border border-qp-amber-400 rounded-qp-sm">
          <p className="text-qp-small text-qp-amber-600">
            {rec.warning_count} warning{rec.warning_count > 1 ? "s" : ""} active
          </p>
        </div>
      )}
    </div>
  );
}
