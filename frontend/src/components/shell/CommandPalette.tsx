"use client";

/**
 * Phase 14.3 — Global command palette.
 *
 * Opens via ⌘K / Ctrl+K (or the TopBar search trigger). Searches:
 *   - Routes — the seven product-area landings and their sub-routes
 *   - Tickers — when the query parses as a valid symbol, deep-link
 *     to /research/[ticker]
 *   - Operator analyses — when the user is signed in and the
 *     analyses endpoint returns
 *   - Recent searches — read from localStorage; populated when a
 *     pick is committed
 *
 * Categories explicitly NOT searched (with documented reasons in
 * lib/search.ts §"Categories that are NOT included"):
 *   - Recommendations: no list endpoint typed on the frontend
 *   - Help articles: no runtime MDX index
 *
 * Accessibility:
 *   - role="dialog" + aria-modal + aria-labelledby on the panel
 *   - Backdrop click closes
 *   - Esc closes
 *   - Arrow keys move selection; Enter activates; Tab cycles
 *     between query input and result list
 *   - Focus restored to the trigger on close
 *
 * Owned by skills:
 *   - finrlx-ux-redesign-director (rule 8 one palette, rule 3
 *     source-grounded — every result describes its source)
 *   - finrlx-ai-ux-governance (palette is NOT an AI prompt;
 *     non-empty empty-state)
 *   - vercel-web-design-guidelines-mirror (a11y dialog semantics)
 */
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Icon } from "@/components/icons/Icon";
import {
  loadRecent,
  recordRecent,
  clearRecent,
  searchRoutes,
  searchTicker,
  searchOperatorAnalyses,
  type SearchResult,
} from "@/lib/search";
import { listOperatorAnalyses, type OperatorAnalysis } from "@/services/operatorApi";
import { useAuth } from "@/contexts/AuthContext";

interface Props {
  open: boolean;
  onClose: () => void;
}

interface ResultGroup {
  key: string;
  label: string;
  results: SearchResult[];
}

export function CommandPalette({ open, onClose }: Props) {
  const router = useRouter();
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [analyses, setAnalyses] = useState<OperatorAnalysis[]>([]);
  const [recent, setRecent] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const dialogRef = useRef<HTMLDivElement | null>(null);

  // Load recents + operator analyses when the palette opens. Operator
  // analyses are fetched lazily and capped to keep payload modest; this
  // is a search index, not a list view.
  useEffect(() => {
    if (!open) return;
    setRecent(loadRecent());
    if (!user) {
      setAnalyses([]);
      return;
    }
    let cancelled = false;
    listOperatorAnalyses({ limit: 50 })
      .then((res) => {
        if (!cancelled) setAnalyses(res.data);
      })
      .catch(() => {
        // Honest empty: if the call fails (network, auth, backend),
        // we simply skip the operator category. No misleading error.
        if (!cancelled) setAnalyses([]);
      });
    return () => {
      cancelled = true;
    };
  }, [open, user]);

  // Auto-focus the input on open. The 0ms timeout lets the dialog
  // mount before we steal focus.
  useEffect(() => {
    if (!open) return;
    const t = window.setTimeout(() => inputRef.current?.focus(), 0);
    return () => window.clearTimeout(t);
  }, [open]);

  // Reset state when the dialog closes so the next open starts clean.
  useEffect(() => {
    if (open) return;
    setQuery("");
    setActiveIndex(0);
  }, [open]);

  // ── Compose result groups ───────────────────────────────────────
  const groups = useMemo<ResultGroup[]>(() => {
    const out: ResultGroup[] = [];

    if (!query.trim() && recent.length > 0) {
      out.push({
        key: "recent",
        label: "Recent searches",
        results: recent.map((q) => ({
          id: `recent:${q}`,
          category: "recent" as const,
          label: q,
          description: "Repeat search",
          href: "#",
          icon: "clock",
        })),
      });
    }

    const ticker = searchTicker(query);
    if (ticker) {
      out.push({ key: "ticker", label: "Ticker", results: [ticker] });
    }

    const routes = searchRoutes(query);
    if (routes.length > 0) {
      out.push({
        key: "routes",
        label: query.trim() ? "Routes" : "Jump to",
        results: routes,
      });
    }

    if (query.trim() && analyses.length > 0) {
      const operatorResults = searchOperatorAnalyses(analyses, query);
      if (operatorResults.length > 0) {
        out.push({ key: "operator", label: "Operator analyses", results: operatorResults });
      }
    }

    return out;
  }, [query, recent, analyses]);

  const flatResults = useMemo(() => groups.flatMap((g) => g.results), [groups]);

  // Reset selection whenever the result list changes shape.
  useEffect(() => {
    setActiveIndex(0);
  }, [groups.length, flatResults.length]);

  const activate = useCallback(
    (result: SearchResult) => {
      if (result.category === "recent") {
        setQuery(result.label);
        return;
      }
      recordRecent(query || result.label);
      onClose();
      router.push(result.href);
    },
    [onClose, query, router],
  );

  // ── Keyboard navigation ────────────────────────────────────────
  const onKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        onClose();
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, Math.max(flatResults.length - 1, 0)));
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        const result = flatResults[activeIndex];
        if (result) activate(result);
        return;
      }
    },
    [activate, flatResults, activeIndex, onClose],
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-ink/40 backdrop-blur-sm"
      onMouseDown={(e) => {
        // Click on the backdrop closes; clicks inside the dialog do not.
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="command-palette-heading"
        onKeyDown={onKeyDown}
        className="w-full max-w-[640px] bg-surface border border-line rounded-xl shadow-lg overflow-hidden"
      >
        {/* Input row */}
        <div className="flex items-center gap-3 px-4 h-14 border-b border-line">
          <Icon name="search" size={20} className="text-ink-3 shrink-0" />
          <label htmlFor="command-palette-input" id="command-palette-heading" className="sr-only">
            Search FINRLX
          </label>
          <input
            ref={inputRef}
            id="command-palette-input"
            type="text"
            autoComplete="off"
            spellCheck={false}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search routes, tickers, operator notes…"
            className="flex-1 bg-transparent border-0 outline-none text-body text-ink placeholder:text-ink-4"
          />
          <kbd className="hidden sm:inline-flex items-center text-meta font-mono text-ink-2 bg-surface-3 px-1.5 py-0.5 rounded">
            Esc
          </kbd>
        </div>

        {/* Results */}
        <div
          role="listbox"
          aria-label="Search results"
          className="max-h-[60vh] overflow-y-auto"
        >
          {groups.length === 0 ? (
            <EmptyState query={query} />
          ) : (
            groups.map((group) => (
              <Group
                key={group.key}
                label={group.label}
                showClear={group.key === "recent"}
                onClear={() => {
                  clearRecent();
                  setRecent([]);
                }}
              >
                {group.results.map((result) => {
                  const flatIndex = flatResults.findIndex((r) => r.id === result.id);
                  const active = flatIndex === activeIndex;
                  return (
                    <ResultRow
                      key={result.id}
                      result={result}
                      active={active}
                      onMouseEnter={() => setActiveIndex(flatIndex)}
                      onClick={() => activate(result)}
                    />
                  );
                })}
              </Group>
            ))
          )}
        </div>

        {/* Hint footer */}
        <div className="flex items-center justify-between gap-3 px-4 h-10 bg-surface-2 border-t border-line text-meta text-ink-4">
          <div className="flex items-center gap-3">
            <span>
              <kbd className="font-mono">↑↓</kbd> navigate
            </span>
            <span>
              <kbd className="font-mono">↵</kbd> open
            </span>
            <span>
              <kbd className="font-mono">Esc</kbd> close
            </span>
          </div>
          <span className="font-mono">FINRLX search</span>
        </div>
      </div>
    </div>
  );
}

