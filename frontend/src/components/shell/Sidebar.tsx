"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "@/components/icons/Icon";
import { fetchWorkspaceCounts, WorkspaceCountsData, fetchSavedViews, SavedView } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import { useFeatureFlags, FeatureFlags } from "@/contexts/FeatureFlagsContext";

type FlagKey = keyof FeatureFlags;

interface NavEntry {
  key: string;
  href: string;
  label: string;
  icon: string;
  countKey?: "overview" | "decisions" | "risk" | "ops";
  flagKey?: FlagKey;
  /** Phase 14.6 — when true, the entry is only rendered for signed-in users. */
  requiresAuth?: boolean;
}

interface NavArea {
  /** Stable area key — also used as the `aria-labelledby` anchor and for active-state matching. */
  key: string;
  /** Section heading shown above the entries (hidden when sidebar is collapsed on desktop). */
  label: string;
  /** Routes whose presence should light up this area's section in the active state. */
  paths: ReadonlyArray<string>;
  entries: ReadonlyArray<NavEntry>;
  /** Phase 14.6 — when true, the section is only rendered for signed-in users. */
  requiresAuth?: boolean;
}

// Phase 4 information architecture: the seven product areas from
// DOCS/handoff/FINRLX_UX_PHASE_2_INFORMATION_ARCHITECTURE.md. Existing
// routes still live under their current paths — they migrate into proper
// sub-routes when their owning phase opens (Phases 6 / 8 / 10).
const AREAS: ReadonlyArray<NavArea> = [
  {
    key: "home",
    label: "Home",
    paths: ["/"],
    entries: [
      { key: "home", href: "/", label: "Command center", icon: "overview", countKey: "overview" },
    ],
  },
  {
    key: "research",
    label: "Research",
    paths: ["/pro/research", "/pro/universe", "/pro/backtests"],
    entries: [
      // Phase 6 — Research hub landing.
      { key: "research-hub", href: "/pro/research", label: "Research hub", icon: "search" },
      { key: "universe", href: "/pro/universe", label: "Universe", icon: "universe", flagKey: "universe_ui" },
      { key: "backtests", href: "/pro/backtests", label: "Backtests", icon: "backtest", flagKey: "backtests" },
    ],
  },
  {
    key: "decisions",
    label: "Decisions",
    paths: ["/pro/decision", "/pro/comparison", "/pro/replay", "/pro/templates"],
    entries: [
      { key: "decision", href: "/pro/decision", label: "Current recommendation", icon: "decision", countKey: "decisions" },
      { key: "comparison", href: "/pro/comparison", label: "Engine comparison", icon: "compare" },
      { key: "replay", href: "/pro/replay", label: "Replay & forensics", icon: "replay", flagKey: "replay" },
      { key: "templates", href: "/pro/templates", label: "Templates", icon: "layers" },
    ],
  },
  {
    key: "portfolio",
    label: "Portfolio & Risk",
    paths: ["/pro/paper", "/pro/risk"],
    entries: [
      { key: "paper", href: "/pro/paper", label: "Paper portfolio", icon: "paper", flagKey: "paper_trading" },
      { key: "risk", href: "/pro/risk", label: "Risk workspace", icon: "risk", countKey: "risk", flagKey: "risk_ui" },
    ],
  },
  {
    key: "insights",
    label: "Insights",
    paths: ["/pro/news"],
    entries: [
      { key: "news", href: "/pro/news", label: "News intelligence", icon: "news", flagKey: "news_ui" },
    ],
  },
  {
    key: "ops",
    label: "Ops & Governance",
    paths: ["/pro/ops", "/pro/policies", "/pro/integrations", "/pro/admin", "/pro/operator"],
    entries: [
      { key: "ops", href: "/pro/ops", label: "Ops command", icon: "ops", countKey: "ops", flagKey: "ops_ui" },
      { key: "policies", href: "/pro/policies", label: "Policies", icon: "check", flagKey: "policy_ui" },
      { key: "integrations", href: "/pro/integrations", label: "Integrations", icon: "database", flagKey: "integrations_ui" },
      // Desktop-only research lab. Sidebar entry survives so operators can find it; the page itself shows a desktop-only gate on mobile.
      { key: "admin", href: "/pro/admin", label: "Research lab", icon: "compare", flagKey: "research_lane" },
      { key: "operator", href: "/pro/operator", label: "Operator console", icon: "user", flagKey: "operator_console", requiresAuth: true },
    ],
  },
  {
    key: "settings",
    label: "Settings",
    paths: ["/profile", "/feedback"],
    // Phase 14.6 — both Settings entries require auth (profile loads
    // POST /api/v1/profile; feedback POSTs as an authenticated user).
    // Surfacing them to anonymous users is a phantom affordance — clicks
    // would redirect to /login anyway. Hide the whole section instead.
    requiresAuth: true,
    entries: [
      { key: "profile", href: "/profile", label: "My profile", icon: "user", requiresAuth: true },
      { key: "feedback", href: "/feedback", label: "Send feedback", icon: "message", requiresAuth: true },
    ],
  },
];

