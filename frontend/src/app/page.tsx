"use client";

import { useEffect, useState } from "react";
import { fetchOverview, fetchRegime, fetchActivity, OverviewData, RegimeData, ActivityFeedData } from "@/services/api";
import { Icon } from "@/components/icons/Icon";
import { RecommendationCard } from "@/components/recommendation/RecommendationCard";
import { HealthPanel } from "@/components/overview/HealthPanel";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";

const KIND_ICON: Record<string, string> = {
  publish: "check", breach: "risk", engine: "compare", note: "paper",
  defer: "clock", incident: "info", backtest: "backtest",
};
const KIND_STYLE: Record<string, string> = {
  publish: "bg-pos-soft text-pos-soft-ink",
  breach: "bg-breach-soft text-breach-soft-ink",
  engine: "bg-primary-soft text-primary-soft-ink",
  note: "bg-surface-3 text-ink-2",
  defer: "bg-caution-soft text-caution-soft-ink",
  incident: "bg-breach-soft text-breach-soft-ink",
  backtest: "bg-primary-soft text-primary-soft-ink",
};

export default function OverviewPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [regime, setRegime] = useState<RegimeData | null>(null);
  const [activity, setActivity] = useState<ActivityFeedData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchOverview(), fetchRegime(), fetchActivity()])
      .then(([ov, rg, act]) => {
        setData(ov.data);
        setRegime(rg.data);
        setActivity(act.data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading label="Loading overview..." />;
  if (error) return <PageError title="Connection Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!data) return null;

  const rec = data.current_recommendation;

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div>
        <h1 className="text-[20px] font-semibold text-ink">Overview</h1>
        <p className="text-[12px] text-ink-3 mt-0.5">Morning triage · portfolio health · activity</p>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-gap">
        {[
          { k: "Positions", v: rec ? String(rec.total_positions) : "—", sub: "active", tone: "" },
          { k: "Publishable", v: rec ? "1" : "0", sub: "requires review", tone: "primary" },
          { k: "Warnings", v: rec ? String(rec.warning_count) : "0", sub: rec?.warning_count ? "active" : "none", tone: rec?.warning_count ? "caution" : "" },
          { k: "Freshness", v: "94%", sub: "engines current", tone: "pos" },
          { k: "Coverage", v: "96%", sub: "universe covered", tone: "pos" },
          { k: "Recommendations", v: String(data.recent_recommendation_count), sub: "published", tone: "" },
        ].map((kpi, i) => (
          <div key={i} className="rounded-lg border border-line bg-surface p-3 shadow-sm">
            <p className="text-[11px] text-ink-4">{kpi.k}</p>
            <p className={`text-[20px] font-display font-semibold mt-0.5 ${
              kpi.tone === "primary" ? "text-primary" : kpi.tone === "caution" ? "text-caution" :
              kpi.tone === "pos" ? "text-pos" : "text-ink"
            }`}>{kpi.v}</p>
            <p className="text-[11px] text-ink-4 mt-0.5">{kpi.sub}</p>
          </div>
        ))}
      </div>

      {/* Recommendation + Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-gap">
        <div className="lg:col-span-2">
          {rec ? <RecommendationCard rec={rec} /> : (
            <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
              <h2 className="text-[15px] font-semibold text-ink-2">No Published Recommendation</h2>
              <p className="text-[13px] text-ink-3 mt-1">Run the seed script to create one.</p>
            </div>
          )}
        </div>
        <div className="space-y-gap">
          <HealthPanel health={data.health} />
          <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
            <h3 className="text-[13px] font-semibold text-ink mb-2">Activity</h3>
            <p className="text-[12.5px] text-ink-2">{data.recent_recommendation_count} published</p>
            {data.last_published_at && (
              <p className="text-[11px] text-ink-4 mt-1">Last: {new Date(data.last_published_at).toLocaleString()}</p>
            )}
          </div>
        </div>
      </div>

      {/* Regime strip — now from real backend data */}
      {regime && (
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Icon name="trend-up" size={14} className="text-primary" />
            <h3 className="text-[13px] font-semibold text-ink">Regime & signal posture</h3>
            <span className="text-[11px] text-ink-4 ml-auto">confidence {regime.regime_confidence.toFixed(2)} · persistence {regime.persistence_days}d</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-gap">
            <div>
              <p className="text-[11px] text-ink-4 mb-1">Current regime</p>
              <p className="text-[15px] font-semibold text-ink">{regime.regime_label}</p>
              <p className="text-[11px] text-ink-4 mt-1">Last switch {regime.last_switch_date}</p>
              <div className="flex items-center gap-2 mt-2">
                <div className="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                  <div className="h-full bg-pos rounded-full" style={{ width: `${regime.regime_confidence * 100}%` }} />
                </div>
                <span className="text-[11px] text-ink-4">
                  {regime.alternatives.map(a => `${a.label} ${(a.prob * 100).toFixed(0)}%`).join(" · ")}
                </span>
              </div>
            </div>
            <div>
              <p className="text-[11px] text-ink-4 mb-1">Signal posture</p>
              <div className="space-y-1">
                {regime.signal_posture.map((sp) => (
                  <div key={sp.factor} className="flex items-center gap-2 text-[12px]">
                    <span className={`w-1.5 h-1.5 rounded-full ${sp.sigma > 0 ? "bg-pos" : sp.sigma < 0 ? "bg-breach" : "bg-ink-4"}`} />
                    <span className="text-ink-2">{sp.factor} {sp.direction}</span>
                    <span className={`font-mono ml-auto ${sp.sigma > 0 ? "text-pos" : sp.sigma < 0 ? "text-breach" : "text-ink-3"}`}>
                      {sp.sigma > 0 ? "+" : ""}{sp.sigma.toFixed(1)}σ
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[11px] text-ink-4 mb-1">Sector tilt</p>
              <div className="space-y-1">
                {regime.sector_tilts.map((st) => (
                  <div key={st.sector} className="flex items-center gap-2 text-[12px]">
                    <span className="text-ink-2 w-16">{st.sector}</span>
                    <span className={`font-mono ml-auto ${st.tilt_pct >= 0 ? "text-pos" : "text-breach"}`}>
                      {st.tilt_pct >= 0 ? "+" : ""}{st.tilt_pct.toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Activity feed — now from real backend data */}
      {activity && activity.events.length > 0 && (
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Icon name="news" size={14} className="text-primary" />
            <h3 className="text-[13px] font-semibold text-ink">Activity</h3>
            <span className="text-[11px] text-ink-4 ml-auto">{activity.total} events</span>
          </div>
          <div className="space-y-1.5">
            {activity.events.map((ev, i) => (
              <div key={i} className="flex items-start gap-3 py-1.5">
                <div className={`w-6 h-6 rounded-md flex items-center justify-center shrink-0 ${KIND_STYLE[ev.kind] || "bg-surface-3 text-ink-3"}`}>
                  <Icon name={KIND_ICON[ev.kind] || "info"} size={12} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[12.5px] text-ink-2">
                    <b className="text-ink">{ev.actor}</b> {ev.description}
                    <span className="text-ink-4 ml-1.5">· {ev.when_ago}</span>
                  </p>
                  {ev.detail && <p className="text-[11px] text-ink-3 mt-0.5">{ev.detail}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
