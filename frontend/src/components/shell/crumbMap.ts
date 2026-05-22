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
  "/research": { area: "Research", title: "Research hub" },
  "/decision": { area: "Decisions", title: "Current recommendation" },
  "/comparison": { area: "Decisions", title: "Engine comparison" },
  "/replay": { area: "Decisions", title: "Replay & forensics" },
  "/templates": { area: "Decisions", title: "Templates" },
  "/backtests": { area: "Research", title: "Backtests" },
  "/universe": { area: "Research", title: "Universe" },
  "/paper": { area: "Portfolio & Risk", title: "Paper portfolio" },
  "/risk": { area: "Portfolio & Risk", title: "Risk workspace" },
  "/news": { area: "Insights", title: "News intelligence" },
  "/ops": { area: "Ops & Governance", title: "Ops command" },
  "/policies": { area: "Ops & Governance", title: "Policies" },
  "/integrations": { area: "Ops & Governance", title: "Integrations" },
  "/admin": { area: "Ops & Governance", title: "Research lab" },
  "/operator": { area: "Ops & Governance", title: "Operator console" },
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
  if (pathname.startsWith("/research/")) {
    const segments = pathname.split("/");
    return { area: "Research", title: (segments[2] || "Ticker").toUpperCase() };
  }
  return { area: null, title: "Workspace" };
}
