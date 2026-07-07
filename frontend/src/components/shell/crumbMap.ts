/**
 * Shared breadcrumb resolver used by both the legacy TopBar (v2) and the
 * Phase 15 ContextStrip (v3). Single source of truth so the breadcrumb
 * label for any route does not drift between chrome implementations.
 *
 * Phase 2 IA reference:
 *   DOCS/handoff/FINRLX_UX_PHASE_2_INFORMATION_ARCHITECTURE.md
 */
export interface CrumbDescriptor {
  /** Product-area name from the seven-area IA, or null for routes
   *  that live outside the product areas (root, auth, legal). */
  area: string | null;
  /** Short page title to render as the breadcrumb leaf. */
  title: string;
}

export const CRUMB_MAP: Record<string, CrumbDescriptor> = {
  "/": { area: null, title: "Decision Command Center" },
  "/pro/research": { area: "Research", title: "Research hub" },
  "/pro/decision": { area: "Decisions", title: "Current recommendation" },
  "/pro/comparison": { area: "Decisions", title: "Engine comparison" },
  "/pro/replay": { area: "Decisions", title: "Replay & forensics" },
  "/pro/templates": { area: "Decisions", title: "Templates" },
  "/pro/backtests": { area: "Research", title: "Backtests" },
  "/pro/universe": { area: "Research", title: "Universe" },
  "/pro/paper": { area: "Portfolio & Risk", title: "Paper portfolio" },
  "/pro/risk": { area: "Portfolio & Risk", title: "Risk workspace" },
  "/pro/news": { area: "Insights", title: "News intelligence" },
  "/pro/ops": { area: "Ops & Governance", title: "Ops command" },
  "/pro/policies": { area: "Ops & Governance", title: "Policies" },
  "/pro/integrations": { area: "Ops & Governance", title: "Integrations" },
  "/pro/admin": { area: "Ops & Governance", title: "Research lab" },
  "/pro/operator": { area: "Ops & Governance", title: "Operator console" },
  "/profile": { area: "Settings", title: "My profile" },
  "/feedback": { area: "Settings", title: "Send feedback" },
  "/help": { area: "Settings", title: "Help center" },
  "/onboarding": { area: null, title: "Welcome" },
};

/** Resolve a pathname to its breadcrumb descriptor.  Falls back to
 *  generic "Workspace" for unknown routes, with special handling for
 *  /help/* (canonical help-center label) and /research/[ticker]
 *  (Research area, ticker as title). */
export function resolveCrumb(pathname: string): CrumbDescriptor {
  const direct = CRUMB_MAP[pathname];
  if (direct) return direct;
  if (pathname.startsWith("/help")) {
    return { area: "Settings", title: "Help center" };
  }
  if (pathname.startsWith("/pro/research/")) {
    const segments = pathname.split("/");
    return { area: "Research", title: (segments[2] || "Ticker").toUpperCase() };
  }
  return { area: null, title: "Workspace" };
}
