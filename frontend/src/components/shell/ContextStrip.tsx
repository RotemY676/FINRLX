"use client";

/**
 * Phase 15.2 — Workspace context strip (bottom row of the two-strip
 * chrome).
 *
 * Workspace-focused. Carries:
 *   - Nav toggle (left edge — toggles sidebar / mobile drawer)
 *   - Breadcrumb (area · page)
 *   - Scope chips (Regime / Horizon / Universe — the FINRLX-domain
 *     state that the analyst is working against)
 *   - Context-pane toggle (right edge — controls the right rail)
 *
 * Shrink-on-scroll behaviour (operator-selected during the strategy
 * gate): when `scrolled` is true, height drops from 48 px to 32 px
 * and the scope chips hide entirely. Breadcrumb + nav toggle +
 * context-pane toggle stay visible because they are workspace
 * structure, not workspace state.
 *
 * Single-line guarantee: every chip is `whitespace-nowrap` and the
 * row uses `overflow-hidden` so chips truncate rather than wrap.
 * Below `lg`, scope chips collapse into a single "Scope" pill with
 * a popover (Phase 15.2 ships the hard-collapse; popover landing in
 * a follow-up if needed).
 *
 * Owned by skills:
 *   - finrlx-fintech-dashboard-patterns (regime dot uses the
 *     freshness contract: pos / caution / breach by confidence
 *     thresholds; chips carry consistent label + value pattern)
 *   - vercel-web-design-guidelines-mirror (semantic <nav
 *     aria-label="Workspace context">, aria-current preserved on
 *     breadcrumb, aria-expanded on context-pane toggle)
 *   - finrlx-ux-redesign-director (rule 4 readable density — chips
 *     at text-body-sm, never below)
 */
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon } from "@/components/icons/Icon";
import { useScope, regimeDotClass } from "@/contexts/ScopeContext";
import { resolveCrumb } from "./crumbMap";

interface ContextStripProps {
  onToggleNav: () => void;
  onToggleCtx: () => void;
  ctxVisible: boolean;
  mobileNavOpen?: boolean;
  /** When true, the strip renders in shrunk mode (h-8, scope chips hidden). */
  scrolled?: boolean;
}

export function ContextStrip({
  onToggleNav,
  onToggleCtx,
  ctxVisible,
  mobileNavOpen = false,
  scrolled = false,
}: ContextStripProps) {
  const pathname = usePathname() ?? "/";
  const crumb = resolveCrumb(pathname);
  const scope = useScope();

  // Height switches between 48 px (normal) and 32 px (shrunk). Padding
  // also shrinks slightly so the row reads as collapsed, not just shorter.
  const heightClass = scrolled ? "h-8" : "h-12";

  // The chip dot mirrors the regime label (uptrend→pos, downtrend→caution,
  // risk-off→breach, neutral/unknown→grey). Colour is redundant with the label
  // text; no confidence number backs it (the system computes none), so we never
  // paint a confidence we don't have.
  const regimeDot = regimeDotClass(scope.regime, scope.regimeKnown);

  return (
    <nav
      aria-label="Workspace context"
      className={`${heightClass} shrink-0 flex items-center gap-2 px-3 md:px-4 border-b border-line bg-surface-2 overflow-hidden transition-[height] duration-150`}
    >
      {/* Nav toggle — moved from app bar so it sits next to the
          breadcrumb (workspace structure), not next to the brand. */}
      <button
        type="button"
        onClick={onToggleNav}
        className={`inline-flex items-center justify-center rounded-md hover:bg-surface-3 text-ink-2 transition-colors shrink-0 ${
          scrolled ? "h-7 w-7" : "h-9 w-9"
        }`}
        aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
        aria-expanded={mobileNavOpen}
        aria-controls="primary-nav"
      >
        <Icon name="panel-left" size={scrolled ? 16 : 18} />
      </button>

      {/* Breadcrumb — guaranteed single line via the wrapping
          <ol>'s overflow-hidden + min-w-0.  Area segment hides
          on <sm to keep the row tight. */}
      <ol className="flex items-center gap-2 text-body-sm min-w-0 flex-1">
        {crumb.area && (
          <>
            <li className="hidden sm:inline text-ink-3 whitespace-nowrap shrink-0">
              {crumb.area}
            </li>
            <li className="hidden sm:inline text-ink-4 shrink-0" aria-hidden="true">
              ·
            </li>
          </>
        )}
        <li
          aria-current="page"
          className="text-ink font-semibold truncate"
        >
          {crumb.title}
        </li>
      </ol>

      {/* Scope chips — collapse when scrolled, hide below `lg` to
          preserve single-line.  Each chip carries its own label and
          value (per fintech-dashboard-patterns: never a bare number). */}
      <div
        className={`hidden lg:flex items-center gap-2 shrink-0 transition-opacity ${
          scrolled ? "opacity-0 pointer-events-none w-0 overflow-hidden" : "opacity-100"
        }`}
        aria-hidden={scrolled}
      >
        <ScopeChip
          dotClass={regimeDot}
          label="Regime"
          value={scope.isLoading ? "…" : scope.regime}
        />
        <ScopeChip icon="clock" label="Horizon" value={scope.horizon} />
        <ScopeChip icon="universe" label="Universe" value={scope.universe} />
      </div>

      {/* Context-pane toggle — anchored to the far right of the
          strip because it gates the right rail.  Active state uses
          primary-soft (consistent with v2 14.1 fix). */}
      <button
        type="button"
        onClick={onToggleCtx}
        className={`inline-flex items-center justify-center rounded-md transition-colors shrink-0 ${
          scrolled ? "h-7 w-7" : "h-9 w-9"
        } ${
          ctxVisible
            ? "bg-primary-soft text-primary-soft-ink"
            : "hover:bg-surface-3 text-ink-2"
        }`}
        title="Toggle context pane"
        aria-label={ctxVisible ? "Hide context pane" : "Show context pane"}
        aria-expanded={ctxVisible}
      >
        <Icon name="panel-right" size={scrolled ? 16 : 18} />
      </button>
    </nav>
  );
}

interface ScopeChipProps {
  icon?: string;
  dotClass?: string;
  label: string;
  value: string;
}

function ScopeChip({ icon, dotClass, label, value }: ScopeChipProps) {
  return (
    <div className="flex items-center gap-1.5 px-2.5 h-8 rounded-md bg-surface text-ink-2 text-body-sm whitespace-nowrap border border-line">
      {dotClass && <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`} aria-hidden="true" />}
      {icon && <Icon name={icon} size={13} className="text-ink-3" />}
      <span className="text-ink-3">{label}</span>
      <span className="text-ink font-semibold">{value}</span>
    </div>
  );
}
