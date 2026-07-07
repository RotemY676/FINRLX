"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Icon } from "@/components/icons/Icon";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import {
  deleteOperatorAnalysis,
  listOperatorAnalyses,
  type OperatorAnalysis,
} from "@/services/operatorApi";

/**
 * Surfaces archived LLM analyses (from /operator pasteback) linked to a
 * specific recommendation. Renders nothing when:
 *  - the operator_console feature flag is off, or
 *  - no analyses are archived for this recommendation.
 *
 * Auth-required — fetch silently fails when unauthenticated.
 */
export function AnalystNotesPanel({
  recommendationId,
}: {
  recommendationId: string;
}) {
  const { flags } = useFeatureFlags();
  const [analyses, setAnalyses] = useState<OperatorAnalysis[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!recommendationId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await listOperatorAnalyses({ recommendation_id: recommendationId });
      setAnalyses(res.data);
    } catch (e) {
      // Silently swallow auth errors — the panel just won't render in that case.
      // Surface real errors so the operator can see them.
      if (e instanceof Error && /401|403/.test(e.message)) {
        setAnalyses([]);
      } else {
        setError(e instanceof Error ? e.message : "Failed to load analyst notes");
      }
    } finally {
      setLoading(false);
    }
  }, [recommendationId]);

  useEffect(() => {
    if (flags.operator_console) void load();
  }, [flags.operator_console, load]);

  const onDelete = useCallback(
    async (id: string) => {
      if (!confirm("Delete this analysis from the audit trail?")) return;
      try {
        await deleteOperatorAnalysis(id);
        await load();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Delete failed");
      }
    },
    [load],
  );

  if (!flags.operator_console) return null;
  if (loading) return null;
  if (analyses.length === 0 && !error) return null;

  return (
    <section
      aria-labelledby="analyst-notes-heading"
      className="bg-surface border border-line rounded-lg shadow-sm p-pad"
    >
      <div className="flex items-center justify-between mb-3 gap-2">
        <h3
          id="analyst-notes-heading"
          className="text-[13px] font-semibold text-ink flex items-center gap-2"
        >
          <Icon name="sparkle" size={14} />
          Analyst notes
          <span className="text-[11px] text-ink-4 font-normal">
            ({analyses.length} archived LLM analys{analyses.length === 1 ? "is" : "es"})
          </span>
        </h3>
        <Link
          href={`/pro/operator?rec=${recommendationId}&surface=replay`}
          className="text-[12px] text-primary hover:underline"
        >
          Add note →
        </Link>
      </div>
      {error && (
        <p role="alert" className="text-[12px] text-breach-soft-ink mb-2">
          {error}
        </p>
      )}
      <ul role="list" className="space-y-3">
        {analyses.map((a) => (
          <li
            key={a.id}
            className="rounded-md border border-line bg-surface-2 p-3"
          >
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <div className="flex items-center gap-2 text-[11px] text-ink-3">
                <span className="font-mono uppercase font-semibold">{a.source}</span>
                <span>·</span>
                <span className="font-mono">{a.surface}</span>
                <span>·</span>
                <span>{a.created_at?.slice(0, 16).replace("T", " ")}</span>
              </div>
              <button
                type="button"
                onClick={() => onDelete(a.id)}
                className="text-[11px] text-ink-4 hover:text-breach"
                title="Delete this analyst note"
              >
                Delete
              </button>
            </div>
            {a.note && (
              <p className="text-[12.5px] text-ink-2 italic mb-1.5">{a.note}</p>
            )}
            {a.prompt && (
              <details className="mb-1.5">
                <summary className="cursor-pointer text-[11px] text-ink-4 hover:text-ink-2">
                  Prompt
                </summary>
                <pre className="mt-1 whitespace-pre-wrap text-[12px] text-ink-3 bg-surface p-2 rounded font-mono">
                  {a.prompt}
                </pre>
              </details>
            )}
            <pre className="whitespace-pre-wrap text-[13px] text-ink leading-relaxed font-sans">
              {a.response}
            </pre>
          </li>
        ))}
      </ul>
    </section>
  );
}
