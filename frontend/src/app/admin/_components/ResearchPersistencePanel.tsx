"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { GlassCard } from "./GlassCard";
import { Icon } from "@/components/icons/Icon";
import {
  getFinrlxPersistenceStatus,
  type FinrlxPersistenceStatus,
  type FinrlxRegistryPersistenceStatus,
} from "@/services/api";

const STATUS_COLOR: Record<string, string> = {
  ok: "bg-pos",
  missing: "bg-caution",
  degraded: "bg-breach",
  unavailable: "bg-ink-4",
};

const STATUS_TEXT: Record<string, string> = {
  ok: "text-pos",
  missing: "text-caution",
  degraded: "text-breach",
  unavailable: "text-ink-4",
};

function RegistryStatusRow({ reg }: { reg: FinrlxRegistryPersistenceStatus }) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-line/30 last:border-b-0">
      <span className={`w-2 h-2 rounded-full shrink-0 ${STATUS_COLOR[reg.status] || "bg-ink-4"}`} />
      <div className="flex-1 min-w-0">
        <p className="text-[12px] text-ink font-medium">{reg.registry_name.replace(/_/g, " ")}</p>
        <p className="text-[10px] text-ink-4 font-mono truncate">{reg.directory_path}</p>
      </div>
      <div className="text-right shrink-0">
        <p className={`text-[11px] font-medium ${STATUS_TEXT[reg.status] || "text-ink-4"}`}>{reg.status}</p>
        <p className="text-[10px] text-ink-4">{reg.item_count} items</p>
      </div>
      {reg.warnings.length > 0 && (
        <div className="shrink-0" title={reg.warnings.join("; ")}>
          <Icon name="alert-triangle" size={12} className="text-caution" />
        </div>
      )}
    </div>
  );
}

export function ResearchPersistencePanel() {
  const [status, setStatus] = useState<FinrlxPersistenceStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getFinrlxPersistenceStatus();
      setStatus(res.data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load persistence status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  if (!status && !loading && !error) return null;

  const hasWarnings = (status?.warnings?.length ?? 0) > 0;
  const allOk = status?.registry_statuses?.every(r => r.status === "ok") ?? false;
  const overallStatus = error ? "error" : allOk && !hasWarnings ? "healthy" : "attention";

  return (
    <GlassCard className="mt-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <Icon name="database" size={15} className={overallStatus === "healthy" ? "text-pos" : overallStatus === "error" ? "text-breach" : "text-caution"} />
        <h3 className="text-[13px] font-semibold text-ink">Research Storage & Deployment</h3>
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Research only</span>
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Offline only</span>
        <button onClick={fetchStatus} disabled={loading}
          className="ml-auto p-1.5 rounded-lg hover:bg-surface-2 text-ink-4 hover:text-ink transition-colors disabled:opacity-40"
          title="Refresh persistence status">
          <Icon name="history" size={14} />
        </button>
        <button onClick={() => setExpanded(!expanded)}
          className="p-1.5 rounded-lg hover:bg-surface-2 text-ink-4 hover:text-ink transition-colors"
          title={expanded ? "Collapse" : "Expand details"}>
          <Icon name={expanded ? "risk" : "info"} size={14} />
        </button>
      </div>

      {/* Loading / Error */}
      {loading && <p className="text-[11px] text-ink-3">Loading persistence status...</p>}
      {error && <p className="text-[11px] text-breach">{error}</p>}

      {status && (
        <>
          {/* Summary strip */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-center mb-3">
            <div>
              <p className="text-[11px] text-ink font-medium">{status.storage_mode.replace(/_/g, " ")}</p>
              <p className="text-[10px] text-ink-4">storage mode</p>
            </div>
            <div>
              <p className={`text-[11px] font-medium ${status.is_database_backed ? "text-pos" : "text-ink-3"}`}>{status.is_database_backed ? "Yes" : "No"}</p>
              <p className="text-[10px] text-ink-4">database backed</p>
            </div>
            <div>
              <p className={`text-[11px] font-medium ${status.is_persistent_volume_configured ? "text-pos" : "text-caution"}`}>{status.is_persistent_volume_configured ? "Yes" : "No"}</p>
              <p className="text-[10px] text-ink-4">persistent volume</p>
            </div>
            <div>
              <p className="text-[11px] text-ink font-medium">{status.deployment_environment}</p>
              <p className="text-[10px] text-ink-4">environment</p>
            </div>
            <div>
              <p className={`text-[11px] font-medium ${status.appears_containerized ? "text-caution" : "text-pos"}`}>{status.appears_containerized ? "Yes" : "No"}</p>
              <p className="text-[10px] text-ink-4">containerized</p>
            </div>
            <div>
              <p className="text-[10px] text-ink-4 font-mono truncate" title={status.storage_root}>{status.storage_root}</p>
              <p className="text-[10px] text-ink-4">storage root</p>
            </div>
          </div>

          {/* Warnings */}
          {status.warnings.length > 0 && (
            <div className="rounded-lg border border-caution/30 bg-caution/5 p-2.5 mb-3">
              {status.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 text-[11px] text-caution mb-1 last:mb-0">
                  <Icon name="alert-triangle" size={11} className="mt-0.5 shrink-0" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          )}

          {/* Recommended action */}
          {status.recommended_next_action && (
            <div className="flex items-start gap-2 text-[11px] text-ink-2 mb-3 p-2 rounded-lg bg-surface-2/60">
              <Icon name="info" size={11} className="mt-0.5 shrink-0 text-primary" />
              <span><strong className="text-ink">Recommended:</strong> {status.recommended_next_action}</span>
            </div>
          )}

          {/* Expanded details */}
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
            >
              {/* Registry statuses */}
              <div className="border-t border-line pt-3 mb-3">
                <h4 className="text-[12px] font-semibold text-ink mb-2">Registry Status</h4>
                {status.registry_statuses.map((reg) => (
                  <RegistryStatusRow key={reg.registry_name} reg={reg} />
                ))}
              </div>

              {/* Limitations */}
              {status.limitations.length > 0 && (
                <div className="border-t border-line pt-3 mb-3">
                  <h4 className="text-[12px] font-semibold text-ink mb-2">Limitations</h4>
                  <ul className="space-y-1">
                    {status.limitations.map((l, i) => (
                      <li key={i} className="flex items-start gap-2 text-[10px] text-ink-3">
                        <span className="text-ink-4 mt-0.5">•</span>
                        <span>{l}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Safety invariant */}
              <div className="border-t border-line pt-3">
                <div className="flex flex-wrap gap-1.5">
                  {[
                    { key: "research_only", label: "Research only" },
                    { key: "offline_only", label: "Offline only" },
                    { key: "no_production_influence", label: "No production influence" },
                  ].map(({ key, label }) => (
                    <span key={key} className={`inline-flex items-center px-2 py-0.5 rounded-md text-[9px] font-medium ${
                      (status as Record<string, unknown>)[key] ? "bg-pos/10 text-pos" : "bg-breach/10 text-breach"
                    }`}>{label}</span>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </>
      )}
    </GlassCard>
  );
}
