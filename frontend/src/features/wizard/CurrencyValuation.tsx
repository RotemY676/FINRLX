"use client";

/**
 * Phase FX-3 — currency-translated valuation card for /paper.
 *
 * Loads the user's profile.base_currency (falls back to USD), lets the
 * user pick a different display currency, and shows the active paper
 * portfolio translated through /paper/current/valuation-in-currency.
 *
 * Per-holding FX rates and any fallback warnings are surfaced explicitly
 * so the user can see when a stale or cross-rate path was used.
 */
import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchMyProfile } from "@/features/wizard/api";

const SUPPORTED_CURRENCIES = ["USD", "EUR", "ILS", "GBP"] as const;

interface ValuationHolding {
  asset_id: string;
  ticker: string;
  asset_currency: string;
  quantity: number;
  last_price: number;
  value_native: number;
  value_in_target: number;
  fx_rate: number;
  fx_rate_date: string;
  fx_is_fallback: boolean;
}

interface ValuationPayload {
  portfolio_id: string;
  base_currency: string;
  target_currency: string;
  as_of_date: string;
  total_value_in_target: number;
  holdings: ValuationHolding[];
}

interface ValuationEnvelope {
  meta: { warnings?: string[] };
  data: ValuationPayload;
}

function buildApiUrl(path: string): string {
  const base =
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "https://backend-production-aab8.up.railway.app";
  return `${base}${path}`;
}

function authHeaders(): Record<string, string> {
  // Read token off localStorage directly to avoid importing the auth
  // service into this lightweight component.
  if (typeof window === "undefined") return {};
  const t = window.localStorage.getItem("finrlx_access_token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function fetchValuation(
  currency: string,
): Promise<{ data: ValuationPayload | null; warnings: string[]; status: number }> {
  const url = buildApiUrl(
    `/api/v1/paper/current/valuation-in-currency?currency=${encodeURIComponent(currency)}`,
  );
  const res = await fetch(url, { headers: { Accept: "application/json", ...authHeaders() } });
  if (res.status === 404) return { data: null, warnings: ["no_active_paper_portfolio"], status: 404 };
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`FX-3 fetch ${res.status}: ${body || res.statusText}`);
  }
  const envelope = (await res.json()) as ValuationEnvelope;
  return {
    data: envelope.data,
    warnings: envelope.meta.warnings ?? [],
    status: res.status,
  };
}

function formatAmount(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${amount.toFixed(0)} ${currency}`;
  }
}

export default function CurrencyValuation() {
  const [currency, setCurrency] = useState<string>("USD");
  const [profileCurrency, setProfileCurrency] = useState<string | null>(null);
  const [payload, setPayload] = useState<ValuationPayload | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // On mount: load profile.base_currency and pre-select it.
  useEffect(() => {
    let cancelled = false;
    fetchMyProfile()
      .then((me) => {
        if (cancelled) return;
        const c = me.profile?.base_currency ?? "USD";
        setProfileCurrency(c);
        setCurrency(c);
      })
      .catch(() => {
        if (!cancelled) {
          setProfileCurrency("USD");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const loadValuation = useCallback(async (c: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchValuation(c);
      setPayload(result.data);
      setWarnings(result.warnings);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setPayload(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (profileCurrency === null) return; // wait for profile load
    void loadValuation(currency);
  }, [currency, profileCurrency, loadValuation]);

  const totalLabel = useMemo(() => {
    if (!payload) return null;
    return formatAmount(payload.total_value_in_target, payload.target_currency);
  }, [payload]);

  const hasFallback = useMemo(
    () => (payload?.holdings ?? []).some((h) => h.fx_is_fallback),
    [payload],
  );

  return (
    <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
      <div className="flex items-start justify-between flex-wrap gap-2">
        <div>
          <p className="text-[11px] text-ink-3">Valuation in</p>
          <div className="flex items-center gap-2 mt-1">
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              aria-label="Display currency"
              className="bg-input border border-line rounded-md px-2 py-1.5 text-[13px] text-ink min-h-[44px]"
            >
              {SUPPORTED_CURRENCIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            {profileCurrency && profileCurrency !== currency ? (
              <button
                type="button"
                onClick={() => setCurrency(profileCurrency)}
                className="text-[11px] text-accent underline"
              >
                use profile ({profileCurrency})
              </button>
            ) : null}
          </div>
        </div>
        <div className="text-right">
          <p className="text-[11px] text-ink-3">Total value</p>
          <p className="text-[20px] font-semibold text-ink font-mono mt-1">
            {isLoading ? "…" : totalLabel ?? "—"}
          </p>
        </div>
      </div>

      {error ? (
        <p role="alert" className="mt-3 text-[12px] text-breach">
          Could not load FX-converted valuation: {error}
        </p>
      ) : null}

      {warnings.length > 0 ? (
        <p
          role="status"
          aria-live="polite"
          className="mt-3 text-[11.5px] text-ink-4 italic"
        >
          {warnings.length === 1
            ? warnings[0]
            : `${warnings.length} FX notes: ${warnings.slice(0, 2).join("; ")}${warnings.length > 2 ? "…" : ""}`}
        </p>
      ) : null}

      {hasFallback ? (
        <p className="mt-2 text-[11px] text-ink-4">
          Some rates used a fallback path (stale or cross-rated). The
          displayed total is best-effort, not point-in-time exact.
        </p>
      ) : null}

      {payload && payload.holdings.length > 0 ? (
        <details className="mt-3">
          <summary className="text-[12px] text-ink-3 cursor-pointer">
            Per-holding FX detail ({payload.holdings.length} positions, as of {payload.as_of_date})
          </summary>
          <ul className="mt-2 space-y-1">
            {payload.holdings.map((h) => (
              <li key={h.asset_id} className="text-[11.5px] text-ink-3 font-mono">
                {h.ticker}: {formatAmount(h.value_native, h.asset_currency)} → {formatAmount(h.value_in_target, payload.target_currency)}{" "}
                <span className="text-ink-4">
                  (rate {h.fx_rate.toFixed(4)} @ {h.fx_rate_date}
                  {h.fx_is_fallback ? ", fallback" : ""})
                </span>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}
