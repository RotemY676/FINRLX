"use client";

import { useEffect, useState } from "react";
import {
  fetchReplayList, fetchReplay,
  ReplayListData, ReplayDetail,
} from "@/services/api";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { ConfidenceBlock } from "@/components/recommendation/ConfidenceBlock";
import { WeightsTable } from "@/components/recommendation/WeightsTable";
import { fmtDateTime, fmtDate, fmtTime } from "@/lib/format";
import { WarningsBlock } from "@/components/recommendation/WarningsBlock";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";
import { HelpLink } from "@/components/help/HelpLink";
import { CopyLLMContextButton } from "@/components/operator/CopyLLMContextButton";
import { AnalystNotesPanel } from "@/components/operator/AnalystNotesPanel";
import { buildReplayContext } from "@/lib/operator/contextBuilder";
import { track } from "@/lib/analytics";
import { useAuth } from "@/contexts/AuthContext";

function StageSnapshotCard({ stage, data, capturedAt }: {
  stage: string;
  data: Record<string, unknown>;
  capturedAt: string;
}) {
  return (
    <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-[13px] font-semibold text-ink capitalize">{stage.replace(/_/g, " ")}</h4>
        <span className="text-[11px] text-ink-4">
          {fmtTime(capturedAt)}
        </span>
      </div>
      {/* Mobile: key stacked above value so the value gets full row width
          (the old w-32 label ate 34% of a 375px viewport and truncated values).
          Desktop (md+): key | value side-by-side as before. */}
      <dl className="space-y-2 md:space-y-1 text-[11px]">
        {Object.entries(data).map(([key, val]) => {
          const display = typeof val === "object" ? JSON.stringify(val).slice(0, 80) + (JSON.stringify(val).length > 80 ? "..." : "") : String(val);
          return (
            <div key={key} className="flex flex-col md:flex-row md:gap-2">
              <dt className="text-ink-4 md:w-32 md:shrink-0 font-mono">{key}</dt>
              <dd className="text-ink-2 break-words md:truncate md:flex-1">{display}</dd>
            </div>
          );
        })}
      </dl>
    </div>
  );
}

export default function ReplayPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [list, setList] = useState<ReplayListData | null>(null);
  const [detail, setDetail] = useState<ReplayDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Phase 19A.3: skip the authenticated fetch for unauthenticated visitors.
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    void track("replay_open");
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
  }, [authLoading, user]);

  if (authLoading || loading) return <PageLoading label="Loading replay..." />;
  if (!user) return <PageEmpty title="Sign in required" message="Sign in to view replay data." />;
  if (error) return <PageError title="Replay Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!list || list.total === 0) return <PageEmpty title="No Replay Data" message="No replay snapshots available. Run the seed script to create demo replay data." />;

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div>
        <h1 className="text-[20px] font-semibold text-ink flex items-center gap-2">Replay / Forensics <HelpLink anchor="reference/pages/replay" label="Open Replay help" /></h1>
        <p className="text-[11px] text-ink-4 mt-1">
          {list.total} recommendation replay{list.total !== 1 ? "s" : ""} available
        </p>
      </div>

      {/* Replay selector */}
      <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
        <h3 className="text-[13px] font-semibold text-ink mb-3">Available Replays</h3>
        <ul className="space-y-1" role="list">
          {list.items.map((item) => {
            const isSelected = detail?.recommendation_id === item.recommendation_id;
            const onSelect = async () => {
              const res = await fetchReplay(item.recommendation_id);
              setDetail(res.data);
            };
            return (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={onSelect}
                  aria-pressed={isSelected}
                  aria-label={`Replay ${item.recommendation_id.slice(0, 8)}, captured ${fmtDate(item.captured_at)}, ${item.total_positions} positions`}
                  className={`w-full flex flex-col md:flex-row md:items-center md:justify-between gap-1 md:gap-2 p-3 min-h-11 rounded-lg text-left transition-colors ${
                    isSelected
                      ? "bg-primary-soft border border-primary"
                      : "hover:bg-surface-3 focus-visible:bg-surface-3"
                  }`}
                >
                  <div className="flex flex-wrap items-baseline gap-x-2">
                    <span className="text-[13px] font-mono text-ink">{item.recommendation_id.slice(0, 8)}…</span>
                    <span className="text-[11px] text-ink-4">{item.total_positions} positions</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <StatusBadge status={item.status} />
                    <span className="text-[11px] text-ink-4">{fmtDate(item.captured_at)}</span>
                  </div>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {detail && (
        <>
          {/* Seeded data warning */}
          {detail.warnings.some(w => w.toLowerCase().includes("seeded") || w.toLowerCase().includes("demo")) && (
            <div className="rounded-lg border border-caution bg-caution-soft p-3 text-[12.5px] text-caution-soft-ink">
              This replay is from seeded/demo data and may not reflect real pipeline decisions.
            </div>
          )}

          {/* Replay header */}
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-[15px] font-semibold text-ink">Replay Detail</h2>
              <p className="text-[11px] text-ink-4 mt-1">
                Captured {fmtDateTime(detail.captured_at)}
                {detail.data_as_of && ` · data as of ${fmtDateTime(detail.data_as_of)}`}
              </p>
            </div>
            <StatusBadge status={detail.status} />
          </div>

          <div>
            <CopyLLMContextButton bundle={buildReplayContext({ replay: detail })} />
          </div>

          {/* Rationale */}
          {detail.rationale_summary && (
            <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
              <h3 className="text-[13px] font-semibold text-ink mb-3">Rationale at Snapshot</h3>
              <p className="text-[13px] text-ink-2">{detail.rationale_summary}</p>
            </div>
          )}

          {/* Trust + Warnings */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
            <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
              <ConfidenceBlock confidence={detail.confidence} />
            </div>
            {detail.warnings.length > 0 ? (
              <WarningsBlock warnings={detail.warnings} />
            ) : (
              <div className="bg-surface border border-line rounded-lg shadow-sm p-pad flex items-center">
                <p className="text-[13px] text-ink-4">No warnings at this snapshot.</p>
              </div>
            )}
          </div>

          {/* Positions */}
          <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
            <h3 className="text-[13px] font-semibold text-ink mb-3">
              Positions at Snapshot
              <span className="text-[11px] text-ink-4 font-normal ml-2">
                Click a row to inspect
              </span>
            </h3>
            <WeightsTable weights={detail.weights} />
          </div>

          {/* Stage snapshots */}
          <div>
            <h2 className="text-[15px] font-semibold text-ink mb-4">Pipeline Stage Snapshots</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
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

          {/* Phase O-4 — archived LLM analyses linked to this recommendation.
              Renders nothing when the operator_console flag is off or when
              no notes have been pasted back yet. */}
          <AnalystNotesPanel recommendationId={detail.recommendation_id} />
        </>
      )}
    </div>
  );
}
