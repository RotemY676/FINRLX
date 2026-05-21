"use client";

import Link from "next/link";
import { useId, useMemo, useState } from "react";
import { Icon } from "@/components/icons/Icon";
import type { HelpSearchEntry } from "@/lib/help/search";

interface MatchResult {
  entry: HelpSearchEntry;
  score: number;
  excerpt: string;
}

const MAX_RESULTS = 10;

function scoreEntry(entry: HelpSearchEntry, terms: string[]): MatchResult | null {
  if (terms.length === 0) return null;
  const title = entry.title.toLowerCase();
  const summary = entry.summary.toLowerCase();
  const body = entry.body.toLowerCase();
  let score = 0;
  let firstMatchIdx = -1;
  for (const t of terms) {
    if (!t) continue;
    const inTitle = title.includes(t);
    const inSummary = summary.includes(t);
    const inBody = body.includes(t);
    if (!inTitle && !inSummary && !inBody) return null;
    if (inTitle) score += 10;
    if (inSummary) score += 5;
    if (inBody) score += 1;
    if (inBody && firstMatchIdx < 0) firstMatchIdx = body.indexOf(t);
  }
  // Boost shorter titles (more specific)
  score += Math.max(0, 4 - Math.floor(entry.title.length / 30));
  const excerpt = excerptAround(entry.body, firstMatchIdx);
  return { entry, score, excerpt };
}

function excerptAround(text: string, idx: number): string {
  if (idx < 0) return text.slice(0, 160);
  const start = Math.max(0, idx - 60);
  const end = Math.min(text.length, idx + 120);
  const prefix = start > 0 ? "…" : "";
  const suffix = end < text.length ? "…" : "";
  return prefix + text.slice(start, end) + suffix;
}

export function HelpSearch({ index }: { index: HelpSearchEntry[] }) {
  const [q, setQ] = useState("");
  const listId = useId();

  const results = useMemo<MatchResult[]>(() => {
    const query = q.trim().toLowerCase();
    if (query.length < 2) return [];
    const terms = query.split(/\s+/).filter((t) => t.length >= 2);
    if (terms.length === 0) return [];
    const matches: MatchResult[] = [];
    for (const entry of index) {
      const r = scoreEntry(entry, terms);
      if (r) matches.push(r);
    }
    return matches.sort((a, b) => b.score - a.score).slice(0, MAX_RESULTS);
  }, [q, index]);

  const showResults = q.trim().length >= 2;
  const empty = showResults && results.length === 0;

  return (
    <div className="my-4">
      <label
        htmlFor={`${listId}-input`}
        className="block text-[12px] font-semibold uppercase tracking-wider text-ink-4 mb-1.5"
      >
        Search Help
      </label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-4">
          <Icon name="search" size={14} />
        </span>
        <input
          id={`${listId}-input`}
          type="search"
          autoComplete="off"
          spellCheck={false}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search the Help center…"
          className="w-full pl-9 pr-3 py-2 rounded-md bg-surface-2 border border-line focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 text-[14px] text-ink placeholder:text-ink-4"
          aria-controls={showResults ? `${listId}-results` : undefined}
        />
      </div>
      {showResults && (
        <div
          id={`${listId}-results`}
          role="region"
          aria-label="Search results"
          className="mt-3 rounded-md border border-line bg-surface divide-y divide-line"
        >
          {empty ? (
            <p className="px-3 py-3 text-[13px] text-ink-3">
              No matches for <strong>{q}</strong>. Try a shorter query or check the{" "}
              <Link href="/help/glossary" className="text-primary hover:underline">
                glossary
              </Link>
              .
            </p>
          ) : (
            <ul className="m-0 p-0 list-none">
              {results.map(({ entry, excerpt }) => (
                <li key={entry.slug}>
                  <Link
                    href={entry.href}
                    className="block px-3 py-3 hover:bg-surface-2 transition-colors group"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-[14px] font-semibold text-ink group-hover:text-primary">
                        {entry.title}
                      </span>
                      <span className="text-[10px] uppercase tracking-wider text-ink-4 font-medium">
                        {entry.areaTitle}
                      </span>
                    </div>
                    {entry.summary && (
                      <p className="mt-0.5 text-[12.5px] text-ink-2 line-clamp-1">{entry.summary}</p>
                    )}
                    <p className="mt-1 text-[12px] text-ink-3 line-clamp-2">{excerpt}</p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
