"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AssetSearchResult, searchAssets } from "@/services/api";

/**
 * Phase 20.5 — Add-asset dialog with ticker autocomplete.
 *
 * Fetches `searchAssets(q)` on each keystroke (debounced 200 ms). The
 * dropdown supports ↑/↓/Enter keyboard navigation; Escape closes the
 * dialog. Submission posts the SELECTED suggestion's ticker, not whatever
 * the user typed — this avoids accidentally submitting a free-text
 * ticker that doesn't exist in the assets table (which the backend
 * would 409 on anyway, but the inline UX is better).
 *
 * The parent owns the actual mutation; this dialog just resolves
 * (ticker_string | null) on submit/cancel.
 */
export function AddAssetDialog({
  open,
  busy,
  error,
  excludeTickers,
  onSubmit,
  onClose,
}: {
  open: boolean;
  busy: boolean;
  error: string | null;
  excludeTickers: string[];  // already-current members; greyed out in the list
  onSubmit: (ticker: string) => void;
  onClose: () => void;
}) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<AssetSearchResult[]>([]);
  const [highlighted, setHighlighted] = useState(0);
  const [searching, setSearching] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Debounced search — 200 ms feels live without spamming the API.
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setSearching(true);
    const t = setTimeout(async () => {
      try {
        const res = await searchAssets(q, 12);
        if (!cancelled) {
          setResults(res.data);
          setHighlighted(0);
        }
      } finally {
        if (!cancelled) setSearching(false);
      }
    }, 200);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [q, open]);

  // Focus the input + reset state when the dialog opens.
  useEffect(() => {
    if (!open) return;
    setQ("");
    setHighlighted(0);
    const t = setTimeout(() => inputRef.current?.focus(), 30);
    return () => clearTimeout(t);
  }, [open]);

  // Esc closes.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !busy) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  const excludeSet = new Set(excludeTickers.map((t) => t.toUpperCase()));
  const eligible = results.filter((r) => !excludeSet.has(r.ticker.toUpperCase()));

  const submitChoice = useCallback(() => {
    const choice = eligible[highlighted];
    if (choice && !busy) onSubmit(choice.ticker);
  }, [eligible, highlighted, busy, onSubmit]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlighted((h) => Math.min(h + 1, Math.max(eligible.length - 1, 0)));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlighted((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      submitChoice();
    }
  }, [eligible.length, submitChoice]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40"
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-asset-title"
      onClick={(e) => { if (e.target === e.currentTarget && !busy) onClose(); }}
    >
      <div className="bg-surface border border-line rounded-lg shadow-lg w-full max-w-md p-pad">
        <h2 id="add-asset-title" className="text-[15px] font-semibold text-ink mb-1">
          Add asset
        </h2>
        <p className="text-[12px] text-ink-3 mb-3">
          Search by ticker or company name. Only assets already ingested are eligible.
        </p>

        <label htmlFor="add-asset-search" className="block text-[12px] text-ink-2 mb-1">
          Ticker or name
        </label>
        <input
          id="add-asset-search"
          ref={inputRef}
          type="text"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={64}
          autoComplete="off"
          className="w-full bg-surface-2 border border-line rounded-md px-3 py-2 text-body text-ink focus:outline-none focus:border-primary"
          placeholder="AAPL, MSFT, Microsoft, …"
          aria-autocomplete="list"
          aria-controls="add-asset-results"
          aria-expanded={results.length > 0}
        />

        <ul
          id="add-asset-results"
          role="listbox"
          aria-label="Matching assets"
          className="mt-2 max-h-64 overflow-y-auto border border-line rounded-md divide-y divide-line"
        >
          {searching && (
            <li className="px-3 py-2 text-[12px] text-ink-4">Searching…</li>
          )}
          {!searching && eligible.length === 0 && (
            <li className="px-3 py-2 text-[12px] text-ink-4">
              {q.trim()
                ? "No matches outside the current universe."
                : "Start typing to see suggestions."}
            </li>
          )}
          {!searching && eligible.map((a, i) => (
            <li
              key={a.asset_id}
              role="option"
              aria-selected={i === highlighted}
              onMouseEnter={() => setHighlighted(i)}
              onClick={() => onSubmit(a.ticker)}
              className={`px-3 py-2 cursor-pointer flex items-baseline gap-2 ${
                i === highlighted ? "bg-primary-soft" : ""
              }`}
            >
              <span className="font-mono text-[12.5px] text-ink font-medium">{a.ticker}</span>
              <span className="text-[11.5px] text-ink-3 truncate">{a.name}</span>
              {a.sector && (
                <span className="ml-auto text-[10.5px] text-ink-4">{a.sector}</span>
              )}
            </li>
          ))}
        </ul>

        {error && (
          <div className="mt-3 text-body-sm text-breach-soft-ink bg-breach-soft border border-breach-soft-ink/20 rounded-md p-2" role="alert">
            {error}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-3">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="px-3 py-1.5 rounded-md text-[12px] text-ink-2 hover:bg-surface-3 disabled:opacity-40"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={submitChoice}
            disabled={busy || eligible.length === 0}
            className="px-3 py-1.5 rounded-md bg-primary text-primary-ink text-[12px] font-medium hover:opacity-90 disabled:opacity-40"
          >
            {busy ? "Adding…" : "Add to universe"}
          </button>
        </div>
      </div>
    </div>
  );
}
