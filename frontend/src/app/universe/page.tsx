"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createUniverse,
  deactivateUniverse,
  fetchUniverses,
  fetchUniverseDetail,
  fetchUniverseCoverage,
  fetchUniverseReadiness,
  updateUniverse,
  UniverseListItem,
  UniverseDetail,
  UniverseCoverage,
  UniverseReadiness,
} from "@/services/api";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import { PageLoading, InlineLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { UniverseList } from "@/components/universe/UniverseList";
import { CoveragePanel } from "@/components/universe/CoveragePanel";
import { ReadinessPanel } from "@/components/universe/ReadinessPanel";
import { SectorBreakdown } from "@/components/universe/SectorBreakdown";
import { UniverseDialog } from "@/components/universe/UniverseDialog";
import { HelpLink } from "@/components/help/HelpLink";

type DialogState =
  | { mode: "closed" }
  | { mode: "create" }
  | { mode: "rename"; universe: UniverseDetail };

export default function UniversePage() {
  const { flags, isLoading: flagsLoading } = useFeatureFlags();
  const [universes, setUniverses] = useState<UniverseListItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<UniverseDetail | null>(null);
  const [coverage, setCoverage] = useState<UniverseCoverage | null>(null);
  const [readiness, setReadiness] = useState<UniverseReadiness | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  // Phase 20.4 CRUD state
  const [dialog, setDialog] = useState<DialogState>({ mode: "closed" });
  const [dialogBusy, setDialogBusy] = useState(false);
  const [dialogError, setDialogError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const reloadList = useCallback(async (preferredSelectedId?: string | null) => {
    const res = await fetchUniverses();
    setUniverses(res.data);
    if (res.data.length === 0) {
      setSelectedId(null);
    } else if (preferredSelectedId && res.data.some((u) => u.universe_id === preferredSelectedId)) {
      setSelectedId(preferredSelectedId);
    } else if (!selectedId || !res.data.some((u) => u.universe_id === selectedId)) {
      setSelectedId(res.data[0].universe_id);
    }
  }, [selectedId]);

  useEffect(() => {
    if (flagsLoading || !flags.universe_ui) return;
    fetchUniverses()
      .then((res) => {
        setUniverses(res.data);
        if (res.data.length > 0) {
          setSelectedId(res.data[0].universe_id);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setListLoading(false));
  }, [flags.universe_ui, flagsLoading]);

  useEffect(() => {
    if (!selectedId) return;
    setDetailLoading(true);
    setDetail(null);
    setCoverage(null);
    setReadiness(null);
    Promise.all([
      fetchUniverseDetail(selectedId),
      fetchUniverseCoverage(selectedId),
      fetchUniverseReadiness(selectedId),
    ])
      .then(([d, c, r]) => {
        setDetail(d.data);
        setCoverage(c.data);
        setReadiness(r.data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setDetailLoading(false));
  }, [selectedId]);

  const handleSubmit = useCallback(async (name: string, description: string) => {
    setDialogBusy(true);
    setDialogError(null);
    try {
      if (dialog.mode === "create") {
        const res = await createUniverse(name, description || null);
        const newId = res.data.universe_id;
        await reloadList(newId);
        setDialog({ mode: "closed" });
      } else if (dialog.mode === "rename") {
        const res = await updateUniverse(dialog.universe.universe_id, {
          name,
          description: description || null,
        });
        await reloadList(res.data.universe_id);
        setDetail(res.data);
        setDialog({ mode: "closed" });
      }
    } catch (e) {
      setDialogError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setDialogBusy(false);
    }
  }, [dialog, reloadList]);

  const handleDeactivate = useCallback(async () => {
    if (!detail) return;
    const confirmed = window.confirm(
      `Deactivate "${detail.name}"? It will disappear from the picker but its membership history stays for backtest replay.`
    );
    if (!confirmed) return;
    setActionError(null);
    try {
      await deactivateUniverse(detail.universe_id);
      await reloadList();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Unknown error");
    }
  }, [detail, reloadList]);

  if (flagsLoading || listLoading) return <PageLoading label="Loading universes..." />;
  if (!flags.universe_ui) {
    return (
      <PageError
        title="Surface not enabled"
        message="The Universe workspace is not enabled for this environment."
        hint="Set FEATURE_UNIVERSE_UI=true in the backend environment."
      />
    );
  }
  if (error) return <PageError title="Connection Error" message={error} hint="Ensure the backend is running." />;

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-[20px] font-semibold text-ink flex items-center gap-2">
            Universe
            <HelpLink anchor="reference/pages/universe" label="Open Universe help" />
          </h1>
          <p className="text-[12px] text-ink-3 mt-0.5">
            Saved universes · coverage · readiness · sector breakdown
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => { setDialogError(null); setDialog({ mode: "create" }); }}
            className="px-3 py-1.5 rounded-md bg-primary text-primary-ink text-[12px] font-medium hover:opacity-90"
          >
            + New universe
          </button>
          <HelpLink
            anchor="guides/manage-your-universe"
            label="How to manage your universe"
            variant="inline"
          />
        </div>
      </div>

      {actionError && (
        <div className="text-body-sm text-breach-soft-ink bg-breach-soft border border-breach-soft-ink/20 rounded-md p-2" role="alert">
          {actionError}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-gap">
        <div className="lg:col-span-1">
          <UniverseList
            universes={universes}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>

        <div className="lg:col-span-2 space-y-gap">
          {detailLoading && <InlineLoading label="Loading detail..." />}
          {detail && (
            <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
              <div className="flex items-baseline justify-between mb-1 gap-2 flex-wrap">
                <h2 className="text-[15px] font-semibold text-ink">{detail.name}</h2>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-ink-4 font-mono">
                    {detail.active_asset_count}/{detail.asset_count} active
                  </span>
                  <button
                    type="button"
                    onClick={() => { setDialogError(null); setDialog({ mode: "rename", universe: detail }); }}
                    className="text-[11px] text-ink-2 hover:text-ink underline underline-offset-2 decoration-1 hover:decoration-2"
                  >
                    Rename
                  </button>
                  <button
                    type="button"
                    onClick={handleDeactivate}
                    className="text-[11px] text-breach hover:opacity-90 underline underline-offset-2 decoration-1 hover:decoration-2"
                  >
                    Deactivate
                  </button>
                </div>
              </div>
              {detail.description && (
                <p className="text-[12.5px] text-ink-3 mb-3">{detail.description}</p>
              )}
              <div className="flex flex-wrap gap-1.5">
                {detail.tickers.slice(0, 40).map((t) => (
                  <span
                    key={t}
                    className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-surface-3 text-ink-2"
                  >
                    {t}
                  </span>
                ))}
                {detail.tickers.length > 40 && (
                  <span className="text-[11px] text-ink-4">
                    +{detail.tickers.length - 40} more
                  </span>
                )}
              </div>
            </div>
          )}

          {coverage && <CoveragePanel coverage={coverage} />}
          {readiness && <ReadinessPanel readiness={readiness} />}
          {detail && <SectorBreakdown assets={detail.assets} />}
        </div>
      </div>

      <UniverseDialog
        open={dialog.mode !== "closed"}
        mode={dialog.mode === "rename" ? "rename" : "create"}
        initial={dialog.mode === "rename" ? { name: dialog.universe.name, description: dialog.universe.description } : null}
        busy={dialogBusy}
        error={dialogError}
        onSubmit={handleSubmit}
        onClose={() => setDialog({ mode: "closed" })}
      />
    </div>
  );
}
