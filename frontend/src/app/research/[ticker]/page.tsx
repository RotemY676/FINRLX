"use client";

/**
 * Phase 6 — Per-ticker research workspace.
 *
 * Real surfaces:
 *   - Header with the ticker symbol.
 *   - Price chart card (reuses `PriceChartCard`, real `/api/v1/pricechart`).
 *   - News strip filtered to the ticker (reuses `/api/v1/news` with a
 *     frontend filter on title + summary, since the news endpoint does
 *     not currently support a ticker filter parameter).
 *
 * Honest empty states:
 *   - Fundamentals / peers — explicit "coming later" panels. There is no
 *     backend for these as of Phase 6.
 *   - Source-grounded assistant — link to existing `/operator` analyst
 *     console (which is the FINRLX-canonical way to capture LLM context
 *     against a ticker). The full embedded assistant lives in Phase 11.
 */
import Link from "next/link";
import { useEffect, useState, use } from "react";

import { fetchNews, NewsItem } from "@/services/api";
import { PriceChartCard } from "@/components/charts/PriceChartCard";
import { PageLoading } from "@/components/feedback/PageLoading";
import { Icon } from "@/components/icons/Icon";
import { FundamentalsPanel } from "@/components/research/FundamentalsPanel";
import { PriceFreshnessBadge } from "@/components/research/PriceFreshnessBadge";
import { PeersPanel } from "@/components/research/PeersPanel";
import { DocumentsPanel } from "@/components/research/DocumentsPanel";
import { InsightsPanel } from "@/components/research/InsightsPanel";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";

interface PageProps {
  params: Promise<{ ticker: string }>;
}

const SENTIMENT_BG: Record<string, string> = {
  positive: "bg-pos-soft text-pos-soft-ink",
  neutral: "bg-surface-3 text-ink-3",
  negative: "bg-breach-soft text-breach-soft-ink",
};

function filterNewsForTicker(items: NewsItem[], ticker: string): NewsItem[] {
  const upper = ticker.toUpperCase();
  // Word-boundary match avoids substring false positives (e.g. "NVDA"
  // inside "convey" never happens, but "AMD" inside "GAMD" would).
  const re = new RegExp(`\\b${upper}\\b`, "i");
  return items.filter(
    (item) => re.test(item.title) || re.test(item.summary),
  );
}

export default function ResearchTickerPage({ params }: PageProps) {
  const { ticker: rawTicker } = use(params);
  const ticker = rawTicker.toUpperCase();
  const { flags } = useFeatureFlags();
  const [news, setNews] = useState<NewsItem[] | null>(null);
  const [newsError, setNewsError] = useState<string | null>(null);

  useEffect(() => {
    fetchNews()
      .then((res) => {
        setNews(filterNewsForTicker(res.data.items, ticker));
      })
      .catch((e) => setNewsError(e.message));
  }, [ticker]);

  return (
    <div className="space-y-gap max-w-[1200px]">
      <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-2">
        <div>
          <Link
            href="/research"
            className="text-caption text-primary hover:underline"
          >
            ← Research hub
          </Link>
          <h1 className="text-page-title text-ink mt-1 font-mono">{ticker}</h1>
          <div className="mt-1"><PriceFreshnessBadge ticker={ticker} /></div>
          <p className="text-body-sm text-ink-2 mt-1 max-w-xl leading-snug">
            Research workspace. Output here is informational — not a
            recommendation to buy or sell the security.
          </p>
        </div>
        <Link
          href={`/operator?surface=manual&ticker=${ticker}`}
          className="inline-flex items-center justify-center gap-1.5 self-start md:self-auto min-h-11 px-4 rounded-md border border-line bg-surface text-ink text-body-sm font-medium hover:border-line-strong transition-colors"
        >
          <Icon name="message" size={14} />
          Capture analyst note
        </Link>
      </header>

      {/* Price chart — the one real data panel we have for an arbitrary
          ticker. The backend may return an empty series if it doesn't
          cover the ticker; the card handles that internally. */}
      <PriceChartCard ticker={ticker} />

      {/* News, filtered for this ticker */}
      <section
        aria-labelledby="news-heading"
        className="rounded-lg border border-line bg-surface p-pad shadow-sm"
      >
        <div className="flex items-center gap-2 mb-3">
          <Icon name="news" size={14} className="text-ink-3" />
          <h2 id="news-heading" className="text-card-title text-ink">
            News mentions
          </h2>
          {news && (
            <span className="text-meta text-ink-4 ml-auto font-mono">
              {news.length} item{news.length === 1 ? "" : "s"}
            </span>
          )}
        </div>
        {news === null && !newsError ? (
          <p className="text-body-sm text-ink-3">Loading news…</p>
        ) : newsError ? (
          <p className="text-body-sm text-breach-soft-ink">
            News feed unreachable: {newsError}
          </p>
        ) : news && news.length === 0 ? (
          <p className="text-body-sm text-ink-3">
            No recent headlines mention this ticker. Try a different symbol or
            refresh the news feed from the Insights surface.
          </p>
        ) : (
          <ul className="space-y-3">
            {news!.slice(0, 8).map((item, idx) => (
              <li key={idx} className="border-b border-line pb-3 last:border-b-0 last:pb-0">
                <div className="flex items-start gap-2 flex-wrap">
                  <span
                    className={`text-meta px-1.5 py-0.5 rounded-sm font-medium ${
                      SENTIMENT_BG[item.sentiment_label] ?? SENTIMENT_BG.neutral
                    }`}
                  >
                    {item.sentiment_label}
                  </span>
                  <span className="text-meta text-ink-4 font-mono">
                    {item.source}
                  </span>
                  {item.published && (
                    <span className="text-meta text-ink-4">
                      · {item.published.slice(0, 10)}
                    </span>
                  )}
                </div>
                <a
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-body-sm text-ink hover:underline mt-1 inline-block"
                >
                  {item.title}
                </a>
                {item.summary && (
                  <p className="text-caption text-ink-3 mt-1 line-clamp-2">
                    {item.summary}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Phase 16.1 — Fundamentals and sector Peers shipped.  Each
          panel hides entirely when its feature flag is off, and renders
          an honest "configure provider" empty state when no provider
          is wired (default Phase 16.0 behaviour). */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {flags.research_fundamentals_ui && <FundamentalsPanel ticker={ticker} />}
        {flags.research_peers_ui && <PeersPanel ticker={ticker} />}
      </div>

      {/* Phase 18.7 — Cross-quarter SEC insights. On mount, auto-fetches
          the last 6 quarterly filings from SEC EDGAR, runs the LLM
          synthesis, and renders the trajectory + latest-quarter delta.
          Caches for 7 days; falls back gracefully for non-US tickers. */}
      <InsightsPanel ticker={ticker} />

      {/* Phase 17.3 — Document upload + LLM analysis. The panel handles
          its own auth gating (sign-in prompt when no user) and surfaces
          the backend's honest 503 states (no LLM provider configured,
          monthly budget exceeded, document not ready) verbatim. */}
      <DocumentsPanel ticker={ticker} />
    </div>
  );
}
