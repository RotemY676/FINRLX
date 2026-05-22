"use client";

import { useEffect, useState } from "react";

import { fetchNews, NewsBundle } from "@/services/api";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";
import { CopyLLMContextButton } from "@/components/operator/CopyLLMContextButton";
import { buildNewsContext } from "@/lib/operator/contextBuilder";

const SENTIMENT_STYLE: Record<string, string> = {
  positive: "bg-pos-soft text-pos-soft-ink",
  negative: "bg-breach-soft text-breach-soft-ink",
  neutral: "bg-surface-3 text-ink-3",
};

function fmtCompound(c: number): string {
  return (c >= 0 ? "+" : "") + c.toFixed(2);
}

export default function NewsPage() {
  const { flags, isLoading: flagsLoading } = useFeatureFlags();
  const [data, setData] = useState<NewsBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = (force = false) => {
    if (flagsLoading || !flags.news_ui) return;
    if (force) setRefreshing(true);
    else setLoading(true);
    fetchNews(force)
      .then((res) => setData(res.data))
      .catch((e) => setError(e.message))
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  };

  useEffect(load, [flagsLoading, flags.news_ui]); // eslint-disable-line react-hooks/exhaustive-deps

  if (flagsLoading || loading) return <PageLoading label="Loading news..." />;
  if (!flags.news_ui) {
    return (
      <PageError
        title="Surface not enabled"
        message="The News intelligence surface is not enabled for this environment."
        hint="Set FEATURE_NEWS_UI=true in the backend environment."
      />
    );
  }
  if (error) return <PageError title="News Error" message={error} hint="The RSS feeds may be unreachable from this network." />;
  if (!data || data.items.length === 0) {
    return (
      <PageEmpty
        title="No headlines"
        message="The RSS aggregator returned no items. This is usually temporary — try refresh in a few minutes."
      />
    );
  }

  const s = data.summary;

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div className="flex items-baseline justify-between gap-2 flex-wrap">
        <div>
          <h1 className="text-[20px] font-semibold text-ink">News intelligence</h1>
          <p className="text-[12px] text-ink-3 mt-0.5">
            {s.total} headlines · VADER sentiment · RSS sources (cached 5 min)
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <CopyLLMContextButton bundle={buildNewsContext({ bundle: data })} />
          <button
            type="button"
            onClick={() => load(true)}
            disabled={refreshing}
            className="inline-flex items-center justify-center min-h-11 md:min-h-0 md:h-9 px-3 rounded-md bg-surface-3 text-ink-2 text-[12.5px] font-medium hover:bg-line transition-colors disabled:opacity-50"
          >
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {/* Summary strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-gap">
        <div className="rounded-lg border border-line bg-surface p-3 shadow-sm">
          <p className="text-[11px] text-ink-4">Total</p>
          <p className="text-[20px] font-display font-semibold text-ink mt-0.5">{s.total}</p>
        </div>
        <div className="rounded-lg border border-line bg-surface p-3 shadow-sm">
          <p className="text-[11px] text-ink-4">Positive</p>
          <p className="text-[20px] font-display font-semibold text-pos mt-0.5">{s.positive}</p>
        </div>
        <div className="rounded-lg border border-line bg-surface p-3 shadow-sm">
          <p className="text-[11px] text-ink-4">Negative</p>
          <p className="text-[20px] font-display font-semibold text-breach mt-0.5">{s.negative}</p>
        </div>
        <div className="rounded-lg border border-line bg-surface p-3 shadow-sm">
          <p className="text-[11px] text-ink-4">Mean compound</p>
          <p className={`text-[20px] font-display font-semibold mt-0.5 ${s.mean_compound > 0.05 ? "text-pos" : s.mean_compound < -0.05 ? "text-breach" : "text-ink"}`}>
            {fmtCompound(s.mean_compound)}
          </p>
        </div>
      </div>

      {/* Items */}
      <ul className="space-y-2" role="list">
        {data.items.map((item, i) => (
          <li key={i} className="rounded-lg border border-line bg-surface p-pad shadow-sm">
            <div className="flex items-baseline justify-between flex-wrap gap-2">
              <a
                href={item.link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[14px] font-semibold text-ink hover:text-primary underline decoration-transparent hover:decoration-current"
              >
                {item.title}
              </a>
              <span className={`px-2 py-0.5 rounded-md text-[11px] font-medium ${SENTIMENT_STYLE[item.sentiment_label] ?? SENTIMENT_STYLE.neutral}`}>
                {item.sentiment_label} {fmtCompound(item.sentiment_compound)}
              </span>
            </div>
            {item.summary && (
              <p className="text-[12.5px] text-ink-2 mt-1.5 break-words">{item.summary}</p>
            )}
            <p className="text-[11px] text-ink-4 mt-2">
              {item.source}
              {item.published && ` · ${item.published}`}
            </p>
          </li>
        ))}
      </ul>

      <p className="text-[11px] text-ink-4">
        Sentiment scored with VADER (rule-based, no external API). Compound range [-1, 1]:
        positive ≥ 0.05, negative ≤ -0.05, neutral otherwise.
      </p>
    </div>
  );
}
