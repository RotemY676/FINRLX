"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { fetchRegime, RegimeData } from "@/services/api";

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
    fetchRegime()
      .then((res) => {
        const d = res.data;
        setScope({
          regime: d.regime_label,
          regimeConfidence: d.regime_confidence,
          horizon: "3M", // derived from recommendation; regime doesn't carry it
          universe: "US-LargeCap",
          isLoading: false,
        });
      })
      .catch(() => {
        setScope((prev) => ({ ...prev, isLoading: false }));
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
