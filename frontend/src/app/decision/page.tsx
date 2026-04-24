"use client";

import { useEffect, useState } from "react";
import {
  fetchCurrentRecommendation, fetchDecisionStages, fetchEvidence, fetchDisagreement,
  RecommendationDetail, DecisionStagesData, EvidenceNarrativeData, DisagreementData,
} from "@/services/api";
import { Icon } from "@/components/icons/Icon";
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

const DELTA_STYLE: Record<string, string> = { pos: "text-pos", neg: "text-breach", neutral: "text-ink-3", flat: "text-ink-4" };

export default function DecisionPage() {
  const [rec, setRec] = useState<RecommendationDetail | null>(null);
  const [stages, setStages] = useState<DecisionStagesData | null>(null);
  const [evidence, setEvidence] = useState<EvidenceNarrativeData | null>(null);
  const [disagreement, setDisagreement] = useState<DisagreementData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrentRecommendation()
      .then(async (res) => {
        setRec(res.data);
        if (res.data) {
          const [s, e, d] = await Promise.all([
            fetchDecisionStages(res.data.id),
            fetchEvidence(),
            fetchDisagreement(),
          ]);
          setStages(s.data);
          setEvidence(e.data);
          setDisagreement(d.data);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading label="Loading decision workspace..." />;
  if (error) return <PageError title="Decision Workspace Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!rec) return <PageEmpty title="No Published Recommendation" message="Run the seed script to create one." />;

  return (
    <div className="space-y-gap max-w-[1200px]">
      {/* ── Hero strip ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <span className="text-[11px] font-mono text-ink-3">{rec.id.slice(0, 16)}…</span>
          <StatusBadge status={rec.status} />
          {rec.data_as_of && <span className="text-[11px] text-ink-4 ml-auto">Data as of {new Date(rec.data_as_of).toLocaleString()}</span>}
        </div>
        {rec.rationale_summary && <p className="text-[14px] text-ink-2 leading-relaxed mb-4">{rec.rationale_summary}</p>}
        <div className="flex items-center gap-6 mb-4 flex-wrap">
          <div><p className="text-[11px] text-ink-4">Positions</p><p className="text-[20px] font-display font-semibold text-ink">{rec.weights.length}</p></div>
          <div><p className="text-[11px] text-ink-4">Horizon</p><p className="text-[20px] font-display font-semibold text-ink">{rec.valid_from && rec.valid_to ? `${Math.round((new Date(rec.valid_to).getTime() - new Date(rec.valid_from).getTime()) / 86400000)}d` : "—"}</p></div>
          {disagreement && (
            <div><p className="text-[11px] text-ink-4">Engine agreement</p><p className="text-[20px] font-display font-semibold text-ink">{disagreement.agreeing}/{disagreement.total_engines}</p></div>
          )}
          {disagreement && (
            <div><p className="text-[11px] text-ink-4">Dispersion</p><p className="text-[20px] font-display font-semibold text-caution">{(disagreement.dispersion * 100).toFixed(0)}%</p></div>
          )}
        </div>
        <ConfidenceBlock confidence={rec.confidence} />
        <div className="flex items-center gap-2 mt-4 pt-4 border-t border-line flex-wrap">
          <button className="px-3 py-1.5 rounded-md bg-primary text-primary-ink text-[12.5px] font-medium flex items-center gap-1.5 hover:opacity-90 transition-colors"><Icon name="check" size={13} /> Save as current thesis</button>
          <button className="px-3 py-1.5 rounded-md bg-surface-3 text-ink-2 text-[12.5px] font-medium flex items-center gap-1.5 hover:bg-line transition-colors"><Icon name="paper" size={13} /> Promote to paper</button>
          <button className="px-3 py-1.5 rounded-md bg-surface-3 text-ink-2 text-[12.5px] font-medium flex items-center gap-1.5 hover:bg-line transition-colors"><Icon name="clock" size={13} /> Defer decision</button>
          <div className="flex-1" />
          <button className="px-2.5 py-1.5 rounded-md text-ink-3 text-[12px] flex items-center gap-1 hover:bg-surface-3 transition-colors"><Icon name="compare" size={12} /> Compare</button>
          <button className="px-2.5 py-1.5 rounded-md text-ink-3 text-[12px] flex items-center gap-1 hover:bg-surface-3 transition-colors"><Icon name="replay" size={12} /> Replay</button>
        </div>
      </section>

      {/* ── Evidence narrative — now from real backend ── */}
      {evidence && evidence.items.length > 0 && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Icon name="sparkle" size={14} className="text-primary" />
            <h3 className="text-[13px] font-semibold text-ink">Evidence narrative</h3>
            {evidence.last_refreshed_min != null && <span className="text-[11px] text-ink-4 ml-auto">Refreshed {evidence.last_refreshed_min}m ago</span>}
          </div>
          <div className="space-y-3">
            {evidence.items.map((item) => (
              <div key={item.order} className="flex items-start gap-3">
                <span className="text-[12px] font-mono text-ink-4 mt-0.5 w-5 shrink-0">{String(item.order).padStart(2, "0")}</span>
                <div className="flex-1">
                  <p className="text-[12.5px] text-ink-2"><b className="text-ink">{item.title}</b> — {item.body}</p>
                  {item.source_engine && <span className="text-[10px] text-ink-4 font-mono mt-0.5 inline-block">{item.source_engine}</span>}
                </div>
                {item.delta_label && (
                  <span className={`text-[12px] font-mono shrink-0 ${DELTA_STYLE[item.delta_direction || "neutral"]}`}>{item.delta_label}</span>
                )}
              </div>
            ))}
          </div>
          {evidence.caveat && (
            <div className="flex items-start gap-2 mt-3 pt-3 border-t border-line text-[12px]">
              <Icon name="alert-triangle" size={13} className="text-caution mt-0.5 shrink-0" />
              <span className="text-ink-3">{evidence.caveat}</span>
            </div>
          )}
        </section>
      )}

      {/* ── Engine disagreement — now from real backend ── */}
      {disagreement && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Icon name="compare" size={14} className="text-accent" />
            <h3 className="text-[13px] font-semibold text-ink">Engine disagreement</h3>
            <span className="text-[11px] text-ink-4 ml-auto">{disagreement.agreeing}/{disagreement.total_engines} agree</span>
          </div>
          <p className="text-[12.5px] text-ink-2 mb-3">{disagreement.summary}</p>
          <div className="flex items-center gap-3">
            {/* Agreement bar */}
            <div className="flex-1 h-2 bg-surface-3 rounded-full overflow-hidden flex">
              <div className="h-full bg-pos rounded-l-full" style={{ width: `${(disagreement.agreeing / disagreement.total_engines) * 100}%` }} />
              <div className="h-full bg-caution" style={{ width: `${(disagreement.dissenting / disagreement.total_engines) * 100}%` }} />
            </div>
            <span className="text-[11px] text-ink-4 shrink-0">dispersion {(disagreement.dispersion * 100).toFixed(0)}%</span>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-3">
            {disagreement.dissenting_engines.map((e) => (
              <span key={e} className="px-2 py-0.5 rounded-md bg-caution-soft text-caution-soft-ink text-[11px] font-medium">{e}</span>
            ))}
          </div>
        </section>
      )}

      {/* ── Warnings ── */}
      {rec.warnings.length > 0 ? <WarningsBlock warnings={rec.warnings} /> : (
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm"><p className="text-[12.5px] text-ink-3">No active warnings.</p></div>
      )}

      {/* ── Portfolio weights ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <h3 className="text-[13px] font-semibold text-ink mb-4">Portfolio Weights</h3>
        <WeightsBarChart weights={rec.weights} />
      </section>

      {/* ── Positions ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <h3 className="text-[13px] font-semibold text-ink">Positions</h3>
          <span className="text-[11px] text-ink-4">Click a row to inspect</span>
        </div>
        <WeightsTable weights={rec.weights} />
      </section>

      {/* ── Risk constraints ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <Icon name="risk" size={14} className="text-caution" />
          <h3 className="text-[13px] font-semibold text-ink">Risk constraints</h3>
        </div>
        {stages?.risk_overlay ? (
          <div className="space-y-3">
            <p className="text-[12.5px] text-ink-2">{stages.risk_overlay.rationale}</p>
            {/* Risk gauge bars */}
            <div className="space-y-2">
              {[
                { name: "Portfolio weight", value: 42, limit: 60, status: "ok" },
                { name: "Sector concentration", value: 81, limit: 75, status: "caution" },
                { name: "Single-name drawdown", value: 35, limit: 60, status: "ok" },
                { name: "Correlation to top 5", value: 68, limit: 65, status: "caution" },
                { name: "Realized vol (30d)", value: 42, limit: 50, status: "ok" },
              ].map((r) => (
                <div key={r.name} className="flex items-center gap-3 text-[12px]">
                  <span className="text-ink-2 w-40 shrink-0">{r.name}</span>
                  <div className="flex-1 h-2 bg-surface-3 rounded-full overflow-hidden relative">
                    <div className={`h-full rounded-full ${r.status === "ok" ? "bg-pos" : "bg-caution"}`} style={{ width: `${r.value}%` }} />
                    <div className="absolute top-0 h-full w-0.5 bg-ink-4" style={{ left: `${r.limit}%` }} title={`Limit: ${r.limit}%`} />
                  </div>
                  <span className={`font-mono w-8 text-right ${r.status === "ok" ? "text-pos" : "text-caution"}`}>{r.value}%</span>
                </div>
              ))}
            </div>
            {stages.risk_overlay.adjustments.length > 0 && (
              <div className="pt-2 border-t border-line space-y-1">
                {stages.risk_overlay.adjustments.map((a, i) => (
                  <div key={i} className="flex items-center gap-2 text-[12.5px]">
                    <Icon name="alert-triangle" size={12} className="text-caution" />
                    <span className="font-mono text-ink">{a.ticker}</span>
                    <span className={`font-mono ${a.delta < 0 ? "text-breach" : "text-pos"}`}>{a.delta > 0 ? "+" : ""}{(a.delta * 100).toFixed(1)}%</span>
                    {a.reason && <span className="text-ink-3">{a.reason}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : <p className="text-[12.5px] text-ink-3">Risk data not available.</p>}
      </section>

      {/* ── Scenario — pending ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <Icon name="filter" size={14} className="text-primary" />
          <h3 className="text-[13px] font-semibold text-ink">Scenario controls</h3>
          <StatusBadge status="pending" />
        </div>
        <p className="text-[12.5px] text-ink-3">Scenario simulation requires backend engine support. UI shell ready.</p>
      </section>

      {/* ── Pipeline stages ── */}
      <div>
        <h2 className="text-[15px] font-semibold text-ink mb-gap">Decision Pipeline</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
          <SelectionStage data={stages?.selection ?? null} />
          <AllocationStage data={stages?.allocation ?? null} />
          <TimingStage data={stages?.timing ?? null} />
          <RiskOverlayStage data={stages?.risk_overlay ?? null} />
        </div>
      </div>

      <MetadataBlock status={rec.status} publishedAt={rec.published_at} validFrom={rec.valid_from} validTo={rec.valid_to} dataAsOf={rec.data_as_of} policyVersionId={rec.policy_version_id} />
    </div>
  );
}
