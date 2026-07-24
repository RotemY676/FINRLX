"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchOps, OpsData } from "@/services/api";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import { useAuth } from "@/contexts/AuthContext";
import { SignInRequired } from "@/components/feedback/SignInRequired";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { OpsKpiStrip } from "@/components/ops/OpsKpiStrip";
import { OpsQueuePanel } from "@/components/ops/OpsQueuePanel";
import { OpsHealthGrid } from "@/components/ops/OpsHealthGrid";
import { OpsBreachesIncidents } from "@/components/ops/OpsBreachesIncidents";
import { OpsAuditLog } from "@/components/ops/OpsAuditLog";

export default function OpsPage() {
  const { flags, isLoading: flagsLoading } = useFeatureFlags();
  const { user, isLoading: authLoading } = useAuth();
  const [data, setData] = useState<OpsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    if (flagsLoading || authLoading || !flags.ops_ui) return;
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchOps()
      .then((res) => setData(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [flagsLoading, flags.ops_ui, authLoading, user]);

  useEffect(load, [load]);

  if (flagsLoading || authLoading || loading) return <PageLoading label="Loading Ops..." />;
  if (!user) return <SignInRequired feature="the ops command center" />;
  if (!flags.ops_ui) {
    return (
      <PageError
        title="Surface not enabled"
        message="The Ops command surface is not enabled for this environment."
        hint="Set FEATURE_OPS_UI=true in the backend environment."
      />
    );
  }
  if (error) return <PageError title="Connection Error" message={error} hint="Ensure the backend is running." />;
  if (!data) return null;

  const handleAction = (_id: string, message: string) => {
    setActionMsg(message);
    // Refetch so the queue and audit reflect the new state.
    load();
  };

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div className="flex items-baseline justify-between gap-2">
        <div>
          <h1 className="text-page-title text-ink">Ops command</h1>
          <p className="text-body-sm text-ink-2 mt-0.5">
            Queue · feeds · engines · breaches · incidents · audit
          </p>
        </div>
      </div>

      {actionMsg && (
        <div
          role="status"
          aria-live="polite"
          className="rounded-md bg-primary-soft text-primary-soft-ink px-3 py-2 text-caption"
        >
          {actionMsg}
        </div>
      )}

      <OpsKpiStrip kpis={data.system_kpis} />

      <OpsQueuePanel items={data.queue} onActionDone={handleAction} />

      <OpsHealthGrid feeds={data.feeds} engines={data.engines} />

      <OpsBreachesIncidents breaches={data.breaches} incidents={data.incidents} />

      <OpsAuditLog entries={data.audit} />
    </div>
  );
}
