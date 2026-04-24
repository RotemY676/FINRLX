"use client";

import { useEffect, useState } from "react";
import {
  fetchCurrentRecommendation,
  fetchDecisionStages,
  RecommendationDetail,
  DecisionStagesData,
} from "@/services/api";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { ConfidenceBlock } from "@/components/recommendation/ConfidenceBlock";
import { WeightsTable } from "@/components/recommendation/WeightsTable";
import { WarningsBlock } from "@/components/recommendation/WarningsBlock";
import { MetadataBlock } from "@/components/recommendation/MetadataBlock";
import { WeightsBarChart } from "@/components/charts/WeightsBarChart";
import { SelectionStage } from "@/components/decision/SelectionStage";
import { AllocationStage } from "@/components/decision/AllocationStage";
import { TimingStage } from "@/components/decision/TimingStage";
import { RiskOverlayStage } from "@/components/decision/RiskOverlayStage";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";

export default function DecisionPage() {
  const [rec, setRec] = useState<RecommendationDetail | null>(null);
  const [stages, setStages] = useState<DecisionStagesData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrentRecommendation()
      .then(async (res) => {
        const detail = res.data;
        setRec(detail);
        if (detail) {
          const stagesRes = await fetchDecisionStages(detail.id);
          setStages(stagesRes.data);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading label="Loading decision workspace..." />;

  if (error) {
    return (
      <PageError
        title="Decision Workspace Error"
        message={error}
        hint="Ensure the backend is running and the database is seeded."
      />
    );
  }

  if (!rec) {
    return (
      <PageEmpty
        title="No Published Recommendation"
        message="The decision workspace requires a published recommendation. Run the seed script to create one."
      />
    );
  }

  return (
    <div className="space-y-qp-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-qp-h1">Decision Workspace</h1>
          <p className="text-qp-small text-qp-text-muted mt-1">
            {rec.weights.length} positions &middot; {rec.status}
          </p>
        </div>
        <StatusBadge status={rec.status} />
      </div>

      {/* Rationale */}
      {rec.rationale_summary && (
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <h3 className="text-qp-h3 mb-qp-2">Rationale</h3>
          <p className="text-qp-body text-qp-text-secondary">{rec.rationale_summary}</p>
        </div>
      )}

      {/* Trust + Warnings row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-qp-6">
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <ConfidenceBlock confidence={rec.confidence} />
        </div>
        {rec.warnings.length > 0 ? (
          <WarningsBlock warnings={rec.warnings} />
        ) : (
          <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4 flex items-center">
            <p className="text-qp-body text-qp-text-muted">No active warnings.</p>
          </div>
        )}
      </div>

      {/* Weights chart + table */}
      <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
        <h3 className="text-qp-h3 mb-qp-4">Portfolio Weights</h3>
        <WeightsBarChart weights={rec.weights} />
      </div>

      <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
        <h3 className="text-qp-h3 mb-qp-3">
          Positions
          <span className="text-qp-small text-qp-text-muted font-normal ml-qp-2">
            Click a row to inspect
          </span>
        </h3>
        <WeightsTable weights={rec.weights} />
      </div>

      {/* Pipeline stages */}
      <div>
        <h2 className="text-qp-h2 mb-qp-4">Decision Pipeline</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-qp-4">
          <SelectionStage data={stages?.selection ?? null} />
          <AllocationStage data={stages?.allocation ?? null} />
          <TimingStage data={stages?.timing ?? null} />
          <RiskOverlayStage data={stages?.risk_overlay ?? null} />
        </div>
      </div>

      {/* Metadata */}
      <MetadataBlock
        status={rec.status}
        publishedAt={rec.published_at}
        validFrom={rec.valid_from}
        validTo={rec.valid_to}
        dataAsOf={rec.data_as_of}
        policyVersionId={rec.policy_version_id}
      />
    </div>
  );
}
