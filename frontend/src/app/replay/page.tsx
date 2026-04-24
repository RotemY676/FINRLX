"use client";

import { useEffect, useState } from "react";
import {
  fetchReplayList, fetchReplay,
  ReplayListData, ReplayDetail,
} from "@/services/api";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { ConfidenceBlock } from "@/components/recommendation/ConfidenceBlock";
import { WeightsTable } from "@/components/recommendation/WeightsTable";
import { WarningsBlock } from "@/components/recommendation/WarningsBlock";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";

function StageSnapshotCard({ stage, data, capturedAt }: {
  stage: string;
  data: Record<string, unknown>;
  capturedAt: string;
}) {
  return (
    <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
      <div className="flex items-center justify-between mb-qp-2">
        <h4 className="text-qp-h3 capitalize">{stage.replace(/_/g, " ")}</h4>
        <span className="text-qp-small text-qp-text-muted">
          {new Date(capturedAt).toLocaleTimeString()}
        </span>
      </div>
      <div className="space-y-qp-1 text-qp-small">
        {Object.entries(data).map(([key, val]) => {
          const display = typeof val === "object" ? JSON.stringify(val).slice(0, 80) + (JSON.stringify(val).length > 80 ? "..." : "") : String(val);
          return (
            <div key={key} className="flex gap-qp-2">
              <span className="text-qp-text-muted w-32 shrink-0 font-mono">{key}</span>
              <span className="text-qp-text-secondary truncate">{display}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ReplayPage() {
  const [list, setList] = useState<ReplayListData | null>(null);
  const [detail, setDetail] = useState<ReplayDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReplayList()
      .then(async (res) => {
        setList(res.data);
        if (res.data.items.length > 0) {
          const first = res.data.items[0];
          const detailRes = await fetchReplay(first.recommendation_id);
          setDetail(detailRes.data);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading label="Loading replay..." />;
  if (error) return <PageError title="Replay Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!list || list.total === 0) return <PageEmpty title="No Replay Data" message="No replay snapshots available. Run the seed script to create demo replay data." />;

  return (
    <div className="space-y-qp-6">
      <div>
        <h1 className="text-qp-h1">Replay / Forensics</h1>
        <p className="text-qp-small text-qp-text-muted mt-1">
          {list.total} recommendation replay{list.total !== 1 ? "s" : ""} available
        </p>
      </div>

      {/* Replay selector */}
      <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
        <h3 className="text-qp-h3 mb-qp-3">Available Replays</h3>
        {list.items.map((item) => (
          <div
            key={item.id}
            className={`flex items-center justify-between p-qp-3 rounded-qp cursor-pointer transition-colors duration-qp ${
              detail?.recommendation_id === item.recommendation_id
                ? "bg-qp-blue-50 border border-qp-blue-200"
                : "hover:bg-qp-bg-hover"
            }`}
            onClick={async () => {
              const res = await fetchReplay(item.recommendation_id);
              setDetail(res.data);
            }}
          >
            <div>
              <span className="text-qp-body font-mono">{item.recommendation_id.slice(0, 8)}...</span>
              <span className="text-qp-small text-qp-text-muted ml-qp-2">
                {item.total_positions} positions
              </span>
            </div>
            <div className="flex items-center gap-qp-2">
              <StatusBadge status={item.status} />
              <span className="text-qp-small text-qp-text-muted">
                {new Date(item.captured_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        ))}
      </div>

      {detail && (
        <>
          {/* Replay header */}
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-qp-h2">Replay Detail</h2>
              <p className="text-qp-small text-qp-text-muted mt-1">
                Captured {new Date(detail.captured_at).toLocaleString()}
                {detail.data_as_of && ` · data as of ${new Date(detail.data_as_of).toLocaleString()}`}
              </p>
            </div>
            <StatusBadge status={detail.status} />
          </div>

          {/* Rationale */}
          {detail.rationale_summary && (
            <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
              <h3 className="text-qp-h3 mb-qp-2">Rationale at Snapshot</h3>
              <p className="text-qp-body text-qp-text-secondary">{detail.rationale_summary}</p>
            </div>
          )}

          {/* Trust + Warnings */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-qp-6">
            <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
              <ConfidenceBlock confidence={detail.confidence} />
            </div>
            {detail.warnings.length > 0 ? (
              <WarningsBlock warnings={detail.warnings} />
            ) : (
              <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4 flex items-center">
                <p className="text-qp-body text-qp-text-muted">No warnings at this snapshot.</p>
              </div>
            )}
          </div>

          {/* Positions */}
          <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
            <h3 className="text-qp-h3 mb-qp-3">
              Positions at Snapshot
              <span className="text-qp-small text-qp-text-muted font-normal ml-qp-2">
                Click a row to inspect
              </span>
            </h3>
            <WeightsTable weights={detail.weights} />
          </div>

          {/* Stage snapshots */}
          <div>
            <h2 className="text-qp-h2 mb-qp-4">Pipeline Stage Snapshots</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-qp-4">
              {detail.stages.map((s) => (
                <StageSnapshotCard
                  key={s.stage}
                  stage={s.stage}
                  data={s.snapshot_data}
                  capturedAt={s.captured_at}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
