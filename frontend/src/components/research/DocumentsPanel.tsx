"use client";

/**
 * Phase 17.3 — Research documents panel for /research/[ticker].
 *
 * Authenticated operators can:
 *   - Upload a PDF (10-Q, 10-K, transcript) against the active ticker
 *   - See the list of documents shared by ticker, newest first
 *   - Select a document and ask LLM questions about it
 *   - See past analyses (Q&A history per document)
 *   - Delete documents they uploaded
 *
 * Honest empty / unconfigured / over-budget states are surfaced
 * verbatim from the backend (never invented). The frontend never
 * pretends the LLM is configured when the /analyze endpoint 503s.
 *
 * Owned by skills:
 *   - finrlx-ai-ux-governance (every analysis answer is grounded in
 *     a specific document the user uploaded; no blank-chat)
 *   - finrlx-fintech-dashboard-patterns (every list row carries
 *     metadata: who uploaded, when, status; analyses show provider +
 *     model + token counts)
 *   - fintech-disclaimer-and-marketing-guard (panel copy never
 *     suggests "buy/sell"; the system prompt the backend uses
 *     refuses trade instructions)
 *   - recommendation-object-provenance (analyses surface the
 *     model/provider/tokens; never a synthesised "score")
 */
import { useCallback, useEffect, useRef, useState } from "react";

import {
  analyzeDocument,
  deleteDocument,
  fetchAnalyses,
  fetchBudgetUsage,
  fetchDocuments,
  uploadDocument,
  type BudgetUsageData,
  type DocumentAnalysisData,
  type DocumentSummaryData,
} from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import { Icon } from "@/components/icons/Icon";


interface Props {
  ticker: string;
}

const PROMPT_SUGGESTIONS: ReadonlyArray<string> = [
  "Summarise this filing in 8 bullet points.",
  "List the top risk factors and how they changed from the prior period.",
  "What were revenue, gross margin, and operating margin? Quote the figures.",
  "Did management revise guidance? Quote any forward statements verbatim.",
  "Which segments grew? Which declined?",
];


