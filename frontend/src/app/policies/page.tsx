"use client";

import { useEffect, useMemo, useState } from "react";

import {
  fetchPolicyRules,
  fetchPolicyBreaches,
  fetchPolicyHistory,
  PolicyRule,
  PolicyBreach,
  PolicyHistoryEntry,
} from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PolicyRuleCard } from "@/components/policies/PolicyRuleCard";
import { HelpLink } from "@/components/help/HelpLink";

export default function PoliciesPage() {
  const { flags, isLoading: flagsLoading } = useFeatureFlags();
  const { user } = useAuth();
  const [rules, setRules] = useState<PolicyRule[]>([]);
  const [breaches, setBreaches] = useState<PolicyBreach[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // History drawer
  const [historyKey, setHistoryKey] = useState<string | null>(null);
  const [historyEntries, setHistoryEntries] = useState<PolicyHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    if (flagsLoading || !flags.policy_ui) return;
    Promise.all([fetchPolicyRules(), fetchPolicyBreaches()])
      .then(([rRes, bRes]) => {
        setRules(rRes.data);
        setBreaches(bRes.data);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [flagsLoading, flags.policy_ui]);

  const grouped = useMemo(() => {
    const m = new Map<string, PolicyRule[]>();
    for (const r of rules) {
      const cat = r.category || "uncategorized";
      const arr = m.get(cat) ?? [];
      arr.push(r);
      m.set(cat, arr);
    }
    return Array.from(m.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [rules]);

  const openHistory = async (key: string) => {
    setHistoryKey(key);
    setHistoryLoading(true);
    try {
      const res = await fetchPolicyHistory(key);
      setHistoryEntries(res.data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "History fetch failed");
    } finally {
      setHistoryLoading(false);
    }
  };

  const onUpdated = (updated: PolicyRule) => {
    setRules((prev) => prev.map((r) => (r.key === updated.key ? updated : r)));
  };

  if (flagsLoading || loading) return <PageLoading label="Loading policies..." />;
  if (!flags.policy_ui) {
    return (
      <PageError
        title="Surface not enabled"
        message="The Policy Editor surface is not enabled for this environment."
        hint="Set FEATURE_POLICY_UI=true in the backend environment."
      />
    );
  }
  if (error) return <PageError title="Connection Error" message={error} hint="Ensure the backend is running." />;

  const actor = user?.email ?? "anonymous";

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-[20px] font-semibold text-ink flex items-center gap-2">
            Policy Editor
            <HelpLink anchor="reference/pages/policies" label="Open Policies help" />
          </h1>
          <p className="text-[12px] text-ink-3 mt-0.5">
            {rules.length} rules · {breaches.filter((b) => b.is_active).length} active breaches
          </p>
        </div>
        <HelpLink
          anchor="guides/edit-a-policy"
          label="How to edit a policy"
          variant="inline"
        />
      </div>

      {breaches.length > 0 && (
        <section className="rounded-lg border border-caution bg-caution-soft p-pad">
          <h2 className="text-[13px] font-semibold text-caution-soft-ink mb-2">
            Active breaches
          </h2>
          <ul className="space-y-1.5" role="list">
            {breaches.filter((b) => b.is_active).map((b, i) => (
              <li key={i} className="text-[12.5px] text-caution-soft-ink flex items-center flex-wrap gap-2">
                <span className="font-medium">{b.label}</span>
                <span className="font-mono text-[11px]">{(b.utilization * 100).toFixed(0)}% · {b.trend}</span>
                {b.related && <span className="font-mono text-[11px] opacity-80">· {b.related}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}

      {grouped.map(([category, catRules]) => (
        <section key={category} className="space-y-2">
          <h2 className="text-[13px] font-semibold text-ink uppercase tracking-wider flex items-center gap-2">
            {category}
            <HelpLink
              anchor={`reference/policy-controls#${category.toLowerCase().replace(/_/g, "-")}`}
              label={`What is ${category}?`}
            />
          </h2>
          <div className="space-y-2">
            {catRules.map((rule) => (
              <PolicyRuleCard
                key={rule.key}
                rule={rule}
                actor={actor}
                onUpdated={onUpdated}
                onViewHistory={openHistory}
              />
            ))}
          </div>
        </section>
      ))}

      {/* Inline history drawer — bottom-sheet on mobile, right-aside on desktop */}
      {historyKey && (
        <>
          <div
            className="md:hidden fixed inset-0 z-30 bg-ink/40 backdrop-blur-sm"
            onClick={() => setHistoryKey(null)}
            aria-hidden="true"
          />
          <aside
            role="dialog"
            aria-modal="true"
            aria-label={`Policy history for ${historyKey}`}
            className="fixed inset-x-0 bottom-0 z-40 max-h-[85vh] rounded-t-2xl shadow-lg md:static md:max-h-none md:rounded-none md:shadow-md md:w-[420px] md:border-l md:border-line bg-surface flex flex-col overflow-hidden safe-area-pb"
          >
            <div className="md:hidden flex justify-center pt-2 pb-1 shrink-0">
              <span aria-hidden="true" className="block h-1 w-10 rounded-full bg-line-strong" />
            </div>
            <div className="flex items-center justify-between border-b border-line px-4 py-2 shrink-0">
              <h3 className="text-[13px] font-semibold text-ink">History · {historyKey}</h3>
              <button
                type="button"
                onClick={() => setHistoryKey(null)}
                aria-label="Close history"
                className="inline-flex items-center justify-center h-11 w-11 md:h-8 md:w-8 rounded-md hover:bg-surface-3 text-ink-3 transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {historyLoading ? (
                <p className="text-[12.5px] text-ink-3">Loading…</p>
              ) : historyEntries.length === 0 ? (
                <p className="text-[12.5px] text-ink-3">No history yet for this rule.</p>
              ) : (
                <ul className="space-y-3" role="list">
                  {historyEntries.map((h) => (
                    <li key={h.id} className="text-[12.5px]">
                      <p className="text-ink">
                        <span className="font-mono">{h.previous_value}</span>
                        {" → "}
                        <span className="font-mono font-semibold">{h.new_value}</span>
                      </p>
                      <p className="text-[11px] text-ink-3">
                        by <b>{h.actor}</b>
                        {h.created_at && ` · ${h.created_at.slice(0, 16).replace("T", " ")}`}
                      </p>
                      {h.reason && <p className="text-[11px] text-ink-3 mt-0.5">{h.reason}</p>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </aside>
        </>
      )}
    </div>
  );
}