function Group({
  label,
  showClear,
  onClear,
  children,
}: {
  label: string;
  showClear?: boolean;
  onClear?: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="py-1">
      <div className="flex items-center justify-between px-4 pt-2 pb-1">
        <p className="text-meta uppercase tracking-wider text-ink-4 font-semibold">{label}</p>
        {showClear && onClear && (
          <button
            type="button"
            onClick={onClear}
            className="text-meta text-ink-3 hover:text-ink-2 transition-colors"
          >
            Clear
          </button>
        )}
      </div>
      <div>{children}</div>
    </div>
  );
}

function ResultRow({
  result,
  active,
  onMouseEnter,
  onClick,
}: {
  result: SearchResult;
  active: boolean;
  onMouseEnter: () => void;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      role="option"
      aria-selected={active}
      onMouseEnter={onMouseEnter}
      onClick={onClick}
      className={`flex items-center gap-3 w-full text-left px-4 min-h-11 transition-colors ${
        active
          ? "bg-primary-soft text-primary-soft-ink"
          : "text-ink-2 hover:bg-surface-3"
      }`}
    >
      <Icon
        name={result.icon ?? "search"}
        size={16}
        className={active ? "text-primary" : "text-ink-3"}
      />
      <div className="flex-1 min-w-0">
        <p className="text-body-sm truncate">{result.label}</p>
        {result.description && (
          <p className="text-meta text-ink-4 truncate">{result.description}</p>
        )}
      </div>
      <span
        className={`text-meta font-mono uppercase tracking-wider ${
          active ? "text-primary-soft-ink/70" : "text-ink-4"
        }`}
      >
        {result.category}
      </span>
    </button>
  );
}

function EmptyState({ query }: { query: string }) {
  const trimmed = query.trim();
  return (
    <div className="px-4 py-8 text-center">
      <Icon name="search" size={20} className="text-ink-4 mx-auto" />
      <p className="text-body-sm text-ink-2 mt-2">
        {trimmed ? `No matches for "${trimmed}"` : "Start typing"}
      </p>
      <p className="text-caption text-ink-4 mt-1 max-w-sm mx-auto leading-snug">
        Search FINRLX routes, ticker symbols (e.g. NVDA), and operator analyses.
        AI prompts live inside the operator console, not the palette.
      </p>
    </div>
  );
}
