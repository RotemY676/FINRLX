"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAdmin } from "../../_context/AdminContext";
import { GlassCard } from "../GlassCard";
import { Icon } from "@/components/icons/Icon";
import {
  createFinrlxDatasetExport,
  listFinrlxDatasetExports,
  getFinrlxDatasetExport,
  markFinrlxDatasetExportStale,
  verifyFinrlxDatasetExport,
  rebuildFinrlxDatasetExportRegistry,
  DatasetExportResponse,
  DatasetExportRegistryEntry,
  DatasetExportVerifyResult,
} from "@/services/api";

export function DatasetExportPanel() {
  const {
    dsExportHistory,
    refreshExportHistory,
    pipelineIds,
    setPipelineId,
  } = useAdmin();

  // ── Export form state ──
  const [dsExportName, setDsExportName] = useState("Local Research Dataset Export");
  const [dsExportStart, setDsExportStart] = useState("2026-03-15");
  const [dsExportEnd, setDsExportEnd] = useState("2026-04-15");
  const [dsExportCandidateId, setDsExportCandidateId] = useState("");
  const [dsExportBenchmarkId, setDsExportBenchmarkId] = useState("");
  const [dsExportFormat, setDsExportFormat] = useState<"jsonl" | "json">("jsonl");
  const [dsExportFeatures, setDsExportFeatures] = useState(true);
  const [dsExportTargets, setDsExportTargets] = useState(true);
  const [dsExportWarnings, setDsExportWarnings] = useState(true);
  const [dsExportAck, setDsExportAck] = useState(false);
  const [dsExportLoading, setDsExportLoading] = useState(false);
  const [dsExportError, setDsExportError] = useState<string | null>(null);
  const [dsExportResult, setDsExportResult] = useState<DatasetExportResponse | null>(null);

  // ── Governance state ──
  const [dsSelectedExport, setDsSelectedExport] = useState<DatasetExportResponse | null>(null);
  const [dsVerifyResult, setDsVerifyResult] = useState<DatasetExportVerifyResult | null>(null);
  const [dsStaleAck, setDsStaleAck] = useState(false);
  const [dsStaleReason, setDsStaleReason] = useState("");
  const [dsRebuildAck, setDsRebuildAck] = useState(false);
  const [dsGovLoading, setDsGovLoading] = useState<string | null>(null);
  const [dsGovError, setDsGovError] = useState<string | null>(null);
  const [dsGovSuccess, setDsGovSuccess] = useState<string | null>(null);

  // ── Callbacks ──
  const runDatasetExport = useCallback(async () => {
    if (!dsExportAck) return;
    setDsExportLoading(true);
    setDsExportError(null);
    setDsExportResult(null);
    try {
      const res = await createFinrlxDatasetExport({
        name: dsExportName,
        start_date: dsExportStart,
        end_date: dsExportEnd,
        candidate_id: dsExportCandidateId || null,
        benchmark_report_id: dsExportBenchmarkId || null,
        format: dsExportFormat,
        include_features: dsExportFeatures,
        include_targets: dsExportTargets,
        include_warnings: dsExportWarnings,
        research_acknowledgement: true,
      });
      if (res.data) {
        setDsExportResult(res.data);
        setPipelineId("exportId", res.data.export_id);
        refreshExportHistory();
      }
    } catch (e: unknown) {
      setDsExportError(e instanceof Error ? e.message : "Dataset export failed");
    } finally {
      setDsExportLoading(false);
    }
  }, [dsExportName, dsExportStart, dsExportEnd, dsExportCandidateId, dsExportBenchmarkId, dsExportFormat, dsExportFeatures, dsExportTargets, dsExportWarnings, dsExportAck, setPipelineId, refreshExportHistory]);

  const selectExportEntry = useCallback(async (entry: DatasetExportRegistryEntry) => {
    setDsSelectedExport(null);
    setDsVerifyResult(null);
    setDsStaleAck(false);
    setDsStaleReason("");
    setDsGovError(null);
    setDsGovSuccess(null);
    try {
      const res = await getFinrlxDatasetExport(entry.export_id);
      if (res.data) setDsSelectedExport(res.data);
    } catch { /* graceful */ }
  }, []);

  const handleVerifyExport = useCallback(async () => {
    if (!dsSelectedExport) return;
    setDsGovLoading("verify");
    setDsGovError(null);
    setDsVerifyResult(null);
    try {
      const res = await verifyFinrlxDatasetExport(dsSelectedExport.export_id);
      if (res.data) setDsVerifyResult(res.data);
    } catch (e: unknown) {
      setDsGovError(e instanceof Error ? e.message : "Verify failed");
    } finally {
      setDsGovLoading(null);
    }
  }, [dsSelectedExport]);

  const handleMarkStale = useCallback(async () => {
    if (!dsSelectedExport || !dsStaleAck) return;
    setDsGovLoading("stale");
    setDsGovError(null);
    setDsGovSuccess(null);
    try {
      await markFinrlxDatasetExportStale(dsSelectedExport.export_id, {
        acknowledgement: true,
        reason: dsStaleReason || undefined,
      });
      setDsGovSuccess("Export marked as stale.");
      refreshExportHistory();
      const match = dsExportHistory.find(e => e.export_id === dsSelectedExport.export_id);
      if (match) selectExportEntry({ ...match });
    } catch (e: unknown) {
      setDsGovError(e instanceof Error ? e.message : "Mark stale failed");
    } finally {
      setDsGovLoading(null);
    }
  }, [dsSelectedExport, dsStaleAck, dsStaleReason, refreshExportHistory, selectExportEntry, dsExportHistory]);

  const handleRebuildRegistry = useCallback(async () => {
    if (!dsRebuildAck) return;
    setDsGovLoading("rebuild");
    setDsGovError(null);
    setDsGovSuccess(null);
    try {
      const res = await rebuildFinrlxDatasetExportRegistry({ acknowledgement: true });
      setDsGovSuccess(`Registry rebuilt: ${res.data.export_count} exports found.`);
      setDsRebuildAck(false);
      refreshExportHistory();
    } catch (e: unknown) {
      setDsGovError(e instanceof Error ? e.message : "Rebuild failed");
    } finally {
      setDsGovLoading(null);
    }
  }, [dsRebuildAck, refreshExportHistory]);

  return (
    <AnimatePresence mode="wait">
      <GlassCard>
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Icon name="sparkle" size={15} className="text-accent-2" />
          <h3 className="text-[13px] font-semibold text-ink">Dataset Export for Local Research</h3>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Research-only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Offline-only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">No production influence</span>
        </div>
        <p className="text-[10px] text-ink-4 mb-3">
          Export shadow dataset for local offline research. Not used by production decisions. Not eligible for promotion. No broker execution.
        </p>

        {/* Export form */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
          <div className="sm:col-span-3">
            <label className="text-[10px] text-ink-4 block mb-1">Export name</label>
            <input type="text" value={dsExportName} onChange={(e) => setDsExportName(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-1">Start date</label>
            <input type="date" value={dsExportStart} onChange={(e) => setDsExportStart(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-1">End date</label>
            <input type="date" value={dsExportEnd} onChange={(e) => setDsExportEnd(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-1">Format</label>
            <select value={dsExportFormat} onChange={(e) => setDsExportFormat(e.target.value as "jsonl" | "json")}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none">
              <option value="jsonl">JSONL</option>
              <option value="json">JSON</option>
            </select>
          </div>
          <div className="sm:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-ink-4 block mb-1">Candidate ID (optional)</label>
              <input type="text" value={dsExportCandidateId} onChange={(e) => setDsExportCandidateId(e.target.value)}
                placeholder="Leave empty for general export"
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
            </div>
            <div>
              <label className="text-[10px] text-ink-4 block mb-1">Benchmark report ID (optional)</label>
              <input type="text" value={dsExportBenchmarkId} onChange={(e) => setDsExportBenchmarkId(e.target.value)}
                placeholder="Leave empty"
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
            </div>
          </div>
        </div>

        {/* Checkboxes */}
        <div className="flex flex-wrap gap-4 mb-3 text-[11px]">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={dsExportFeatures} onChange={(e) => setDsExportFeatures(e.target.checked)} className="rounded" />
            <span className="text-ink-2">Include features</span>
          </label>
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={dsExportTargets} onChange={(e) => setDsExportTargets(e.target.checked)} className="rounded" />
            <span className="text-ink-2">Include targets</span>
          </label>
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={dsExportWarnings} onChange={(e) => setDsExportWarnings(e.target.checked)} className="rounded" />
            <span className="text-ink-2">Include warnings</span>
          </label>
        </div>

        {/* Acknowledgement */}
        <label className="flex items-start gap-2 mb-3 cursor-pointer">
          <input type="checkbox" checked={dsExportAck} onChange={(e) => setDsExportAck(e.target.checked)} className="mt-0.5 rounded" />
          <span className="text-[10px] text-ink-3">
            I acknowledge this is a research-only, offline-only, shadow-only dataset export.
            It is not used by production decisions and is not eligible for promotion.
          </span>
        </label>

        {/* Run button */}
        <button
          onClick={runDatasetExport}
          disabled={dsExportLoading || !dsExportAck || !dsExportStart || !dsExportEnd}
          className="px-4 py-1.5 rounded-md text-[12px] font-medium bg-primary text-primary-ink hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {dsExportLoading ? "Exporting..." : "Run Dataset Export"}
        </button>

        {dsExportError && (
          <div className="mt-3 p-3 rounded-md bg-breach/10 border border-breach/20 text-[11px] text-breach break-words">{dsExportError}</div>
        )}

        {/* Result panel */}
        {dsExportResult && (
          <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="mt-3 p-3 rounded-md bg-surface-2 border border-line text-[11px] space-y-1.5">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="font-semibold text-ink">Export completed</span>
              <span className="text-pos text-[10px]">{dsExportResult.status}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[10px]">
              <div><span className="text-ink-4">Export ID:</span> <span className="font-mono text-ink-2 break-all">{dsExportResult.export_id}</span></div>
              <div><span className="text-ink-4">Row count:</span> <span className="text-ink">{dsExportResult.row_count}</span></div>
              <div><span className="text-ink-4">Date range:</span> <span className="text-ink">{dsExportResult.date_range ? `${dsExportResult.date_range.start} - ${dsExportResult.date_range.end}` : "N/A"}</span></div>
              <div><span className="text-ink-4">Format:</span> <span className="text-ink">{dsExportResult.export_format}</span></div>
              <div className="sm:col-span-2"><span className="text-ink-4">Export path:</span> <span className="font-mono text-ink-2 break-all">{dsExportResult.export_path}</span></div>
              <div className="sm:col-span-2"><span className="text-ink-4">Checksum:</span> <span className="font-mono text-ink-2 break-all">{dsExportResult.checksum}</span></div>
              <div><span className="text-ink-4">Fingerprint:</span> <span className="font-mono text-ink-2 break-all">{dsExportResult.fingerprint}</span></div>
            </div>
            {dsExportResult.feature_schema.length > 0 && (
              <div className="text-[10px]"><span className="text-ink-4">Features:</span> <span className="text-ink-2">{dsExportResult.feature_schema.join(", ")}</span></div>
            )}
            {dsExportResult.target_schema.length > 0 && (
              <div className="text-[10px]"><span className="text-ink-4">Targets:</span> <span className="text-ink-2">{dsExportResult.target_schema.join(", ")}</span></div>
            )}
            {dsExportResult.warnings.length > 0 && (
              <div className="text-[10px] text-caution">Warnings: {dsExportResult.warnings.join("; ")}</div>
            )}
            <div className="flex flex-wrap gap-1.5 mt-1">
              {Object.entries(dsExportResult.safety_flags).map(([k, v]) => (
                <span key={k} className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${v ? "bg-pos/10 text-pos" : "bg-breach/10 text-breach"}`}>
                  {k.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </motion.div>
        )}

        {/* Export registry / governance */}
        <div className="mt-4 border-t border-line pt-3">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <h4 className="text-[12px] font-semibold text-ink">Dataset Export Governance</h4>
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Local export registry</span>
          </div>

          {dsGovError && <div className="mb-2 p-2 rounded-md bg-breach/10 border border-breach/20 text-[10px] text-breach break-words">{dsGovError}</div>}
          {dsGovSuccess && <div className="mb-2 p-2 rounded-md bg-pos/10 border border-pos/20 text-[10px] text-pos">{dsGovSuccess}</div>}

          {/* Export registry list */}
          {dsExportHistory.length > 0 && (
            <div className="mb-3">
              <div className="space-y-1">
                {dsExportHistory.map((h) => (
                  <button key={h.export_id} onClick={() => selectExportEntry(h)}
                    className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                      dsSelectedExport?.export_id === h.export_id ? "border-primary bg-primary/5" : "border-line/30 hover:bg-surface-2"
                    }`}>
                    <span className="font-mono text-ink-2 break-all">{h.export_id?.slice(0, 8)}</span>
                    <span className="text-ink font-medium truncate max-w-[150px]">{h.name}</span>
                    <span className="text-ink-3">{h.row_count} rows</span>
                    <span className="text-ink-4">{h.export_format}</span>
                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                      h.lifecycle_state === "active" ? "bg-pos/10 text-pos" : "bg-caution/10 text-caution"
                    }`}>{h.lifecycle_state}</span>
                    <span className={`w-1.5 h-1.5 rounded-full ${h.artifact_exists ? "bg-pos" : "bg-breach"}`} title={h.artifact_exists ? "Artifact exists" : "Artifact missing"} />
                    <span className="text-ink-4 ml-auto">{h.created_at?.slice(0, 19)}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Selected export detail */}
          {dsSelectedExport && (
            <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="p-3 rounded-md bg-surface-2 border border-line text-[10px] space-y-2 mb-3">
              <div className="font-semibold text-[11px] text-ink mb-1">Export Detail</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                <div><span className="text-ink-4">Export ID:</span> <span className="font-mono text-ink-2 break-all">{dsSelectedExport.export_id}</span></div>
                <div><span className="text-ink-4">Status:</span> <span className="text-ink">{dsSelectedExport.status}</span> / <span className={dsSelectedExport.lifecycle_state === "active" ? "text-pos" : "text-caution"}>{dsSelectedExport.lifecycle_state}</span></div>
                <div><span className="text-ink-4">Row count:</span> <span className="text-ink">{dsSelectedExport.row_count}</span></div>
                <div><span className="text-ink-4">Format:</span> <span className="text-ink">{dsSelectedExport.export_format}</span></div>
                <div className="sm:col-span-2"><span className="text-ink-4">Path:</span> <span className="font-mono text-ink-2 break-all">{dsSelectedExport.export_path}</span></div>
                <div className="sm:col-span-2"><span className="text-ink-4">Checksum:</span> <span className="font-mono text-ink-2 break-all">{dsSelectedExport.checksum}</span></div>
                <div><span className="text-ink-4">Fingerprint:</span> <span className="font-mono text-ink-2 break-all">{dsSelectedExport.fingerprint}</span></div>
                <div><span className="text-ink-4">Artifact:</span> <span className={dsSelectedExport.artifact_exists ? "text-pos" : "text-breach"}>{dsSelectedExport.artifact_exists ? "exists" : "missing"}</span></div>
              </div>
              {dsSelectedExport.warnings && dsSelectedExport.warnings.length > 0 && (
                <div className="text-caution">Warnings: {dsSelectedExport.warnings.join("; ")}</div>
              )}
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(dsSelectedExport.safety_flags || {}).map(([k, v]) => (
                  <span key={k} className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${v ? "bg-pos/10 text-pos" : "bg-breach/10 text-breach"}`}>
                    {k.replace(/_/g, " ")}
                  </span>
                ))}
              </div>

              {/* Operator controls */}
              <div className="flex flex-wrap gap-2 pt-2 border-t border-line/30">
                <button onClick={handleVerifyExport} disabled={dsGovLoading === "verify"}
                  className="px-3 py-1 rounded-md text-[10px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40 transition-colors">
                  {dsGovLoading === "verify" ? "Verifying..." : "Verify Artifact"}
                </button>
              </div>

              {dsVerifyResult && (
                <div className="p-2 rounded-md bg-surface-3 text-[10px] space-y-1">
                  <div className="font-medium text-ink">Artifact Verification</div>
                  <div>Metadata: <span className={dsVerifyResult.metadata_exists ? "text-pos" : "text-breach"}>{dsVerifyResult.metadata_exists ? "found" : "missing"}</span></div>
                  <div>Data: <span className={dsVerifyResult.data_exists ? "text-pos" : "text-breach"}>{dsVerifyResult.data_exists ? "found" : "missing"}</span></div>
                  {dsVerifyResult.warnings.length > 0 && <div className="text-caution">{dsVerifyResult.warnings.join("; ")}</div>}
                </div>
              )}

              {/* Mark stale control */}
              {dsSelectedExport.lifecycle_state === "active" && (
                <div className="pt-2 border-t border-line/30 space-y-2">
                  <div className="text-[10px] text-ink-3 font-medium">Mark as Stale</div>
                  <input type="text" value={dsStaleReason} onChange={(e) => setDsStaleReason(e.target.value)}
                    placeholder="Reason (optional)"
                    className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
                  <label className="flex items-center gap-1.5 cursor-pointer text-[10px]">
                    <input type="checkbox" checked={dsStaleAck} onChange={(e) => setDsStaleAck(e.target.checked)} className="rounded" />
                    <span className="text-ink-3">I acknowledge this marks the export as stale (does not delete files)</span>
                  </label>
                  <button onClick={handleMarkStale} disabled={!dsStaleAck || dsGovLoading === "stale"}
                    className="px-3 py-1 rounded-md text-[10px] font-medium bg-caution/20 text-caution hover:bg-caution/30 disabled:opacity-40 transition-colors">
                    {dsGovLoading === "stale" ? "Marking..." : "Mark Stale"}
                  </button>
                </div>
              )}
            </motion.div>
          )}

          {/* Rebuild registry control */}
          <div className="pt-2 border-t border-line/30">
            <div className="text-[10px] text-ink-3 font-medium mb-1">Rebuild Registry from Files</div>
            <label className="flex items-center gap-1.5 cursor-pointer text-[10px] mb-1.5">
              <input type="checkbox" checked={dsRebuildAck} onChange={(e) => setDsRebuildAck(e.target.checked)} className="rounded" />
              <span className="text-ink-3">I acknowledge this scans research/finrlx_cpu/exports/ and rebuilds the registry</span>
            </label>
            <button onClick={handleRebuildRegistry} disabled={!dsRebuildAck || dsGovLoading === "rebuild"}
              className="px-3 py-1 rounded-md text-[10px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40 transition-colors">
              {dsGovLoading === "rebuild" ? "Rebuilding..." : "Rebuild Registry"}
            </button>
          </div>
        </div>
      </GlassCard>
    </AnimatePresence>
  );
}
