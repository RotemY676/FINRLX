"use client";

/**
 * Phase 15.1 — FINRLX AppBar (top row of the two-strip chrome).
 *
 * Identity-focused. Eleven competing controls of the legacy TopBar
 * collapse into four slots here:
 *
 *   [ Brand ]──────[ Search (centerpiece) ]──────[ Notif · Account ]
 *
 * Domain state (Regime / Horizon / Universe), breadcrumb, nav toggle,
 * and context-pane toggle all move to ContextStrip (Phase 15.2).
 * Density / Theme / Help all live inside the UserMenu (already done
 * in 15.4 personalisation row).
 *
 * Height: 64 px (h-16). Search is `flex-1 max-w-[560px]` so it grows
 * with viewport but never dominates ultra-wide displays.
 *
 * Owned by skills:
 *   - finrlx-ux-redesign-director (rule 8 one search, rule 4 readable
 *     density: search is the largest interactive element)
 *   - anthropic-frontend-design-mirror (asymmetric composition: brand
 *     left, search dominant centre, account/notif right; subtle
 *     elevation via a left-to-right gradient instead of a flat
 *     background)
 *   - vercel-web-design-guidelines-mirror (semantic <header
 *     role="banner">, aria-keyshortcuts on search trigger, focus
 *     ring on every interactive control)
 *   - fintech-disclaimer-and-marketing-guard (search placeholder
 *     copy is neutral: "tickers, decisions, ops, notes" — not
 *     "Find trade ideas")
 */
import { Icon } from "@/components/icons/Icon";
import { UserMenu } from "@/components/shell/UserMenu";
import { NotificationsPanel } from "@/components/shell/NotificationsPanel";
import { BrandMark } from "@/components/shell/BrandMark";
import Link from "next/link";

interface AppBarProps {
  onOpenPalette: () => void;
}

export function AppBar({ onOpenPalette }: AppBarProps) {
  return (
    <header
      role="banner"
      aria-label="FINRLX app bar"
      // h-16 is the chrome height. The gradient is intentionally
      // subtle (4–6% across the row) so the bar reads as elevated
      // without competing with content.
      className="h-16 shrink-0 flex items-center gap-3 px-4 md:px-5 border-b border-line bg-gradient-to-r from-surface via-surface to-surface-2"
    >
      {/* Brand — clickable, lands at home */}
      <Link
        href="/"
        aria-label="FINRLX — go to home"
        className="flex items-center gap-2.5 shrink-0 text-primary hover:opacity-90 transition-opacity focus:outline-none focus:ring-2 focus:ring-primary rounded-md px-1 py-1 -mx-1"
      >
        <BrandMark size={28} />
        <span className="hidden sm:inline font-display font-semibold text-card-title text-ink tracking-[-0.01em]">
          FINRLX
        </span>
      </Link>
      <Link href="/pro" className="text-sm text-[var(--ink-2)] underline-offset-2 hover:underline" title="Pro mode: the full decision command center and manual tools">Pro</Link>

      {/* Search — the centerpiece. Grows with viewport, capped at
          560 px so it doesn't sprawl on ultra-wide displays. */}
      <button
        type="button"
        onClick={onOpenPalette}
        aria-label="Open search palette"
        aria-keyshortcuts="Meta+K Control+K"
        className="group flex-1 max-w-[560px] mx-auto flex items-center gap-2.5 h-11 px-4 rounded-lg bg-surface-2 hover:bg-surface-3 border border-line hover:border-line-strong text-ink-3 hover:text-ink-2 text-body-sm transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:bg-surface"
      >
        <Icon name="search" size={18} className="shrink-0" />
        <span className="flex-1 text-left truncate">
          <span className="hidden md:inline">Search FINRLX — tickers, decisions, ops, notes</span>
          <span className="md:hidden">Search…</span>
        </span>
        <kbd className="hidden md:inline-flex items-center text-meta font-mono text-ink-2 bg-surface-3 group-hover:bg-surface border border-line px-1.5 py-0.5 rounded shrink-0">
          ⌘K
        </kbd>
      </button>

      {/* Right cluster — notifications + help shortcut + account.
          Density / theme / help-page live inside the UserMenu (avoids
          rebuilding the legacy 5-icon toolbar that the strategic
          plan diagnosed as a "dev toolbar" aesthetic). */}
      <div className="flex items-center gap-1 shrink-0">
        <NotificationsPanel />
        <UserMenu />
      </div>
    </header>
  );
}
