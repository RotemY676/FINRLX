"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Icon } from "@/components/icons/Icon";
import { PageError } from "@/components/feedback/PageError";
import { PageLoading } from "@/components/feedback/PageLoading";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import {
  createOperatorAnalysis,
  deleteOperatorAnalysis,
  listOperatorAnalyses,
  type OperatorAnalysis,
  type OperatorAnalysisSource,
  type OperatorAnalysisSurface,
} from "@/services/operatorApi";

const SURFACE_OPTIONS: OperatorAnalysisSurface[] = ["decision", "replay", "news", "manual"];
const SOURCE_OPTIONS: OperatorAnalysisSource[] = ["gpt", "claude", "other"];

export default function OperatorConsolePage() {
  // useSearchParams must be wrapped in a Suspense boundary so the static
  // export step does not bail. The inner component holds all the logic.
  return (
    <Suspense fallback={<PageLoading label="Loading operator console..." />}>
      <OperatorConsoleInner />
    </Suspense>
  );
}

function OperatorConsoleInner() {
  const { flags, isLoading: flagsLoading } = useFeatureFlags();
  const params = useSearchParams();
  const recParam = params?.get("rec") ?? null;
  const surfaceParam = (params?.get("surface") as OperatorAnalysisSurface) ?? "decision";
  // Phase 11: home assistant prompts deep-link with a `prompt` query
  // param so the operator lands with the question already typed in.
  const promptParam = params?.get("prompt") ?? "";

  const [surface, setSurface] = useState<OperatorAnalysisSurface>(
    SURFACE_OPTIONS.includes(surfaceParam) ? surfaceParam : "decision",
  );
  const [source, setSource] = useState<OperatorAnalysisSource>("gpt");
  const [recommendationId, setRecommendationId] = useState<string>(recParam ?? "");
  const [response, setResponse] = useState("");
  const [prompt, setPrompt] = useState(promptParam);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [analyses, setAnalyses] = useState<OperatorAnalysis[]>([]);
  const [analysesLoading, setAnalysesLoading] = useState(true);

  useEffect(() => {
    if (recParam && !recommendationId) setRecommendationId(recParam);
  }, [recParam, recommendationId]);

  const reload = useCallback(async () => {
    setAnalysesLoading(true);
    try {
      const res = await listOperatorAnalyses({ limit: 100 });
      setAnalyses(res.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analyses");
    } finally {
      setAnalysesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!flagsLoading && flags.operator_console) {
      void reload();
    }
  }, [flagsLoading, flags.operator_console, reload]);

  const onSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!response.trim()) {
        setError("Response is required.");
        return;
      }
      setSaving(true);
      setError(null);
      try {
        await createOperatorAnalysis({
          surface,
          source,
          recommendation_id: recommendationId.trim() || null,
          prompt: prompt.trim() || null,
          response: response.trim(),
          note: note.trim() || null,
        });
        setSavedMsg("Saved");
        setResponse("");
        setPrompt("");
        setNote("");
        await reload();
        window.setTimeout(() => setSavedMsg(null), 2000);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Save failed");
      } finally {
        setSaving(false);
      }
    },
    [surface, source, recommendationId, prompt, response, note, reload],
  );

  const onDelete = useCallback(
    async (id: string) => {
      if (!confirm("Delete this analysis? The audit-trail entry is removed permanently.")) return;
      try {
        await deleteOperatorAnalysis(id);
        await reload();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Delete failed");
      }
    },
    [reload],
  );

  if (flagsLoading) return <PageLoading label="Loading operator console..." />;
  if (!flags.operator_console) {
    return (
      <PageError
        title="Operator console disabled"
        message="The operator console is not enabled for this environment."
        hint="Set FEATURE_OPERATOR_CONSOLE=true in the backend environment."
      />
    );
  }

  return (
    <div className="space-y-gap max-w-[1100px]">
      <div>
        <h1 className="text-[20px] font-semibold text-ink">Operator console</h1>
        <p className="text-[12.5px] text-ink-3 mt-1 max-w-2xl">
          Single-operator workbench. Copy structured page context from Decision, Replay, or News into ChatGPT or Claude (see the &ldquo;Copy LLM context&rdquo; buttons on those pages). Paste the response back here to archive it linked to the recommendation. Stored analyses surface on the Replay page as Analyst notes.
        </p>
      </div>

      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <h2 className="text-[14px] font-semibold text-ink mb-3 flex items-center gap-2">
          <Icon name="paper" size={14} />
          Archive an LLM response
        </h2>
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <label className="block">
              <span className="block text-[11px] uppercase tracking-wider text-ink-4 mb-1 font-semibold">Surface</span>
              <select
                value={surface}
                onChange={(e) => setSurface(e.target.value as OperatorAnalysisSurface)}
                className="w-full px-2 py-1.5 rounded-md bg-surface-2 border border-line text-[13px] text-ink"
              >
                {SURFACE_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="block text-[11px] uppercase tracking-wider text-ink-4 mb-1 font-semibold">LLM source</span>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value as OperatorAnalysisSource)}
                className="w-full px-2 py-1.5 rounded-md bg-surface-2 border border-line text-[13px] text-ink"
              >
                {SOURCE_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s.toUpperCase()}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="block text-[11px] uppercase tracking-wider text-ink-4 mb-1 font-semibold">Recommendation ID (optional)</span>
              <input
                type="text"
                value={recommendationId}
                onChange={(e) => setRecommendationId(e.target.value)}
                placeholder="e.g. e3fcaa53-9e5f-..."
                className="w-full px-2 py-1.5 rounded-md bg-surface-2 border border-line text-[13px] text-ink font-mono"
              />
            </label>
          </div>
          <label className="block">
            <span className="block text-[11px] uppercase tracking-wider text-ink-4 mb-1 font-semibold">Prompt you used (optional)</span>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
              placeholder="What you asked the LLM after pasting the context — useful for reproducing later."
              className="w-full px-2 py-1.5 rounded-md bg-surface-2 border border-line text-[13px] text-ink resize-y"
            />
          </label>
          <label className="block">
            <span className="block text-[11px] uppercase tracking-wider text-ink-4 mb-1 font-semibold">LLM response *</span>
            <textarea
              value={response}
              onChange={(e) => setResponse(e.target.value)}
              rows={10}
              required
              placeholder="Paste the response from ChatGPT / Claude here."
              className="w-full px-2 py-1.5 rounded-md bg-surface-2 border border-line text-[13px] text-ink resize-y"
            />
          </label>
          <label className="block">
            <span className="block text-[11px] uppercase tracking-wider text-ink-4 mb-1 font-semibold">Your note (optional)</span>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="One-line context: e.g. 'sanity-check before promotion'."
              className="w-full px-2 py-1.5 rounded-md bg-surface-2 border border-line text-[13px] text-ink"
            />
          </label>
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={saving || !response.trim()}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-primary text-primary-ink text-[13px] font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              <Icon name="check" size={14} />
              {saving ? "Saving…" : "Archive analysis"}
            </button>
            {savedMsg && <span role="status" className="text-[12px] text-pos-soft-ink">{savedMsg}</span>}
            {error && <span role="alert" className="text-[12px] text-breach-soft-ink">{error}</span>}
          </div>
        </form>
      </section>

      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[14px] font-semibold text-ink flex items-center gap-2">
            <Icon name="history" size={14} />
            Archived analyses
          </h2>
          <button
            type="button"
            onClick={reload}
            className="text-[12px] text-ink-3 hover:text-ink"
          >
            Refresh
          </button>
        </div>
        {analysesLoading ? (
          <p className="text-[12.5px] text-ink-3">Loading…</p>
        ) : analyses.length === 0 ? (
          <p className="text-[12.5px] text-ink-3">
            No archived analyses yet. Copy context from a page using the &ldquo;Copy LLM context&rdquo; button, paste into ChatGPT / Claude, then paste the response above.
          </p>
        ) : (
          <ul className="space-y-3" role="list">
            {analyses.map((a) => (
              <li key={a.id} className="rounded-md border border-line bg-surface-2 p-3">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2 text-[11px] text-ink-3">
                    <span className="font-mono uppercase">{a.source}</span>
                    <span>·</span>
                    <span>{a.surface}</span>
                    {a.recommendation_id && (
                      <>
                        <span>·</span>
                        <Link
                          href={`/replay?id=${a.recommendation_id}`}
                          className="text-primary hover:underline font-mono"
                        >
                          {a.recommendation_id.slice(0, 8)}…
                        </Link>
                      </>
                    )}
                    <span>·</span>
                    <span>{a.created_at?.slice(0, 16).replace("T", " ")}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => onDelete(a.id)}
                    className="text-[11px] text-ink-4 hover:text-breach"
                  >
                    Delete
                  </button>
                </div>
                {a.note && <p className="text-[12.5px] text-ink-2 mb-1.5 italic">{a.note}</p>}
                {a.prompt && (
                  <details className="mb-1">
                    <summary className="cursor-pointer text-[11px] text-ink-4">Prompt</summary>
                    <pre className="mt-1 whitespace-pre-wrap text-[12px] text-ink-3 bg-surface p-2 rounded font-mono">{a.prompt}</pre>
                  </details>
                )}
                <pre className="whitespace-pre-wrap text-[13px] text-ink leading-relaxed font-sans">{a.response}</pre>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