// Saved views are now DB-backed per user (Phase B3). Sidebar fetches the
// current user's list on mount + refreshes on workspace-count refresh tick.
// When the user is signed-out or has no saved views, the section hides.

interface SidebarProps {
  /** Desktop (≥md) only: toggle the in-flow column between w-52 and w-14. */
  collapsed: boolean;
  /** Mobile (<md) only: drawer open/closed. Ignored at ≥md. */
  mobileOpen?: boolean;
  /** Called when the user navigates or otherwise dismisses the mobile drawer. */
  onMobileClose?: () => void;
  /**
   * Phase 15.3 — chrome height as a Tailwind top-N class.  v2 chrome
   * = top-14 (56 px), v3 chrome = top-28 (112 px).  Used only on the
   * mobile drawer overlay; desktop sidebar is in-flow.
   */
  chromeOffsetClass?: string;
}

export function Sidebar({
  collapsed,
  mobileOpen = false,
  onMobileClose,
  chromeOffsetClass = "top-14",
}: SidebarProps) {
  const pathname = usePathname() ?? "/";
  const [counts, setCounts] = useState<WorkspaceCountsData | null>(null);
  const [savedViews, setSavedViews] = useState<SavedView[]>([]);
  const { flags, isLoading: flagsLoading } = useFeatureFlags();
  const { user } = useAuth();
  const isSignedIn = Boolean(user);

  useEffect(() => {
    fetchWorkspaceCounts()
      .then((res) => setCounts(res.data))
      .catch(() => {});

    // Refresh counts every 60s
    const interval = setInterval(() => {
      fetchWorkspaceCounts()
        .then((res) => setCounts(res.data))
        .catch(() => {});
    }, 60_000);
    return () => clearInterval(interval);
  }, []);

  // Saved views (Phase B3) — DB-backed, fetched once when the user is
  // signed in. If the auth context refreshes (e.g. after login), we re-fetch.
  useEffect(() => {
    if (!isSignedIn) {
      setSavedViews([]);
      return;
    }
    fetchSavedViews()
      .then((res) => setSavedViews(res.data))
      .catch(() => setSavedViews([]));
  }, [isSignedIn]);

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  const getBadge = (countKey?: "overview" | "decisions" | "risk" | "ops") => {
    if (!countKey || !counts) return undefined;
    const val = counts[countKey];
    return val > 0 ? String(val) : undefined;
  };

  // Fail-closed while flags load — hide gated entries to avoid flash of restricted content.
  const isGatedVisible = (flagKey?: FlagKey) => {
    if (!flagKey) return true;
    if (flagsLoading) return false;
    return flags[flagKey];
  };

  // Phase 14.6 — auth gate. Entries / sections that need a signed-in
  // user disappear from the nav for anonymous visitors.
  const isAuthVisible = (requiresAuth?: boolean) => {
    if (!requiresAuth) return true;
    return isSignedIn;
  };

  const renderNavItem = (item: NavEntry) => {
    if (!isGatedVisible(item.flagKey)) return null;
    if (!isAuthVisible(item.requiresAuth)) return null;
    const active = isActive(item.href);
    const badge = getBadge(item.countKey);
    return (
      <Link
        key={item.key}
        href={item.href}
        onClick={onMobileClose}
        // aria-current per the Phase 2 navigation spec (§7) — assistive
        // tech announces the active entry rather than relying on the
        // visual highlight alone.
        aria-current={active ? "page" : undefined}
        className={`flex items-center gap-2.5 px-3 min-h-11 md:min-h-0 md:py-1.5 mx-1.5 rounded-md text-caption transition-colors ${
          active
            ? "bg-primary-soft text-primary-soft-ink font-medium"
            : "text-ink-2 hover:bg-surface-3"
        }`}
        title={collapsed ? item.label : undefined}
      >
        <Icon name={item.icon} size={16} className={active ? "text-primary" : "text-ink-3"} />
        {/* On mobile the drawer is always full-width — labels and badges are
            always visible. On md+, hide labels when the sidebar is collapsed. */}
        <span className={`flex-1 truncate ${collapsed ? "md:hidden" : ""}`}>
          {item.label}
        </span>
        {badge && (
          <span className={`text-meta font-mono min-w-[20px] text-center rounded-sm px-1 ${
            collapsed ? "md:hidden" : ""
          } ${active ? "text-primary" : "text-ink-4 bg-surface-2"}`}>
            {badge}
          </span>
        )}
      </Link>
    );
  };

  /** Render one product-area section. Hides the section entirely when every entry it contains is flag-gated off OR auth-gated off, so the divider doesn't show a phantom heading. */
  const renderArea = (area: NavArea, withDivider: boolean) => {
    if (!isAuthVisible(area.requiresAuth)) return null;
    const visibleEntries = area.entries.filter(
      (entry) => isGatedVisible(entry.flagKey) && isAuthVisible(entry.requiresAuth),
    );
    if (visibleEntries.length === 0) return null;
    const headingId = `nav-area-${area.key}`;
    return (
      <div
        key={area.key}
        role="group"
        aria-labelledby={headingId}
        className={withDivider ? "py-2 border-t border-line" : "py-2"}
      >
        <div
          id={headingId}
          className={`px-3 py-1.5 text-meta font-semibold uppercase tracking-wider text-ink-4 ${
            collapsed ? "md:hidden" : ""
          }`}
        >
          {area.label}
        </div>
        {visibleEntries.map(renderNavItem)}
      </div>
    );
  };

  // Mobile (<md): off-canvas overlay sliding in from the left, w-64.
  // Desktop (≥md): in-flow column with collapsible width (w-52 ↔ w-14).
  const mobileTransform = mobileOpen ? "translate-x-0" : "-translate-x-full";
  const desktopWidth = collapsed ? "md:w-14" : "md:w-52";

  return (
    <aside
      id="primary-nav"
      aria-label="Primary navigation"
      className={[
        // mobile-first: fixed overlay, full-height under the topbar.
        // Phase 15.3 — chromeOffsetClass tracks v2 (top-14) vs v3
        // (top-28) chrome heights via a className from AppShell.
        `fixed inset-y-0 left-0 ${chromeOffsetClass} z-30 w-64 transform transition-transform`,
        mobileTransform,
        // md+: revert to in-flow column
        "md:static md:top-auto md:translate-x-0 md:transition-all",
        desktopWidth,
        // shared
        "shrink-0 border-r border-line bg-surface flex flex-col overflow-y-auto",
      ].join(" ")}
    >
      {/* Seven product areas — the Phase 4 IA. Each area renders its own
          section with an `aria-labelledby` group; sections with all
          entries flag-gated off self-suppress. */}
      {AREAS.map((area, idx) => renderArea(area, idx > 0))}

      {/* Saved views — DB-backed per-user (Phase B3). Section hides when the
          user has no saved views OR is signed-out, so we don't ship an
          "empty" pile that misleads. Hides entirely on md+ when collapsed. */}
      {savedViews.length > 0 && (
        <div className={`py-2 border-t border-line mt-auto ${collapsed ? "md:hidden" : ""}`}>
          <div className="px-3 py-1.5 text-meta font-semibold uppercase tracking-wider text-ink-4">
            Saved views
          </div>
          {savedViews.map((v) => (
            <div
              key={v.id}
              className="flex items-center gap-2 px-3 min-h-11 md:min-h-0 md:py-1 mx-1.5 rounded-md text-meta text-ink-3 hover:bg-surface-3 cursor-pointer transition-colors"
              title={`${v.scope} · ${v.created_at?.slice(0, 10) ?? ""}`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${v.tone ? "bg-current " + v.tone : "bg-ink-4"}`} />
              <span className="truncate">{v.name}</span>
            </div>
          ))}
        </div>
      )}

      {/* Version */}
      <div className={`px-3 py-2 border-t border-line ${collapsed ? "md:hidden" : ""}`}>
        <span className="text-meta text-ink-4">v0.3.0</span>
      </div>
    </aside>
  );
}
