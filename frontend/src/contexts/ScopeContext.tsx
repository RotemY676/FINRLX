"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { fetchRegime, fetchOverview } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";

interface ScopeContextValue {
  /** Rule-based regime label ("uptrend" | "downtrend" | "risk-off" | "neutral"),
   *  or "—" when it could not be computed. Never a fabricated default. */
  regime: string;
  /** False when the regime is unknown (not yet loaded, or the source was down).
   *  Drives a neutral dot instead of implying a risk-on/off reading we don't have. */
  regimeKnown: boolean;
  horizon: string;
  universe: string;
  isLoading: boolean;
}

const UNKNOWN_REGIME = "—";

const DEFAULT_SCOPE: ScopeContextValue = {
  regime: UNKNOWN_REGIME,
  regimeKnown: false,
  horizon: "3M",
  universe: "US Large Cap",
  isLoading: true,
};

const ScopeContext = createContext<ScopeContextValue>(DEFAULT_SCOPE);

/**
 * Maps a regime label to a status-dot colour. Colour is a redundant cue — the
 * label text always carries the meaning (NFR-4). Unknown → neutral grey, so the
 * strip never asserts a risk reading it doesn't have.
 */
export function regimeDotClass(regime: string, known: boolean): string {
  if (!known) return "bg-ink-3";
  switch (regime) {
    case "uptrend":
      return "bg-pos";
    case "risk-off":
      return "bg-breach";
    case "downtrend":
      return "bg-caution";
    default:
      return "bg-ink-3";
  }
}

export function ScopeProvider({ children }: { children: ReactNode }) {
  const { user, isLoading: authLoading } = useAuth();
  const [scope, setScope] = useState<ScopeContextValue>(DEFAULT_SCOPE);

  useEffect(() => {
    // Wait for auth to settle so we don't fire the authed /overview call while
    // the token is still hydrating (that produced a spurious 401 on first paint).
    if (authLoading) return;

    let cancelled = false;
    const signedIn = Boolean(user);

    Promise.all([
      // /regime is public market context — fetched for everyone, including a
      // logged-out desk visitor. /overview is tenant state — only when signed in.
      fetchRegime().catch(() => null),
      signedIn ? fetchOverview().catch(() => null) : Promise.resolve(null),
    ]).then(([regimeRes, overviewRes]) => {
      if (cancelled) return;
      const regime = regimeRes?.data;
      const overview = overviewRes?.data;

      // Horizon comes from the tenant's current recommendation validity window.
      // Logged out (no overview) we don't know it, so keep the neutral default.
      let horizon = "3M";
      const rec = overview?.current_recommendation;
      if (rec?.valid_from && rec?.valid_to) {
        const days = Math.round(
          (new Date(rec.valid_to).getTime() - new Date(rec.valid_from).getTime()) /
            86400000,
        );
        if (days <= 30) horizon = "1M";
        else if (days <= 60) horizon = "2M";
        else if (days <= 90) horizon = "3M";
        else if (days <= 180) horizon = "6M";
        else horizon = `${days}d`;
      }

      const label = regime?.regime_label;
      setScope({
        regime: label || UNKNOWN_REGIME,
        regimeKnown: Boolean(label),
        horizon,
        universe: "US Large Cap",
        isLoading: false,
      });
    });

    return () => {
      cancelled = true;
    };
  }, [user, authLoading]);

  return <ScopeContext.Provider value={scope}>{children}</ScopeContext.Provider>;
}

export function useScope() {
  return useContext(ScopeContext);
}
