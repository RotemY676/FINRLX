"use client";

import { useEffect, useState } from "react";
import {
  fetchCurrentRecommendation, fetchDecisionStages, fetchEvidence, fetchDisagreement,
  actionSaveThesis, actionPromotePaper, actionDefer,
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
import { SignInRequired } from "@/components/feedback/SignInRequired";
import { ScenarioCard } from "@/components/decision/ScenarioCard";
import { PriceChartCard } from "@/components/charts/PriceChartCard";
import { HelpLink } from "@/components/help/HelpLink";
import { CopyLLMContextButton } from "@/components/operator/CopyLLMContextButton";
import { buildDecisionContext } from "@/lib/operator/contextBuilder";
import { track } from "@/lib/analytics";
import { useAuth } from "@/contexts/AuthContext";

const DELTA_STYLE: Record<string, string> = { pos: "text-pos", neg: "text-breach", neutral: "text-ink-3", flat: "text-ink-4" };

export default function DecisionPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [rec, setRec] = useState<RecommendationDetail | null>(null);
  const [stages, setStages] = useState<DecisionStagesData | null>(null);
  const [evidence, setEvidence] = useState<EvidenceNarrativeData | null>(null);
  const [disagreement, setDisagreement] = useState<DisagreementData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    fetchCurrentRecommendation()
      .then(async (res) => {
        setRec(res.data);
        if (res.data) {
          void track("first_rec_view", { recommendation_id: res.data.id });
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
  }, [authLoading, user]);

  if (authLoading || loading) return <PageLoading label="Loading decision workspace..." />;
  if (!user) return <SignInRequired feature="the decision workspace" />;
  if (error) return <PageError title="Decision Workspace Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!rec) return <PageEmpty title="No Published Recommendation" message="Run the seed script to create one." />;

  return (
    <div className="space-y-gap max-w-[1200px]">
      {/* ── Hero strip ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <span className="text-[11px] font-mono text-ink-3">{rec.id.slice(0, 16)}…</span>
          <StatusBadge status={rec.status} />
          {rec.data_as_of && <span className="text-[11px] text-ink-4 ml-auto">Data as of {rec.data_as_of.slice(0, 16).replace("T", " ")}</span>}
        </div>
        <div className="mb-3">
          <CopyLLMContextButton bundle={buildDecisionContext({ rec, evidence })} />
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
        {/* Action strip: 3 primary CTAs (handler-wired) + 5 secondary affordances
            (no handlers yet — hidden on mobile to keep the 44pt grid breathable). */}
        <div className="mt-4 pt-4 border-t border-line">
          {/* Mobile: vertical stack so each CTA gets its own row and a 44pt floor.
              Desktop: existing flex-wrap row. */}
          <div className="flex flex-col md:flex-row md:items-center md:flex-wrap gap-2 md:gap-2">
            <button
              type="button"
              disabled={actionLoading}
              onClick={async () => { setActionLoading(true); try { const r = await actionSaveThesis(); setActionMsg(r.data.message); } catch { setActionMsg("Failed"); } finally { setActionLoading(false); }}}
              className="inline-flex items-center justify-center md:justify-start gap-1.5 min-h-11 md:min-h-0 px-4 md:px-3 md:py-1.5 rounded-md bg-primary text-primary-ink text-[13px] md:text-[12.5px] font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            ><Icon name="check" size={14} /> Save as current thesis</button>
            <button
              type="button"
              disabled={actionLoading}
              onClick={async () => { setActionLoading(true); try { const r = await actionPromotePaper(); setActionMsg(r.data.message); } catch { setActionMsg("Failed"); } finally { setActionLoading(false); }}}
              className="inline-flex items-center justify-center md:justify-start gap-1.5 min-h-11 md:min-h-0 px-4 md:px-3 md:py-1.5 rounded-md bg-surface-3 text-ink-2 text-[13px] md:text-[12.5px] font-medium hover:bg-line transition-colors disabled:opacity-50"
            ><Icon name="paper" size={14} /> Promote to paper</button>
            <HelpLink anchor="guides/promote-to-paper" label="How to promote to paper" />
            <button
              type="button"
              disabled={actionLoading}
              onClick={async () => { setActionLoading(true); try { const r = await actionDefer(); setActionMsg(r.data.message); } catch { setActionMsg("Failed"); } finally { setActionLoading(false); }}}
              className="inline-flex items-center justify-center md:justify-start gap-1.5 min-h-11 md:min-h-0 px-4 md:px-3 md:py-1.5 rounded-md bg-surface-3 text-ink-2 text-[13px] md:text-[12.5px] font-medium hover:bg-line transition-colors disabled:opacity-50"
            ><Icon name="clock" size={14} /> Defer decision</button>
            <HelpLink anchor="guides/defer-or-save-a-thesis" label="What does defer do?" />
            <div className="hidden md:block md:flex-1" />
            {actionMsg && (
              <span className="text-[11px] text-pos font-medium md:animate-pulse" role="status" aria-live="polite">{actionMsg}</span>
            )}
            {/* Phase 7: dead Bookmark / Share / More buttons removed.
                Compare / Replay become real <a> links because those
                routes exist. No phantom affordances. */}
            <a
              href="/pro/comparison"
              className="hidden md:inline-flex items-center justify-center gap-1 h-9 px-2.5 rounded-md text-ink-3 text-caption hover:bg-surface-3 transition-colors"
            >
              <Icon name="compare" size={12} /> Compare
            </a>
            <a
              href="/pro/replay"
              className="hidden md:inline-flex items-center justify-center gap-1 h-9 px-2.5 rounded-md text-ink-3 text-caption hover:bg-surface-3 transition-colors"
            >
              <Icon name="replay" size={12} /> Replay
            </a>
          </div>
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

      {/* ── Price chart with event markers ── */}
      <PriceChartCard ticker={rec.weights[0]?.ticker || "NVDA"} />

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
          <h3 className="text-card-title text-ink">Risk constraints</h3>
        </div>
        {stages?.risk_overlay ? (
          <div className="space-y-3">
            {stages.risk_overlay.rationale && (
              <p className="text-caption text-ink-2">{stages.risk_overlay.rationale}</p>
            )}
            {/* Phase 7: hardcoded gauge values removed. Backend's
                `RiskOverlayView` carries `portfolio_risk_score`,
                `constraints_applied`, and `adjustments` — show those
                instead of inventing numbers. If a future phase adds
                per-constraint utilisation to the backend, the gauges
                can come back. */}
            <div className="flex flex-wrap items-center gap-4 pt-1">
              {stages.risk_overlay.portfolio_risk_score != null && (
                <div>
                  <p className="text-meta text-ink-4">Portfolio risk score</p>
                  <p className="text-section-title font-display text-ink font-mono">
                    {stages.risk_overlay.portfolio_risk_score.toFixed(2)}
                  </p>
                </div>
              )}
              {stages.risk_overlay.constraints_applied.length > 0 && (
                <div className="flex-1 min-w-[200px]">
                  <p className="text-meta text-ink-4 mb-1">Constraints applied</p>
                  <div className="flex flex-wrap gap-1.5">
                    {stages.risk_overlay.constraints_applied.map((c) => (
                      <span
                        key={c}
                        className="text-meta font-mono bg-surface-3 text-ink-2 px-1.5 py-0.5 rounded-sm"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {stages.risk_overlay.adjustments.length > 0 && (
              <div className="pt-2 border-t border-line space-y-1">
                <p className="text-meta text-ink-4 uppercase tracking-wider">Per-position adjustments</p>
                {stages.risk_overlay.adjustments.map((a, i) => (
                  <div key={i} className="flex items-center gap-2 text-caption">
                    <Icon name="alert-triangle" size={12} className="text-caution" />
                    <span className="font-mono text-ink">{a.ticker}</span>
                    <span className={`font-mono ${a.delta < 0 ? "text-breach" : "text-pos"}`}>{a.delta > 0 ? "+" : ""}{(a.delta * 100).toFixed(1)}%</span>
                    {a.reason && <span className="text-ink-3">{a.reason}</span>}
                  </div>
                ))}
              </div>
            )}
            {stages.risk_overlay.portfolio_risk_score == null &&
              stages.risk_overlay.constraints_applied.length === 0 &&
              stages.risk_overlay.adjustments.length === 0 && (
                <p className="text-caption text-ink-3">
                  Risk overlay ran but reported no constraints, score, or
                  adjustments for this recommendation.
                </p>
              )}
          </div>
        ) : (
          <p className="text-caption text-ink-3">Risk data not available for this recommendation.</p>
        )}
      </section>

      {/* ── Scenario controls — interactive ── */}
      <ScenarioCard />

      {/* ── Pipeline stages ── */}
      <div>
        <h2 className="text-section-title text-ink mb-gap">Decision Pipeline</h2>
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
