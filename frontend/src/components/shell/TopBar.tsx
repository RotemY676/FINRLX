"use client";

import { Icon } from "@/components/icons/Icon";
import { usePathname } from "next/navigation";
import { useTheme } from "@/contexts/ThemeContext";
import { useScope } from "@/contexts/ScopeContext";

const CRUMB_MAP: Record<string, string> = {
  "/": "Overview",
  "/decision": "Decision Workspace",
  "/comparison": "Engine Comparison",
  "/replay": "Replay & Forensics",
  "/backtests": "Backtests",
  "/paper": "Paper Portfolio",
  "/admin": "Ops Command Center",
};

interface TopBarProps {
  onToggleNav: () => void;
  onToggleCtx: () => void;
  ctxVisible: boolean;
}

export function TopBar({ onToggleNav, onToggleCtx, ctxVisible }: TopBarProps) {
  const pathname = usePathname() ?? "/";
  const crumb = CRUMB_MAP[pathname] || "Workspace";
  const { theme, toggleTheme } = useTheme();
  const scope = useScope();

  return (
    <header className="h-11 shrink-0 flex items-center gap-3 px-4 border-b border-line bg-surface text-[13px]">
      {/* Brand */}
      <div className="flex items-center gap-2 shrink-0">
        <div className="w-5 h-5 rounded-md bg-primary" />
        <span className="font-semibold text-ink">
          QuantPipeline<em className="font-normal text-ink-3 not-italic"> · decision</em>
        </span>
      </div>

      {/* Nav toggle */}
      <button
        onClick={onToggleNav}
        className="p-1 rounded-md hover:bg-surface-3 text-ink-3 transition-colors"
        title="Toggle sidebar"
      >
        <Icon name="panel-left" size={15} />
      </button>

      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1.5 text-ink-3">
        <span>Workspaces</span>
        <Icon name="chevron-right" size={11} className="text-ink-4" />
        <span className="text-ink font-medium">{crumb}</span>
      </nav>

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
        <span className="ml-auto px-1 py-0.5 rounded bg-surface-3 text-[10px] font-mono">⌘K</span>
      </div>

      {/* Theme toggle */}
      <button
        onClick={toggleTheme}
        className="p-1.5 rounded-md hover:bg-surface-3 text-ink-3 transition-colors"
        title={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
      >
        <Icon name={theme === "light" ? "moon" : "sun"} size={15} />
      </button>

      {/* Notifications */}
      <button className="p-1.5 rounded-md hover:bg-surface-3 text-ink-3 transition-colors relative" title="Notifications">
        <Icon name="bell" size={15} />
        <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-breach" />
      </button>

      {/* Context pane toggle */}
      <button
        onClick={onToggleCtx}
        className="p-1.5 rounded-md hover:bg-surface-3 transition-colors"
        title="Toggle context pane"
        style={{ opacity: ctxVisible ? 1 : 0.45 }}
      >
        <Icon name="panel-right" size={15} className="text-ink-3" />
      </button>

      {/* Avatar */}
      <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-primary-ink text-[11px] font-semibold">
        RM
      </div>
    </header>
  );
}
