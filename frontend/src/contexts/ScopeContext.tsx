"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { fetchRegime, fetchOverview, RegimeData } from "@/services/api";

interface ScopeContextValue {
  regime: string;
  regimeConfidence: number;
  horizon: string;
  universe: string;
  isLoading: boolean;
}

const ScopeContext = createContext<ScopeContextValue>({
  regime: "Risk-on",
  regimeConfidence: 0,
  horizon: "3M",
  universe: "US-LargeCap",
  isLoading: true,
});

export function ScopeProvider({ children }: { children: ReactNode }) {
  const [scope, setScope] = useState<ScopeContextValue>({
    regime: "Risk-on",
    regimeConfidence: 0,
    horizon: "3M",
    universe: "US-LargeCap",
    isLoading: true,
  });

  useEffect(() => {
    Promise.all([
      fetchRegime().catch(() => null),
      fetchOverview().catch(() => null),
    ]).then(([regimeRes, overviewRes]) => {
      const regime = regimeRes?.data;
      const overview = overviewRes?.data;

      // Compute horizon from recommendation valid_from/valid_to
      let horizon = "3M";
      if (overview?.current_recommendation?.valid_from && overview?.current_recommendation?.valid_to) {
        const days = Math.round(
          (new Date(overview.current_recommendation.valid_to).getTime() -
           new Date(overview.current_recommendation.valid_from).getTime()) / 86400000
        );
        if (days <= 30) horizon = "1M";
        else if (days <= 60) horizon = "2M";
        else if (days <= 90) horizon = "3M";
        else if (days <= 180) horizon = "6M";
        else horizon = `${days}d`;
      }

      setScope({
        regime: regime?.regime_label || "Risk-on",
        regimeConfidence: regime?.regime_confidence || 0,
        horizon,
        universe: "US Large Cap",
        isLoading: false,
      });
    });
  }, []);

  return (
    <ScopeContext.Provider value={scope}>
      {children}
    </ScopeContext.Provider>
  );
}

export function useScope() {
  return useContext(ScopeContext);
}
