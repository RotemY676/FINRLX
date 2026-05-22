"use client";

/**
 * Phase 16.1 — Peers panel for /research/[ticker].
 *
 * Replaces the prior "coming later" placeholder. Consumes
 * /api/v1/research/peers/{ticker} which:
 *   - always returns 200 with a structurally-complete envelope
 *   - returns an empty `peers` list + `coverage_note` when no
 *     provider is configured
 *   - returns the provider's sector peers (Finnhub /stock/peers,
 *     etc.) when activated
 *
 * Each peer renders as a row with ticker, name, last close, daily
 * change, and a deep link to its own /research/[peer] workspace —
 * keeping the user inside the research-grounded flow (no auto-
 * publish path).
 *
 * Owned by skills:
 *   - finrlx-fintech-dashboard-patterns (every row carries
 *     ticker + name + last_close + change with consistent units)
 *   - recommendation-object-provenance (peer links lead to the
 *     research workspace, never to a published recommendation)
 *   - fintech-disclaimer-and-marketing-guard (no "Buy" CTAs)
 */
import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchPeers, type PeersData, type PeerEntryData } from "@/services/api";
import { Icon } from "@/components/icons/Icon";

interface Props {
  ticker: string;
}

export function PeersPanel({ ticker }: Props) {
  const [data, setData] = useState<PeersData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchPeers(ticker)
      .then((res) => {
        if (!cancelled) setData(res.data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  if (error) {
    return (
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <PanelHeader />
        <p className="text-body-sm text-breach-soft-ink mt-2">
          Peers unreachable: {error}
        </p>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <PanelHeader />
        <p className="text-body-sm text-ink-3 mt-2">Loading peers…</p>
      </section>
    );
  }

  const isStub = data.source === "stub";
  const hasPeers = data.peers.length > 0;

  return (
    <section
      aria-labelledby="peers-heading"
      className="rounded-lg border border-line bg-surface p-pad shadow-sm"
    >
      <PanelHeader sector={data.target_sector} industry={data.target_industry} />

      {/* Stub / empty state — honest about why nothing is here */}
      {isStub || !hasPeers ? (
        <div className="mt-3 rounded-md border border-dashed border-line bg-surface-2 p-3">
          <p className="text-body-sm text-ink-2">
            {data.coverage_note ??
              "No peers returned for this ticker. The provider may not cover this symbol's sector."}
          </p>
        </div>
      ) : (
        <ul role="list" className="mt-3 divide-y divide-line">
          {data.peers.map((peer) => (
            <PeerRow key={peer.ticker} peer={peer} />
          ))}
        </ul>
      )}

      <Provenance source={data.source} asOf={data.as_of} cachedAt={data.cached_at} />
    </section>
  );
}

function PanelHeader({
  sector,
  industry,
}: {
  sector?: string | null;
  industry?: string | null;
}) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Icon name="compare" size={14} className="text-ink-3" />
      <h2 id="peers-heading" className="text-card-title text-ink">
        Sector peers
      </h2>
      {(industry || sector) && (
        <span className="ml-auto text-meta text-ink-3 font-mono uppercase tracking-wider">
          {industry ?? sector}
        </span>
      )}
    </div>
  );
}

function PeerRow({ peer }: { peer: PeerEntryData }) {
  const change = peer.change_pct_1d;
  const changeColor =
    change == null ? "text-ink-4" : change >= 0 ? "text-pos" : "text-breach";
  const changeLabel =
    change == null
      ? "—"
      : `${change >= 0 ? "+" : ""}${(change * 100).toFixed(2)}%`;

  return (
    <li>
      <Link
        href={`/research/${encodeURIComponent(peer.ticker)}`}
        className="flex items-center gap-3 py-2.5 hover:bg-surface-3 -mx-2 px-2 rounded-md transition-colors"
      >
        <span className="font-mono text-body-sm text-ink font-semibold w-16 shrink-0">
          {peer.ticker}
        </span>
        <span className="text-body-sm text-ink-2 truncate flex-1">
          {peer.name ?? "—"}
        </span>
        <span className="text-meta text-ink-4 font-mono tabular-nums shrink-0 hidden sm:inline">
          {peer.last_close_usd != null ? `$${peer.last_close_usd.toFixed(2)}` : "—"}
        </span>
        <span className={`text-body-sm font-mono font-medium tabular-nums shrink-0 w-20 text-right ${changeColor}`}>
          {changeLabel}
        </span>
      </Link>
    </li>
  );
}

function Provenance({
  source,
  asOf,
  cachedAt,
}: {
  source: string;
  asOf: string | null;
  cachedAt: string | null;
}) {
  return (
    <p className="text-meta text-ink-4 mt-3 pt-3 border-t border-line">
      Source <span className="font-mono">{source}</span>
      {asOf && (
        <>
          {" "}
          · as of <span className="font-mono">{asOf.slice(0, 10)}</span>
        </>
      )}
      {cachedAt && (
        <>
          {" "}
          · cached <span className="font-mono">{cachedAt.slice(0, 16).replace("T", " ")}</span>
        </>
      )}
    </p>
  );
}