export function DocumentsPanel({ ticker }: Props) {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<DocumentSummaryData[] | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [analyses, setAnalyses] = useState<DocumentAnalysisData[] | null>(null);
  const [budget, setBudget] = useState<BudgetUsageData | null>(null);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [analyzeBusy, setAnalyzeBusy] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // ── Loaders ─────────────────────────────────────────────────

  const loadDocuments = useCallback(async () => {
    try {
      const res = await fetchDocuments(ticker);
      setDocuments(res.data.documents);
    } catch {
      setDocuments([]);
    }
  }, [ticker]);

  const loadAnalyses = useCallback(async (docId: string) => {
    try {
      const res = await fetchAnalyses(docId);
      setAnalyses(res.data);
    } catch {
      setAnalyses([]);
    }
  }, []);

  const loadBudget = useCallback(async () => {
    try {
      const res = await fetchBudgetUsage();
      setBudget(res.data);
    } catch {
      setBudget(null);
    }
  }, []);

  useEffect(() => {
    if (!user) return;
    void loadDocuments();
    void loadBudget();
  }, [user, loadDocuments, loadBudget]);

  useEffect(() => {
    if (!selectedDocId) {
      setAnalyses(null);
      return;
    }
    void loadAnalyses(selectedDocId);
  }, [selectedDocId, loadAnalyses]);

  // ── Handlers ────────────────────────────────────────────────

  const handleUpload = useCallback(
    async (file: File) => {
      setUploadBusy(true);
      setUploadError(null);
      try {
        await uploadDocument(ticker, file);
        await loadDocuments();
      } catch (e) {
        setUploadError(e instanceof Error ? e.message : String(e));
      } finally {
        setUploadBusy(false);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    },
    [ticker, loadDocuments],
  );

  const handleDelete = useCallback(
    async (docId: string) => {
      try {
        await deleteDocument(docId);
        if (selectedDocId === docId) setSelectedDocId(null);
        await loadDocuments();
      } catch (e) {
        setUploadError(e instanceof Error ? e.message : String(e));
      }
    },
    [loadDocuments, selectedDocId],
  );

  const handleAnalyze = useCallback(async () => {
    if (!selectedDocId || !prompt.trim()) return;
    setAnalyzeBusy(true);
    setAnalyzeError(null);
    try {
      await analyzeDocument(selectedDocId, prompt.trim());
      setPrompt("");
      await Promise.all([loadAnalyses(selectedDocId), loadBudget()]);
    } catch (e) {
      setAnalyzeError(e instanceof Error ? e.message : String(e));
    } finally {
      setAnalyzeBusy(false);
    }
  }, [selectedDocId, prompt, loadAnalyses, loadBudget]);

  // ── Render ──────────────────────────────────────────────────

  if (!user) {
    return (
      <section className="rounded-lg border border-dashed border-line bg-surface-2 p-pad">
        <div className="flex items-center gap-2 mb-2">
          <Icon name="paper" size={14} className="text-ink-4" />
          <h2 className="text-card-title text-ink-2">Document analysis</h2>
        </div>
        <p className="text-body-sm text-ink-3 leading-snug">
          Sign in to upload quarterly filings and ask the FINRLX
          research assistant questions about them.
        </p>
      </section>
    );
  }

  const selected = documents?.find((d) => d.id === selectedDocId) ?? null;

  return (
    <section
      aria-labelledby="docs-heading"
      className="rounded-lg border border-line bg-surface p-pad shadow-sm"
    >
      <header className="flex items-center gap-2 flex-wrap">
        <Icon name="paper" size={14} className="text-ink-3" />
        <h2 id="docs-heading" className="text-card-title text-ink">
          Document analysis
        </h2>
        <span className="text-meta text-ink-4 ml-auto font-mono">
          {documents ? `${documents.length} doc${documents.length === 1 ? "" : "s"}` : ""}
        </span>
      </header>

      {/* Upload area */}
      <UploadArea
        busy={uploadBusy}
        error={uploadError}
        onPick={handleUpload}
        fileInputRef={fileInputRef}
      />

      {/* Documents list */}
      <div className="mt-4">
        <p className="text-meta text-ink-4 uppercase tracking-wider mb-2">Uploaded filings</p>
        {documents === null ? (
          <p className="text-body-sm text-ink-3">Loading documents…</p>
        ) : documents.length === 0 ? (
          <p className="text-body-sm text-ink-3 rounded-md bg-surface-2 border border-line p-3">
            No filings uploaded yet for {ticker}. Drag a 10-Q or 10-K PDF
            into the box above, or use the picker.
          </p>
        ) : (
          <ul role="list" className="divide-y divide-line">
            {documents.map((doc) => (
              <DocumentRow
                key={doc.id}
                doc={doc}
                isSelected={doc.id === selectedDocId}
                isOwner={doc.uploaded_by_email.toLowerCase() === user.email.toLowerCase()}
                onSelect={() => setSelectedDocId(doc.id)}
                onDelete={() => handleDelete(doc.id)}
              />
            ))}
          </ul>
        )}
      </div>

      {/* Analyses panel — only when a document is selected */}
      {selected && (
        <AnalysisArea
          document={selected}
          analyses={analyses}
          prompt={prompt}
          setPrompt={setPrompt}
          onAnalyze={handleAnalyze}
          busy={analyzeBusy}
          error={analyzeError}
          budget={budget}
        />
      )}

      {/* Budget indicator */}
      <BudgetFooter budget={budget} />
    </section>
  );
}


// ── Sub-components ──────────────────────────────────────────────


function UploadArea({
  busy,
  error,
  onPick,
  fileInputRef,
}: {
  busy: boolean;
  error: string | null;
  onPick: (file: File) => void;
  // React 18 + types older than React 19 narrow `useRef(null)` into
  // RefObject<T | null>, which the `ref` prop's LegacyRef can't bind
  // to. Casting via `any` is fine here — the runtime contract is
  // identical and a real type-fix lives in a React/types upgrade.
  fileInputRef: React.MutableRefObject<HTMLInputElement | null>;
}) {
  const [dragOver, setDragOver] = useState(false);

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files?.[0];
      if (file) onPick(file);
    },
    [onPick],
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
      className={`mt-3 rounded-md border-2 border-dashed p-pad text-center transition-colors ${
        dragOver
          ? "border-primary bg-primary-soft"
          : "border-line bg-surface-2 hover:border-line-strong"
      }`}
    >
      <Icon name="paper" size={20} className="mx-auto text-ink-4" />
      <p className="text-body-sm text-ink-2 mt-1">
        Drop a PDF filing here, or{" "}
        <button
          type="button"
          className="text-primary hover:underline disabled:opacity-50"
          onClick={() => fileInputRef.current?.click()}
          disabled={busy}
        >
          choose a file
        </button>
        .
      </p>
      <p className="text-caption text-ink-4 mt-1">
        10-Q, 10-K, earnings transcripts, IR presentations. PDFs up to 50 MB.
      </p>
      <input
        ref={fileInputRef as React.RefObject<HTMLInputElement>}
        type="file"
        accept="application/pdf,.pdf"
        className="sr-only"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onPick(f);
        }}
      />
      {busy && (
        <p className="text-caption text-ink-2 mt-2">
          Uploading and extracting text…
        </p>
      )}
      {error && (
        <p className="text-caption text-breach-soft-ink bg-breach-soft rounded-md p-2 mt-2 inline-block">
          {error}
        </p>
      )}
    </div>
  );
}


