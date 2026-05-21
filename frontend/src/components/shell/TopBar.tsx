"use client";

import { useState, useCallback, useEffect } from "react";
import { Icon } from "@/components/icons/Icon";
import { usePathname } from "next/navigation";
import { useTheme } from "@/contexts/ThemeContext";
import { useScope } from "@/contexts/ScopeContext";
import { UserMenu } from "@/components/shell/UserMenu";

const DENSITIES = ["default", "compact", "comfortable"] as const;
type Density = typeof DENSITIES[number];

const CRUMB_MAP: Record<string, string> = {
  "/": "Decision Command Center",
  "/decision": "Decision",
  "/comparison": "Engine comparison",
  "/replay": "Replay",
  "/backtests": "Backtests",
  "/paper": "Paper portfolio",
  "/admin": "Research lab",
  "/profile": "My profile",
  "/templates": "Templates",
  "/feedback": "Send feedback",
  "/onboarding": "Welcome",
  "/risk": "Risk",
  "/news": "News",
  "/ops": "Ops",
  "/policies": "Policies",
  "/integrations": "Integrations",
  "/universe": "Universe",
};

interface TopBarProps {
  onToggleNav: () => void;
  onToggleCtx: () => void;
  ctxVisible: boolean;
  /** When true on a mobile viewport, the nav drawer is open. */
  mobileNavOpen?: boolean;
}

export function TopBar({ onToggleNav, onToggleCtx, ctxVisible, mobileNavOpen = false }: TopBarProps) {
  const pathname = usePathname() ?? "/";
  const crumb = CRUMB_MAP[pathname] || "Workspace";
  const { theme, toggleTheme } = useTheme();
  const scope = useScope();

  const [density, setDensity] = useState<Density>("default");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("finrlx-density") as Density | null;
    if (saved && DENSITIES.includes(saved)) {
      setDensity(saved);
      if (saved !== "default") {
        document.documentElement.setAttribute("data-density", saved);
      }
    }
  }, []);

  const cycleDensity = useCallback(() => {
    const idx = DENSITIES.indexOf(density);
    const next = DENSITIES[(idx + 1) % DENSITIES.length];
    setDensity(next);
    if (next === "default") {
      document.documentElement.removeAttribute("data-density");
    } else {
      document.documentElement.setAttribute("data-density", next);
    }
    localStorage.setItem("finrlx-density", next);
  }, [density]);

  return (
    <header
      role="banner"
      aria-label="FINRLX top navigation"
      className="h-11 shrink-0 flex items-center gap-3 px-4 border-b border-line bg-surface text-[13px]"
    >
      {/* Brand */}
      <div className="flex items-center gap-2 shrink-0">
        <div className="w-5 h-5 rounded-md bg-primary" aria-hidden="true" />
        <span className="font-semibold text-ink">FINRLX</span>
      </div>

      {/* Nav toggle — opens the mobile drawer below md, collapses the column above md */}
      <button
        onClick={onToggleNav}
        className="inline-flex items-center justify-center h-11 w-11 md:h-9 md:w-9 rounded-md hover:bg-surface-3 text-ink-3 transition-colors"
        aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
        aria-expanded={mobileNavOpen}
        aria-controls="primary-nav"
      >
        <Icon name="panel-left" size={18} />
      </button>

      {/* Current page label — replaces the noisy "Workspaces > X" breadcrumb. */}
      <span className="text-ink font-medium">{crumb}</span>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Scope chips — dynamic from ScopeContext */}
      <div className="hidden lg:flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-2 text-ink-2 text-[12px]">
          <span className={`w-1.5 h-1.5 rounded-full ${scope.regimeConfidence > 0.7 ? "bg-pos" : scope.regimeConfidence > 0.4 ? "bg-caution" : "bg-breach"}`} />
          Regime <b className="text-ink font-medium ml-0.5">{scope.isLoading ? "..." : scope.regime}</b>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-2 text-ink-2 text-[12px]">
          <Icon name="clock" size={11} />
          Horizon <b className="text-ink font-medium ml-0.5">{scope.horizon}</b>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-2 text-ink-2 text-[12px]">
          <Icon name="universe" size={11} />
          Universe <b className="text-ink font-medium ml-0.5">{scope.universe}</b>
        </div>
      </div>

      {/* Search */}
      <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-md bg-surface-2 text-ink-4 text-[12px] w-56">
        <Icon name="search" size={13} />
        <span>Search…</span>
        <span className="ml-auto px-1 py-0.5 rounded bg-surface-3 text-[10px] text-ink-3 font-mono">⌘K</span>
      </div>

      {/* Density selector */}
      <button
        onClick={cycleDensity}
        className="hidden lg:flex items-center gap-1 px-2 py-1 rounded-md hover:bg-surface-3 text-ink-3 text-[10px] font-mono transition-colors"
        title={`Density: ${density} — click to cycle`}
      >
        {density === "compact" ? "Aa−" : density === "comfortable" ? "Aa+" : "Aa"}
      </button>

      {/* Theme toggle */}
      <button
        onClick={toggleTheme}
        className="inline-flex items-center justify-center h-11 w-11 md:h-9 md:w-9 rounded-md hover:bg-surface-3 text-ink-3 transition-colors"
        title={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
        aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
      >
        <Icon name={theme === "light" ? "moon" : "sun"} size={18} />
      </button>

      {/* Notifications — hidden on mobile to free up TopBar real estate; the
          drawer-equivalent surface for notifications lands in a future phase. */}
      <button
        className="hidden md:inline-flex items-center justify-center h-9 w-9 rounded-md hover:bg-surface-3 text-ink-3 transition-colors relative"
        title="Notifications"
        aria-label="Notifications"
      >
        <Icon name="bell" size={15} />
        <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-breach" />
      </button>

      {/* Context pane toggle. On mobile (<md) the pane opens as a bottom sheet;
          on desktop it docks as a right aside. */}
      <button
        onClick={onToggleCtx}
        className="inline-flex items-center justify-center h-11 w-11 md:h-9 md:w-9 rounded-md hover:bg-surface-3 transition-colors"
        title="Toggle context pane"
        aria-label={ctxVisible ? "Hide context pane" : "Show context pane"}
        aria-expanded={ctxVisible}
        style={{ opacity: ctxVisible ? 1 : 0.45 }}
      >
        <Icon name="panel-right" size={18} className="text-ink-3" />
      </button>

      {/* Avatar dropdown — UI-1 follow-up. Replaces the static chip +
          adjacent "Sign out" button with the industry-standard pattern. */}
      <UserMenu />
    </header>
  );
}
