"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "@/components/icons/Icon";
import { fetchWorkspaceCounts, WorkspaceCountsData } from "@/services/api";
import { useFeatureFlags, FeatureFlags } from "@/contexts/FeatureFlagsContext";

type FlagKey = keyof FeatureFlags;

const WORKSPACES: ReadonlyArray<{
  key: string;
  href: string;
  label: string;
  icon: string;
  countKey?: "overview" | "decisions" | "risk" | "ops";
  flagKey?: FlagKey;
}> = [
  { key: "overview", href: "/", label: "Overview", icon: "overview", countKey: "overview" },
  { key: "decision", href: "/decision", label: "Decisions", icon: "decision", countKey: "decisions" },
  { key: "comparison", href: "/comparison", label: "Engine comparison", icon: "compare" },
  { key: "risk", href: "#", label: "Risk workspace", icon: "risk", countKey: "risk" },
  { key: "replay", href: "/replay", label: "Replay & forensics", icon: "replay", flagKey: "replay" },
  { key: "backtests", href: "/backtests", label: "Backtests", icon: "backtest", flagKey: "backtests" },
  { key: "paper", href: "/paper", label: "Paper portfolio", icon: "paper", flagKey: "paper_trading" },
  { key: "universe", href: "/universe", label: "Universe", icon: "universe", flagKey: "universe_ui" },
  { key: "news", href: "#", label: "News intelligence", icon: "news" },
];

const OPS: ReadonlyArray<{
  key: string;
  href: string;
  label: string;
  icon: string;
  countKey?: "overview" | "decisions" | "risk" | "ops";
  flagKey?: FlagKey;
}> = [
  { key: "admin", href: "/admin", label: "Ops command", icon: "ops", countKey: "ops", flagKey: "research_lane" },
];

const SAVED = [
  { label: "Momentum leaders · 3M", tone: "" },
  { label: "Breach watch · concentration", tone: "text-accent" },
  { label: "Fresh changes · today", tone: "text-pos" },
  { label: "Post-mortem cases", tone: "text-breach" },
];

interface SidebarProps {
  /** Desktop (≥md) only: toggle the in-flow column between w-52 and w-14. */
  collapsed: boolean;
  /** Mobile (<md) only: drawer open/closed. Ignored at ≥md. */
  mobileOpen?: boolean;
  /** Called when the user navigates or otherwise dismisses the mobile drawer. */
  onMobileClose?: () => void;
}

export function Sidebar({ collapsed, mobileOpen = false, onMobileClose }: SidebarProps) {
  const pathname = usePathname() ?? "/";
  const [counts, setCounts] = useState<WorkspaceCountsData | null>(null);
  const { flags, isLoading: flagsLoading } = useFeatureFlags();

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

  const renderNavItem = (item: (typeof WORKSPACES)[number] | (typeof OPS)[number]) => {
    if (!isGatedVisible(item.flagKey)) return null;
    const active = isActive(item.href);
    const badge = getBadge(item.countKey);
    return (
      <Link
        key={item.key}
        href={item.href}
        onClick={onMobileClose}
        className={`flex items-center gap-2.5 px-3 min-h-11 md:min-h-0 md:py-1.5 mx-1.5 rounded-md text-[13px] transition-colors ${
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
          <span className={`text-[11px] font-mono min-w-[20px] text-center rounded-sm px-1 ${
            collapsed ? "md:hidden" : ""
          } ${active ? "text-primary" : "text-ink-4 bg-surface-2"}`}>
            {badge}
          </span>
        )}
      </Link>
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
        // mobile-first: fixed overlay, full-height under the topbar (h-11=44px)
        "fixed inset-y-0 left-0 top-11 z-30 w-64 transform transition-transform",
        mobileTransform,
        // md+: revert to in-flow column
        "md:static md:top-auto md:translate-x-0 md:transition-all",
        desktopWidth,
        // shared
        "shrink-0 border-r border-line bg-surface flex flex-col overflow-y-auto",
      ].join(" ")}
    >
      {/* Workspaces */}
      <div className="py-2">
        <div className={`px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-4 ${collapsed ? "md:hidden" : ""}`}>
          Workspaces
        </div>
        {WORKSPACES.map(renderNavItem)}
      </div>

      {/* Operations */}
      <div className="py-2 border-t border-line">
        <div className={`px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-4 ${collapsed ? "md:hidden" : ""}`}>
          Operations
        </div>
        {OPS.map(renderNavItem)}
      </div>

      {/* Saved views — full-content section, hides entirely on md+ when collapsed */}
      <div className={`py-2 border-t border-line mt-auto ${collapsed ? "md:hidden" : ""}`}>
        <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-4">
          Saved views
        </div>
        {SAVED.map((s, i) => (
          <div
            key={i}
            className="flex items-center gap-2 px-3 min-h-11 md:min-h-0 md:py-1 mx-1.5 rounded-md text-[12px] text-ink-3 hover:bg-surface-3 cursor-pointer transition-colors"
          >
            <span className={`w-1.5 h-1.5 rounded-full ${s.tone ? "bg-current " + s.tone : "bg-ink-4"}`} />
            <span className="truncate">{s.label}</span>
          </div>
        ))}
      </div>

      {/* Version */}
      <div className={`px-3 py-2 border-t border-line ${collapsed ? "md:hidden" : ""}`}>
        <span className="text-[11px] text-ink-4">v0.3.0</span>
      </div>
    </aside>
  );
}
