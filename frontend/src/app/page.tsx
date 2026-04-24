"use client";

import { useEffect, useState } from "react";
import { fetchOverview, OverviewData } from "@/services/api";
import { RecommendationCard } from "@/components/recommendation/RecommendationCard";
import { HealthPanel } from "@/components/overview/HealthPanel";

export default function OverviewPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview()
      .then((res) => {
        setData(res.data);
        setError(null);
      })
      .catch((err) => {
        setError(err.message || "Failed to load overview");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-qp-body text-qp-text-muted">Loading overview...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-qp-6 bg-qp-red-400/10 border border-qp-red-400 rounded-qp">
        <h2 className="text-qp-h2 text-qp-red-600 mb-qp-2">Connection Error</h2>
        <p className="text-qp-body text-qp-text-secondary">{error}</p>
        <p className="text-qp-small text-qp-text-muted mt-qp-2">
          Ensure the backend is running at localhost:8000
        </p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      <h1 className="text-qp-h1 mb-qp-6">Overview</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-qp-6">
        <div className="lg:col-span-2">
          {data.current_recommendation ? (
            <RecommendationCard rec={data.current_recommendation} />
          ) : (
            <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-6">
              <h2 className="text-qp-h2 text-qp-text-secondary">
                No Published Recommendation
              </h2>
              <p className="text-qp-body text-qp-text-muted mt-qp-2">
                No recommendation has been published yet. Run the seed script or
                wait for the pipeline to produce a recommendation.
              </p>
            </div>
          )}
        </div>

        <div className="space-y-qp-6">
          <HealthPanel health={data.health} />

          <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-6">
            <h3 className="text-qp-h3 mb-qp-2">Activity</h3>
            <p className="text-qp-body text-qp-text-secondary">
              {data.recent_recommendation_count} published recommendation
              {data.recent_recommendation_count !== 1 ? "s" : ""}
            </p>
            {data.last_published_at && (
              <p className="text-qp-small text-qp-text-muted mt-1">
                Last: {new Date(data.last_published_at).toLocaleString()}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
