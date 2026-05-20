"use client";

import { useEffect, useMemo, useState } from "react";

import {
  fetchIntegrations,
  fetchIntegrationHealth,
  Integration,
  IntegrationHealth,
} from "@/services/api";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { Icon } from "@/components/icons/Icon";

const STATUS_STYLE: Record<string, string> = {
  healthy: "bg-pos-soft text-pos-soft-ink",
  degraded: "bg-caution-soft text-caution-soft-ink",
  stale: "bg-caution-soft text-caution-soft-ink",
  placeholder: "bg-surface-3 text-ink-3",
};

const CATEGORY_LABEL: Record<string, string> = {
  market_data: "Market data",
  news: "News & sentiment",
  fundamentals: "Fundamentals",
  sentiment: "Alternative & sentiment",
};

function IntegrationCard({ integration }: { integration: Integration }) {
  const i = integration;
  return (
    <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center flex-wrap gap-2">
            <h3 className="text-[14px] font-semibold text-ink truncate">{i.name}</h3>
            <span className={`px-2 py-0.5 rounded-md text-[11px] font-medium ${STATUS_STYLE[i.status] ?? STATUS_STYLE.placeholder}`}>
              {i.status}
            </span>
            {i.is_placeholder && (
              <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-caution-soft text-caution-soft-ink">
                placeholder
              </span>
            )}
          </div>
          <p className="text-[11px] text-ink-4 font-mono mt-1">{i.source_key}</p>
        </div>
        <div className="flex flex-col items-start md:items-end gap-1 text-[12px] text-ink-3 shrink-0">
          <span>Coverage: <span className="text-ink-2">{i.coverage}</span></span>
          <span>Freshness: <span className="text-ink-2">{i.freshness}</span></span>
          {i.last_success_at && (
            <span className="text-[11px] text-ink-4">Last OK {i.last_success_at.slice(0, 16).replace("T", " ")}</span>
          )}
        </div>
      </div>
      {i.warnings.length > 0 && (
        <ul className="mt-3 space-y-1" role="list">
          {i.warnings.map((w, idx) => (
            <li key={idx} className="flex items-start gap-2 text-[12px] text-caution-soft-ink">
              <Icon name="alert-triangle" size={12} className="mt-0.5 shrink-0 text-caution" aria-hidden="true" />
              <span>{w}</span>
            </li>
          ))}
        </ul>
      )}
      {i.next_action && (
        <p className="mt-2 text-[11px] text-ink-3">
          Next action: <span className="font-mono">{i.next_action}</span>
        </p>
      )}
    </div>
  );
}

export default function IntegrationsPage() {
  const { flags, isLoading: flagsLoading } = useFeatureFlags();
  const [items, setItems] = useState<Integration[]>([]);
  const [health, setHealth] = useState<IntegrationHealth | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (flagsLoading || !flags.integrations_ui) return;
    Promise.all([fetchIntegrations(), fetchIntegrationHealth()])
      .then(([iRes, hRes]) => {
        setItems(iRes.data);
        setHealth(hRes.data);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [flagsLoading, flags.integrations_ui]);

  const grouped = useMemo(() => {
    const m = new Map<string, Integration[]>();
    for (const i of items) {
      const cat = i.category || "uncategorized";
      const arr = m.get(cat) ?? [];
      arr.push(i);
      m.set(cat, arr);
    }
    return Array.from(m.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [items]);

  if (flagsLoading || loading) return <PageLoading label="Loading integrations..." />;
  if (!flags.integrations_ui) {
    return (
      <PageError
        title="Surface not enabled"
        message="The Integrations surface is not enabled for this environment."
        hint="Set FEATURE_INTEGRATIONS_UI=true in the backend environment."
      />
    );
  }
  if (error) return <PageError title="Connection Error" message={error} hint="Ensure the backend is running." />;

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div>
        <h1 className="text-[20px] font-semibold text-ink">Integrations</h1>
        <p className="text-[12px] text-ink-3 mt-0.5">
          {items.length} data sources connected
        </p>
      </div>

      {health && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-gap">
          <div className="rounded-lg border border-line bg-surface p-3 shadow-sm">
            <p className="text-[11px] text-ink-4">Total</p>
            <p className="text-[20px] font-display font-semibold text-ink mt-0.5">{health.total_integrations}</p>
          </div>
          <div className="rounded-lg border border-line bg-surface p-3 shadow-sm">
            <p className="text-[11px] text-ink-4">Healthy</p>
            <p className="text-[20px] font-display font-semibold text-pos mt-0.5">{health.healthy}</p>
          </div>
          <div className="rounded-lg border border-line bg-surface p-3 shadow-sm">
            <p className="text-[11px] text-ink-4">Degraded</p>
            <p className={`text-[20px] font-display font-semibold mt-0.5 ${health.degraded > 0 ? "text-caution" : "text-ink"}`}>
              {health.degraded}
            </p>
          </div>
          <div className="rounded-lg border border-line bg-surface p-3 shadow-sm">
            <p className="text-[11px] text-ink-4">Placeholder</p>
            <p className={`text-[20px] font-display font-semibold mt-0.5 ${health.placeholder > 0 ? "text-caution" : "text-ink"}`}>
              {health.placeholder}
            </p>
          </div>
          <div className="rounded-lg border border-line bg-surface p-3 shadow-sm">
            <p className="text-[11px] text-ink-4">Real providers</p>
            <p className="text-[20px] font-display font-semibold text-ink mt-0.5">{health.real_providers}</p>
          </div>
        </div>
      )}

      {grouped.map(([category, catItems]) => (
        <section key={category} className="space-y-2">
          <h2 className="text-[13px] font-semibold text-ink uppercase tracking-wider">
            {CATEGORY_LABEL[category] ?? category}
          </h2>
          <div className="space-y-2">
            {catItems.map((i) => (
              <IntegrationCard key={i.source_key + i.name} integration={i} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