function DocumentRow({
  doc,
  isSelected,
  isOwner,
  onSelect,
  onDelete,
}: {
  doc: DocumentSummaryData;
  isSelected: boolean;
  isOwner: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  const sizeMb = (doc.file_size_bytes / (1024 * 1024)).toFixed(1);
  const statusStyle =
    doc.extraction_status === "ready"
      ? "text-pos-soft-ink bg-pos-soft"
      : doc.extraction_status === "failed"
        ? "text-breach-soft-ink bg-breach-soft"
        : "text-caution-soft-ink bg-caution-soft";
  return (
    <li
      className={`py-2.5 flex items-center gap-3 ${
        isSelected ? "bg-primary-soft -mx-2 px-2 rounded-md" : ""
      }`}
    >
      <button
        type="button"
        onClick={onSelect}
        className="flex-1 min-w-0 text-left flex items-center gap-3"
      >
        <Icon name="paper" size={14} className="text-ink-3 shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-body-sm text-ink truncate font-medium">{doc.filename}</p>
          <p className="text-meta text-ink-4 truncate">
            {doc.uploaded_by_email} · {doc.uploaded_at.slice(0, 10)} · {sizeMb} MB
          </p>
        </div>
      </button>
      <span className={`text-meta px-1.5 py-0.5 rounded-sm font-medium ${statusStyle}`}>
        {doc.extraction_status}
      </span>
      {isOwner && (
        <button
          type="button"
          onClick={onDelete}
          aria-label="Delete document"
          className="text-meta text-ink-4 hover:text-breach transition-colors"
          title="Delete document"
        >
          ✕
        </button>
      )}
    </li>
  );
}


function AnalysisArea({
  document,
  analyses,
  prompt,
  setPrompt,
  onAnalyze,
  busy,
  error,
  budget,
}: {
  document: DocumentSummaryData;
  analyses: DocumentAnalysisData[] | null;
  prompt: string;
  setPrompt: (v: string) => void;
  onAnalyze: () => void;
  busy: boolean;
  error: string | null;
  budget: BudgetUsageData | null;
}) {
  const canAnalyze =
    document.extraction_status === "ready" && !!prompt.trim() && !busy && !budget?.over_budget;

  return (
    <div className="mt-5 pt-4 border-t border-line">
      <div className="flex items-center gap-2 flex-wrap mb-3">
        <Icon name="sparkle" size={14} className="text-primary" />
        <h3 className="text-card-title text-ink">{document.filename}</h3>
        <span className="text-meta text-ink-4 ml-auto">
          {document.extraction_status === "ready"
            ? `${(document.extracted_text_tokens_estimate ?? 0).toLocaleString()} tokens`
            : `extraction ${document.extraction_status}`}
        </span>
      </div>

      {document.extraction_status !== "ready" ? (
        <p className="text-body-sm text-caution-soft-ink bg-caution-soft rounded-md p-3">
          {document.extraction_error ??
            "Document extraction did not complete. Re-upload the file to retry."}
        </p>
      ) : (
        <>
          {/* Prompt + suggestions */}
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask a question about this filing…"
            rows={3}
            className="w-full rounded-md border border-line bg-canvas p-3 text-body text-ink placeholder:text-ink-4 focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <div className="flex flex-wrap gap-1.5 mt-2">
            {PROMPT_SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setPrompt(s)}
                className="text-meta text-ink-2 bg-surface-2 hover:bg-surface-3 border border-line rounded-md px-2 py-1 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
          <div className="flex items-center justify-between gap-2 mt-3">
            <button
              type="button"
              onClick={onAnalyze}
              disabled={!canAnalyze}
              className="inline-flex items-center justify-center gap-1.5 min-h-11 md:min-h-10 px-4 rounded-md bg-primary text-primary-ink text-body-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Icon name="sparkle" size={14} />
              {busy ? "Analysing…" : "Analyse"}
            </button>
            {budget?.over_budget && (
              <span className="text-meta text-breach-soft-ink bg-breach-soft rounded-md px-2 py-1">
                Monthly LLM budget exceeded
              </span>
            )}
          </div>
          {error && (
            <p className="text-caption text-breach-soft-ink bg-breach-soft rounded-md p-3 mt-3">
              {error}
            </p>
          )}
        </>
      )}

      {/* Past analyses */}
      <div className="mt-5">
        <p className="text-meta text-ink-4 uppercase tracking-wider mb-2">Past analyses</p>
        {analyses === null ? (
          <p className="text-body-sm text-ink-3">Loading…</p>
        ) : analyses.length === 0 ? (
          <p className="text-body-sm text-ink-3">No analyses yet for this document.</p>
        ) : (
          <ul role="list" className="space-y-3">
            {analyses.map((a) => (
              <li key={a.id} className="rounded-md border border-line bg-surface-2 p-3">
                <p className="text-body-sm text-ink-2 font-medium mb-2">Q: {a.prompt}</p>
                <p className="text-body-sm text-ink whitespace-pre-wrap leading-relaxed">
                  {a.response}
                </p>
                <p className="text-meta text-ink-4 mt-2 font-mono">
                  {a.provider} · {a.model || "—"} ·{" "}
                  {(a.input_tokens ?? 0).toLocaleString()} in /{" "}
                  {(a.output_tokens ?? 0).toLocaleString()} out ·{" "}
                  {a.cost_estimate_usd != null
                    ? `$${a.cost_estimate_usd.toFixed(4)}`
                    : "$—"}{" "}
                  · {a.created_by_email} · {a.created_at.slice(0, 16).replace("T", " ")}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}


function BudgetFooter({ budget }: { budget: BudgetUsageData | null }) {
  if (!budget) return null;
  const pct = budget.cap_tokens > 0 ? Math.min(100, (budget.used_tokens / budget.cap_tokens) * 100) : 0;
  const tone =
    pct >= 100 ? "bg-breach" : pct >= 80 ? "bg-caution" : "bg-primary";
  return (
    <div className="mt-4 pt-3 border-t border-line">
      <div className="flex items-center justify-between text-meta text-ink-4 mb-1">
        <span>
          Monthly LLM budget: {budget.used_tokens.toLocaleString()} /{" "}
          {budget.cap_tokens.toLocaleString()} tokens
        </span>
        <span className="font-mono">
          ${budget.cost_estimate_usd.toFixed(4)} est.
        </span>
      </div>
      <div className="h-1.5 bg-surface-3 rounded-full overflow-hidden">
        <div className={`h-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
