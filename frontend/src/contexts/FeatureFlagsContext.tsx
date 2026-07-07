"use client";

/**
 * Feature flags context (Phase MVP-4).
 *
 * Reads /api/v1/flags once at mount. Fail-closed during the loading window —
 * if the fetch hasn't completed yet (or fails), all flags are treated as OFF
 * to prevent flashes of restricted content.
 *
 * Backend defaults to ON for all flags; production sets env vars to flip
 * specific surfaces OFF without redeploy.
 */
import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

export interface FeatureFlags {
  research_lane: boolean;
  paper_trading: boolean;
  backtests: boolean;
  replay: boolean;
  universe_ui: boolean;
  ops_ui: boolean;
  policy_ui: boolean;
  integrations_ui: boolean;
  risk_ui: boolean;
  news_ui: boolean;
  operator_console: boolean;
  // Phase 16 — research fundamentals + peers panels on /research/[ticker]
  research_fundamentals_ui: boolean;
  research_peers_ui: boolean;
  // Desk W1 (DEC-7) — Unified Research Desk v2; dark until the SPEC-04
  // exit gate passes in the browser-equipped environment.
  desk_v2: boolean;
}

interface FeatureFlagsContextValue {
  flags: FeatureFlags;
  isLoading: boolean;
}

const FAIL_CLOSED: FeatureFlags = {
  research_lane: false,
  paper_trading: false,
  backtests: false,
  replay: false,
  universe_ui: false,
  ops_ui: false,
  policy_ui: false,
  integrations_ui: false,
  risk_ui: false,
  news_ui: false,
  operator_console: false,
  research_fundamentals_ui: false,
  research_peers_ui: false,
  desk_v2: false,
};

const FeatureFlagsContext = createContext<FeatureFlagsContextValue>({
  flags: FAIL_CLOSED,
  isLoading: true,
});

export function FeatureFlagsProvider({ children }: { children: ReactNode }) {
  const [flags, setFlags] = useState<FeatureFlags>(FAIL_CLOSED);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const base = API_BASE_URL.replace(/\/+$/, "");
    fetch(`${base}/api/v1/flags`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((body) => {
        if (cancelled) return;
        const data = body?.data;
        if (data && typeof data === "object") {
          setFlags({
            research_lane: Boolean(data.research_lane),
            paper_trading: Boolean(data.paper_trading),
            backtests: Boolean(data.backtests),
            replay: Boolean(data.replay),
            universe_ui: Boolean(data.universe_ui),
            ops_ui: Boolean(data.ops_ui),
            policy_ui: Boolean(data.policy_ui),
            integrations_ui: Boolean(data.integrations_ui),
            risk_ui: Boolean(data.risk_ui),
            news_ui: Boolean(data.news_ui),
            operator_console: Boolean(data.operator_console),
            research_fundamentals_ui: Boolean(data.research_fundamentals_ui),
            research_peers_ui: Boolean(data.research_peers_ui),
            desk_v2: Boolean(data.desk_v2),
          });
        }
      })
      .catch(() => {
        // Stay fail-closed.
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <FeatureFlagsContext.Provider value={{ flags, isLoading }}>
      {children}
    </FeatureFlagsContext.Provider>
  );
}

export function useFeatureFlags() {
  return useContext(FeatureFlagsContext);
}
