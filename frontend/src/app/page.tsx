"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon } from "@/components/icons/Icon";
import { HealthPanel } from "@/components/overview/HealthPanel";
import { RecommendationCard } from "@/components/recommendation/RecommendationCard";
import { PageError } from "@/components/feedback/PageError";
import { PageLoading } from "@/components/feedback/PageLoading";
import { useAuth } from "@/contexts/AuthContext";
import {
  ActivityFeedData,
  OverviewData,
  RegimeData,
  fetchActivity,
  fetchOverview,
  fetchRegime,
} from "@/services/api";

const KIND_ICON: Record<string, string> = {
  publish: "check",
  breach: "risk",
  engine: "compare",
  note: "paper",
  defer: "clock",
  incident: "info",
  backtest: "backtest",
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

const NEXT_ACTIONS = [
  {
    href: "/profile",
    icon: "user",
    title: "Review your profile",
    body: "Edit your risk tolerance, sector preferences, and currency.",
  },
  {
    href: "/templates",
    icon: "layers",
    title: "Try a template",
    body: "Apply a pre-made allocation (Conservative → Aggressive) in one click.",
  },
  {
    href: "/paper",
    icon: "paper",
    title: "See your paper portfolio",
    body: "Recommendations are tracked here in your base currency.",
  },
];

function firstNameFromEmail(email: string | undefined): string {
  if (!email) return "there";
  const local = email.split("@")[0] || "there";
  const first = local.split(/[._-]/)[0] || "there";
  return first.charAt(0).toUpperCase() + first.slice(1);
}

export default function OverviewPage() {
  const { user } = useAuth();
  const [data, setData] = useState<OverviewData | null>(null);
  const [regime, setRegime] = useState<RegimeData | null>(null);
  const [activity, setActivity] = useState<ActivityFeedData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiWarnings, setApiWarnings] = useState<string[]>([]);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    Promise.all([fetchOverview(), fetchRegime(), fetchActivity()])
      .then(([ov, rg, act]) => {
        setData(ov.data);
        setRegime(rg.data);
        setActivity(act.data);
        setApiWarnings(ov.meta?.warnings || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading label="Loading…" />;
  if (error)
    return (
      <PageError
        title="Connection Error"
        message={error}
        hint="Ensure the backend is running and seeded."
      />
    );
  if (!data) return null;

  const rec = data.current_recommendation;
  const firstName = firstNameFromEmail(user?.email);

  return (
    <div className="space-y-gap max-w-[1100px]">
      {/* Greeting */}
      <div>
        <h1 className="text-[22px] font-semibold text-ink">Hi, {firstName}.</h1>
        <p className="text-[13px] text-ink-3 mt-1">
          {rec
            ? "Your latest recommendation is ready below. Three next actions follow."
            : "No recommendation is published yet. Here's how to set up your first one."}
        </p>
      </div>

      {/* Pipeline warnings banner */}
      {apiWarnings.length > 0 && (
        <div className="rounded-lg border border-caution bg-caution-soft p-3">
          {apiWarnings.map((w, i) => (
            <p
              key={i}
              className="text-[12.5px] text-caution-soft-ink flex items-center gap-2"
            >
              <Icon name="info" size={14} />
              {w}
            </p>
          ))}
        </div>
      )}

      {/* Hero: recommendation OR empty-state with onboarding tiles */}
      {rec ? (
        <RecommendationCard rec={rec} />
      ) : (
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-md bg-primary-soft text-primary-soft-ink flex items-center justify-center shrink-0">
              <Icon name="sparkle" size={18} />
            </div>
            <div className="flex-1">
              <h2 className="text-[16px] font-semibold text-ink">
                No active recommendation yet
              </h2>
              <p className="text-[13px] text-ink-3 mt-1 leading-relaxed">
                Recommendations are generated on a schedule (typically once
                per business day). While you wait, customize your profile or
                try a template — both feed into the next run.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Next actions — three uniform CTA tiles */}
      <div>
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-ink-3 mb-2">
          Next actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-gap">
          {NEXT_ACTIONS.map((a) => (
            <Link
              key={a.href}
              href={a.href}
              className="rounded-lg border border-line bg-surface p-4 shadow-sm hover:border-primary hover:bg-surface-2 transition-colors block group"
            >
              <div className="w-8 h-8 rounded-md bg-primary-soft text-primary-soft-ink flex items-center justify-center mb-2">
                <Icon name={a.icon} size={16} />
              </div>
              <div className="text-[14px] font-semibold text-ink group-hover:text-primary transition-colors">
                {a.title}
              </div>
              <p className="text-[12.5px] text-ink-3 mt-1 leading-snug">
                {a.body}
              </p>
            </Link>
          ))}
        </div>
      </div>

      {/* Operations snapshot — collapsed by default (operator vocabulary) */}
      <details
        className="rounded-lg border border-line bg-surface shadow-sm"
        open={showDetails}
        onToggle={(e) => setShowDetails((e.target as HTMLDetailsElement).open)}
      >
        <summary className="cursor-pointer list-none px-4 py-3 flex items-center gap-2 text-[13px] text-ink-2">
          <Icon name="chevron-right" size={12} className={`transition-transform ${showDetails ? "rotate-90" : ""}`} />
          <span className="font-medium">Operations snapshot</span>
          <span className="text-[11px] text-ink-4">pipeline + health + activity</span>
        </summary>

        <div className="px-4 pb-4 space-y-gap border-t border-line pt-4">
          {/* KPI strip (kept for power users) */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
            {[
              { k: "Positions", v: rec ? String(rec.total_positions) : "—", sub: "active" },
              { k: "Publishable", v: rec ? "1" : "0", sub: "needs review", tone: "primary" },
              { k: "Warnings", v: rec ? String(rec.warning_count) : "0", sub: rec?.warning_count ? "active" : "none", tone: rec?.warning_count ? "caution" : "" },
              { k: "Freshness", v: data.health.source_freshness_ok ? "OK" : "Stale", sub: data.health.source_freshness_ok ? "sources current" : "check feeds", tone: data.health.source_freshness_ok ? "pos" : "caution" },
              { k: "Model health", v: data.health.model_health_ok ? "OK" : "Degraded", sub: data.health.model_health_ok ? "models healthy" : "check models", tone: data.health.model_health_ok ? "pos" : "caution" },
              { k: "Published recs", v: String(data.recent_recommendation_count), sub: "published" },
            ].map((kpi, i) => (
              <div key={i} className="rounded-md border border-line bg-surface-2 p-2.5">
                <p className="text-[10px] text-ink-4">{kpi.k}</p>
                <p
                  className={`text-[15px] font-display font-semibold mt-0.5 ${
                    kpi.tone === "primary"
                      ? "text-primary"
                      : kpi.tone === "caution"
                      ? "text-caution"
                      : kpi.tone === "pos"
                      ? "text-pos"
                      : "text-ink"
                  }`}
                >
                  {kpi.v}
                </p>
                <p className="text-[10px] text-ink-4 mt-0.5">{kpi.sub}</p>
              </div>
            ))}
          </div>

          <HealthPanel health={data.health} />

          {regime && (
            <div className="rounded-md border border-line bg-surface-2 p-3">
              <div className="flex items-center gap-2 mb-2">
                <Icon name="trend-up" size={13} className="text-primary" />
                <h3 className="text-[12px] font-semibold text-ink">
                  Regime & signal posture
                </h3>
                <span className="text-[10px] text-ink-4 ml-auto">
                  confidence {regime.regime_confidence.toFixed(2)} ·
                  persistence {regime.persistence_days}d
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-[11.5px]">
                <div>
                  <p className="text-[10px] text-ink-4 mb-1">Current regime</p>
                  <p className="text-[13px] font-semibold text-ink">
                    {regime.regime_label}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] text-ink-4 mb-1">Signal posture</p>
                  <div className="space-y-0.5">
                    {regime.signal_posture.map((sp) => (
                      <div key={sp.factor} className="flex items-center gap-2">
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            sp.sigma > 0
                              ? "bg-pos"
                              : sp.sigma < 0
                              ? "bg-breach"
                              : "bg-ink-4"
                          }`}
                        />
                        <span className="text-ink-2">
                          {sp.factor} {sp.direction}
                        </span>
                        <span
                          className={`font-mono ml-auto ${
                            sp.sigma > 0
                              ? "text-pos"
                              : sp.sigma < 0
                              ? "text-breach"
                              : "text-ink-3"
                          }`}
                        >
                          {sp.sigma > 0 ? "+" : ""}
                          {sp.sigma.toFixed(1)}σ
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[10px] text-ink-4 mb-1">Sector tilt</p>
                  <div className="space-y-0.5">
                    {regime.sector_tilts.map((st) => (
                      <div key={st.sector} className="flex items-center gap-2">
                        <span className="text-ink-2 w-16">{st.sector}</span>
                        <span
                          className={`font-mono ml-auto ${
                            st.tilt_pct >= 0 ? "text-pos" : "text-breach"
                          }`}
                        >
                          {st.tilt_pct >= 0 ? "+" : ""}
                          {st.tilt_pct.toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activity && activity.events.length > 0 && (
            <div className="rounded-md border border-line bg-surface-2 p-3">
              <div className="flex items-center gap-2 mb-2">
                <Icon name="news" size={13} className="text-primary" />
                <h3 className="text-[12px] font-semibold text-ink">Activity</h3>
                <span className="text-[10px] text-ink-4 ml-auto">
                  {activity.total} events
                </span>
              </div>
              <div className="space-y-1">
                {activity.events.slice(0, 6).map((ev, i) => (
                  <div key={i} className="flex items-start gap-2 py-1">
                    <div
                      className={`w-5 h-5 rounded-md flex items-center justify-center shrink-0 ${
                        KIND_STYLE[ev.kind] || "bg-surface-3 text-ink-3"
                      }`}
                    >
                      <Icon name={KIND_ICON[ev.kind] || "info"} size={10} />
                    </div>
                    <div className="flex-1 min-w-0 text-[11.5px]">
                      <p className="text-ink-2">
                        <b className="text-ink">{ev.actor}</b> {ev.description}
                        <span className="text-ink-4 ml-1.5">
                          · {ev.when_ago}
                        </span>
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}
