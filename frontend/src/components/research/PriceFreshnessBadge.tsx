"use client";

/**
 * LEAP F1.6 — per-ticker price-freshness badge for Pro surfaces.
 * Binds GET /api/v1/prices/freshness?ticker= (D6 tiers, F2 calendar-aware)
 * to the existing DataFreshnessBadge treatments. Best-effort: absence of a
 * report renders nothing rather than inventing a status.
 */
import { useEffect, useState } from "react";

import { DataFreshnessBadge } from "@/components/home/DataFreshnessBadge";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

interface FreshnessPayload {
  ticker: string;
  latest_bar_date_iso: string;
  lag_trading_days: number;
  status: "fresh" | "stale" | "degraded";
}

const STATE_MAP = { fresh: "ok", stale: "stale", degraded: "warning" } as const;

export function PriceFreshnessBadge({ ticker }: { ticker: string }) {
  const [data, setData] = useState<FreshnessPayload | null>(null);

  useEffect(() => {
    const ctl = new AbortController();
    void (async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/v1/prices/freshness?ticker=${encodeURIComponent(ticker)}`,
          { signal: ctl.signal },
        );
        if (!res.ok) return;
        const body = (await res.json()) as { data: FreshnessPayload };
        setData(body.data);
      } catch {
        /* badge is best-effort; never block the page */
      }
    })();
    return () => ctl.abort();
  }, [ticker]);

  if (!data) return null;
  return (
    <DataFreshnessBadge
      label="Prices"
      asOf={data.latest_bar_date_iso}
      state={STATE_MAP[data.status]}
      warning={
        data.status === "fresh"
          ? null
          : `${data.lag_trading_days} trading day(s) behind the latest session`
      }
    />
  );
}
