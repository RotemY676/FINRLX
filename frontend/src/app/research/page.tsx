"use client";

/**
 * Phase 6 — Research hub landing.
 *
 * Search-first; lists existing universes; deep-links to the per-ticker
 * workspace `/research/[ticker]` and to the existing `/backtests` and
 * `/universe` surfaces (the latter remains the coverage / readiness
 * view, per the Phase 2 IA).
 *
 * Honestly scoped: fundamentals, peer comparison, and the
 * source-grounded research assistant get full UI in Phase 11 + a
 * dedicated follow-up. This page surfaces only what the existing
 * backend supports today.
 */
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchUniverses, UniverseListItem } from "@/services/api";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import { PageError } from "@/components/feedback/PageError";
import { PageLoading } from "@/components/feedback/PageLoading";
import { Icon } from "@/components/icons/Icon";

function normalizeTicker(input: string): string | null {
  const t = input.trim().toUpperCase();
  if (!t) return null;
  if (!/^[A-Z]{1,8}(\.[A-Z]{1,4})?$/.test(t)) return null;
  return t;
}

export default function ResearchHubPage() {
  const router = useRouter();
  const { flags, isLoading: flagsLoading } = useFeatureFlags();
  const [universes, setUniverses] = useState<UniverseListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tickerInput, setTickerInput] = useState("");
  const [tickerError, setTickerError] = useState<string | null>(null);

  useEffect(() => {
    if (flagsLoading) return;
    if (!flags.universe_ui) {
      // Universe is gated off — still allow free-form ticker entry,
      // skip the universe list.
      setUniverses([]);
      return;
    }
    fetchUniverses()
      .then((res) => setUniverses(res.data))
      .catch((e) => setError(e.message));
  }, [flags.universe_ui, flagsLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const normalized = normalizeTicker(tickerInput);
    if (!normalized) {
      setTickerError("Enter a ticker symbol (e.g. NVDA, AAPL, MSFT.US).");
      return;
    }
    setTickerError(null);
    router.push(`/research/${normalized}`);
  };

  if (flagsLoading || universes === null) {
    return <PageLoading label="Loading research hub..." />;
  }
  if (error) {
    return (
      <PageError
        title="Research unavailable"
        message={error}
        hint="The universe API may be unreachable. Free-form ticker entry below still works."
      />
    );
  }

  return (
    <div className="space-y-gap max-w-[1200px]">
      <header>
        <h1 className="text-page-title text-ink">Research</h1>
        <p className="text-body-sm text-ink-2 mt-1 max-w-xl leading-snug">
          Search a ticker, browse a universe, or open a saved backtest. Every
          finding here is research output — not advice, not a published
          recommendation.
        </p>
      </header>

      {/* Free-form ticker search */}
      <section
        aria-labelledby="ticker-search-heading"
        className="rounded-lg border border-line bg-surface p-pad shadow-sm"
      >
        <h2 id="ticker-search-heading" className="text-card-title text-ink mb-2">
          Open a ticker workspace
        </h2>
        <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-2">
          <label htmlFor="ticker-input" className="sr-only">
            Ticker symbol
          </label>
          <input
            id="ticker-input"
            type="text"
            inputMode="text"
            autoComplete="off"
            value={tickerInput}
            onChange={(e) => {
              setTickerInput(e.target.value);
              if (tickerError) setTickerError(null);
            }}
            placeholder="e.g. NVDA"
            className="flex-1 min-h-11 px-3 rounded-md border border-line bg-canvas text-body text-ink placeholder:text-ink-4 focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            type="submit"
            className="inline-flex items-center justify-center gap-1.5 min-h-11 px-4 rounded-md bg-primary text-primary-ink text-body-sm font-medium hover:opacity-90 transition-opacity"
          >
            <Icon name="search" size={14} />
            Open workspace
          </button>
        </form>
        {tickerError && (
          <p role="alert" className="text-caption text-breach mt-2">
            {tickerError}
          </p>
        )}
      </section>

      {/* Universes list */}
      <section aria-labelledby="universes-heading" className="space-y-3">
        <div className="flex items-baseline justify-between">
          <h2 id="universes-heading" className="text-section-title text-ink">
            Universes
          </h2>
          {flags.universe_ui && (
            <Link
              href="/universe"
              className="text-caption text-primary hover:underline"
            >
              Coverage &amp; readiness →
            </Link>
          )}
        </div>
        {!flags.universe_ui ? (
          <div className="rounded-lg border border-line bg-surface-2 p-pad text-body-sm text-ink-3">
            The universe surface is gated off in this environment
            (<code className="font-mono text-meta">FEATURE_UNIVERSE_UI</code>).
            Use the ticker search above.
          </div>
        ) : universes.length === 0 ? (
          <div className="rounded-lg border border-line bg-surface-2 p-pad text-body-sm text-ink-3">
            No universes published yet. Once an operator publishes one, it
            will appear here.
          </div>
        ) : (
          <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {universes.map((u) => (
              <li key={u.universe_id}>
                <Link
                  href={`/universe?id=${encodeURIComponent(u.universe_id)}`}
                  className="block rounded-lg border border-line bg-surface p-pad shadow-sm hover:border-line-strong transition-colors"
                >
                  <h3 className="text-card-title text-ink">{u.name}</h3>
                  {u.description && (
                    <p className="text-caption text-ink-3 mt-1 line-clamp-2">
                      {u.description}
                    </p>
                  )}
                  <p className="text-meta text-ink-4 mt-2 font-mono">
                    {u.asset_count} assets
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Other research entry points */}
      <section aria-labelledby="other-research-heading" className="space-y-3">
        <h2 id="other-research-heading" className="text-section-title text-ink">
          Other entry points
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {flags.backtests && (
            <Link
              href="/backtests"
              className="rounded-lg border border-line bg-surface p-pad shadow-sm hover:border-line-strong transition-colors"
            >
              <h3 className="text-card-title text-ink flex items-center gap-2">
                <Icon name="backtest" size={16} className="text-ink-3" />
                Backtests
              </h3>
              <p className="text-body-sm text-ink-3 mt-1 leading-snug">
                Saved offline strategy runs. Output is research only; not a
                forecast and not a published recommendation.
              </p>
            </Link>
          )}
          <Link
            href="/decision"
            className="rounded-lg border border-line bg-surface p-pad shadow-sm hover:border-line-strong transition-colors"
          >
            <h3 className="text-card-title text-ink flex items-center gap-2">
              <Icon name="decision" size={16} className="text-ink-3" />
              Current recommendation
            </h3>
            <p className="text-body-sm text-ink-3 mt-1 leading-snug">
              The published thesis from today&rsquo;s pipeline run — for
              context only while you research.
            </p>
          </Link>
        </div>
      </section>

      {/* Honest "coming later" note */}
      <p className="text-caption text-ink-4">
        Fundamentals, peer comparison, and the source-grounded research
        assistant are scheduled for a later phase. Today the ticker workspace
        ships price-chart and news context; the rest renders honest empty
        states.
      </p>
    </div>
  );
}
