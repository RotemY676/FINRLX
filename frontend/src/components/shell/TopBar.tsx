"use client";

import { useState, useCallback, useEffect } from "react";
import Link from "next/link";
import { Icon } from "@/components/icons/Icon";
import { usePathname } from "next/navigation";
import { useTheme } from "@/contexts/ThemeContext";
import { useScope } from "@/contexts/ScopeContext";
import { UserMenu } from "@/components/shell/UserMenu";
import { NotificationsPanel } from "@/components/shell/NotificationsPanel";
import { BrandMark } from "@/components/shell/BrandMark";

const DENSITIES = ["default", "compact", "comfortable"] as const;
type Density = typeof DENSITIES[number];

/**
 * Phase 4 area-aware breadcrumbs. Each route knows which product area it
 * belongs to (per `DOCS/handoff/FINRLX_UX_PHASE_2_INFORMATION_ARCHITECTURE.md`)
 * plus its own short title. The breadcrumb renders as `Area · Title` when
 * both are present, falling back to the title alone for the root and for
 * routes outside the seven areas (legal, auth).
 */
interface CrumbDescriptor {
  area: string | null;
  title: string;
}

const CRUMB_MAP: Record<string, CrumbDescriptor> = {
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

interface TopBarProps {
  onToggleNav: () => void;
  onToggleCtx: () => void;
  ctxVisible: boolean;
  /** When true on a mobile viewport, the nav drawer is open. */
  mobileNavOpen?: boolean;
  /** Phase 14.3 — open the global command palette. */
  onOpenPalette: () => void;
}

export function TopBar({
  onToggleNav,
  onToggleCtx,
  ctxVisible,
  mobileNavOpen = false,
  onOpenPalette,
}: TopBarProps) {
  const pathname = usePathname() ?? "/";
  const crumbDescriptor: CrumbDescriptor =
    CRUMB_MAP[pathname] ||
    (pathname.startsWith("/help")
      ? { area: "Settings", title: "Help center" }
      : pathname.startsWith("/research/")
        ? { area: "Research", title: pathname.split("/")[2]?.toUpperCase() ?? "Ticker" }
        : { area: null, title: "Workspace" });
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
      // Phase 14.1 — taller (h-14 / 56 px desktop) so the TopBar reads
      // as a real chrome surface, not a strip. Mobile keeps min-h-11
      // tap targets via min-h-11 on each interactive child.
      className="h-14 shrink-0 flex items-center gap-3 px-4 border-b border-line bg-surface"
    >
      {/* Brand — Phase 15.0 identity uplift.
          - Mark: distinctive SVG glyph (BrandMark) replaces the prior
            flat-color square. The mark uses currentColor for the bars
            so it inherits the wordmark hue.
          - Wordmark: Fraunces display face (already loaded via
            globals.css) for institutional gravitas. Tightened tracking
            (-0.01em). */}
      <Link
        href="/"
        aria-label="FINRLX — go to home"
        className="flex items-center gap-2 shrink-0 text-primary hover:opacity-90 transition-opacity"
      >
        <BrandMark size={26} />
        <span className="font-display font-semibold text-card-title text-ink tracking-[-0.01em]">
          FINRLX
        </span>
      </Link>
      <Link href="/pro" className="text-sm text-[var(--ink-2)] underline-offset-2 hover:underline" title="Pro mode: the full decision command center and manual tools">Pro</Link>

      {/* Nav toggle — opens the mobile drawer below md, collapses the column above md */}
      <button
        onClick={onToggleNav}
        className="inline-flex items-center justify-center h-11 w-11 md:h-10 md:w-10 rounded-md hover:bg-surface-3 text-ink-2 transition-colors"
        aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
        aria-expanded={mobileNavOpen}
        aria-controls="primary-nav"
      >
        <Icon name="panel-left" size={20} />
      </button>

      {/* Area-aware breadcrumb. Renders `Area · Page` when the route lives
          in one of the seven product areas; falls back to the page title
          alone for the root, legal pages, and auth flows. The middle dot
          uses U+00B7 per the Vercel web-design-guidelines mirror
          (Unicode glyphs, not "ASCII slashes"). The area segment hides
          on mobile (< 640 px) so the TopBar slot does not crowd.
          Phase 14.1 — body-sm title with explicit semibold; area
          segment at body-sm but ink-3 weight-normal for contrast. */}
      <nav aria-label="Breadcrumb" className="min-w-0">
        <ol className="flex items-center gap-2 text-body-sm">
          {crumbDescriptor.area && (
            <>
              <li className="hidden sm:inline text-ink-3 truncate">{crumbDescriptor.area}</li>
              <li className="hidden sm:inline text-ink-4" aria-hidden="true">·</li>
            </>
          )}
          <li aria-current="page" className="text-ink font-semibold truncate">
            {crumbDescriptor.title}
          </li>
        </ol>
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Scope chips — dynamic from ScopeContext.
          Phase 14.1: bumped to text-body-sm for legibility; dropped the
          half-faded look. */}
      <div className="hidden lg:flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-surface-2 text-ink-2 text-body-sm">
          <span className={`w-1.5 h-1.5 rounded-full ${scope.regimeConfidence > 0.7 ? "bg-pos" : scope.regimeConfidence > 0.4 ? "bg-caution" : "bg-breach"}`} />
          Regime <b className="text-ink font-semibold ml-0.5">{scope.isLoading ? "…" : scope.regime}</b>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-surface-2 text-ink-2 text-body-sm">
          <Icon name="clock" size={13} />
          Horizon <b className="text-ink font-semibold ml-0.5">{scope.horizon}</b>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-surface-2 text-ink-2 text-body-sm">
          <Icon name="universe" size={13} />
          Universe <b className="text-ink font-semibold ml-0.5">{scope.universe}</b>
        </div>
      </div>

      {/* Search — Phase 14.3 — opens the global CommandPalette. The
          chip on the TopBar is the visible trigger; ⌘K opens from
          anywhere. Mobile gets a compact icon-only button so the
          TopBar slot stays breathable. */}
      <button
        type="button"
        onClick={onOpenPalette}
        aria-label="Open search palette"
        aria-keyshortcuts="Meta+K Control+K"
        className="hidden md:flex items-center gap-2 px-3 h-10 rounded-md bg-surface-2 hover:bg-surface-3 text-ink-3 text-body-sm w-64 transition-colors focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <Icon name="search" size={16} />
        <span className="flex-1 text-left">Search FINRLX…</span>
        <kbd className="ml-auto px-1.5 py-0.5 rounded bg-surface-3 text-meta text-ink-3 font-mono">
          ⌘K
        </kbd>
      </button>
      <button
        type="button"
        onClick={onOpenPalette}
        aria-label="Open search palette"
        className="md:hidden inline-flex items-center justify-center h-11 w-11 rounded-md hover:bg-surface-3 text-ink-2 transition-colors"
      >
        <Icon name="search" size={20} />
      </button>

      {/* Density selector */}
      <button
        onClick={cycleDensity}
        className="hidden lg:flex items-center justify-center w-10 h-10 rounded-md hover:bg-surface-3 text-ink-2 text-body-sm font-mono transition-colors"
        title={`Density: ${density} — click to cycle`}
        aria-label={`Density: ${density}. Click to cycle.`}
      >
        {density === "compact" ? "Aa−" : density === "comfortable" ? "Aa+" : "Aa"}
      </button>

      {/* Theme toggle */}
      <button
        onClick={toggleTheme}
        className="inline-flex items-center justify-center h-11 w-11 md:h-10 md:w-10 rounded-md hover:bg-surface-3 text-ink-2 transition-colors"
        title={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
        aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
      >
        <Icon name={theme === "light" ? "moon" : "sun"} size={20} />
      </button>

      {/* Help center — global entry point, every page. Deep-links into /help. */}
      <Link
        href="/help"
        className="inline-flex items-center justify-center h-11 w-11 md:h-10 md:w-10 rounded-md hover:bg-surface-3 text-ink-2 transition-colors"
        title="Help center"
        aria-label="Open Help center"
        data-help-trigger="topbar"
      >
        <Icon name="help-circle" size={20} />
      </Link>

      {/* Notifications — Phase 14.4 — wired to NotificationsPanel which
          composes from /api/v1/ops + /api/v1/overview. Read-state lives
          in localStorage per user email. */}
      <NotificationsPanel />

      {/* Context pane toggle. On mobile (<md) the pane opens as a bottom sheet;
          on desktop it docks as a right aside. Phase 14.1 — dropped the
          half-faded look (opacity 0.45) that read as "disabled" to users.
          Active state now uses a subtle background tint. */}
      <button
        onClick={onToggleCtx}
        className={`inline-flex items-center justify-center h-11 w-11 md:h-10 md:w-10 rounded-md transition-colors ${
          ctxVisible
            ? "bg-primary-soft text-primary-soft-ink"
            : "hover:bg-surface-3 text-ink-2"
        }`}
        title="Toggle context pane"
        aria-label={ctxVisible ? "Hide context pane" : "Show context pane"}
        aria-expanded={ctxVisible}
      >
        <Icon name="panel-right" size={20} />
      </button>

      {/* Avatar dropdown — Gmail-style rich menu landing in sub-phase 14.2. */}
      <UserMenu />
    </header>
  );
}
