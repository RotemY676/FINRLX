"use client";

import { useState, useCallback } from "react";
import { TopBar } from "./TopBar";
import { Sidebar } from "./Sidebar";
import { PaneProvider, ContextPanePanel, usePaneContext } from "./ContextPane";
import { DisclaimerBanner } from "../legal/DisclaimerBanner";
import { DisclaimerModal } from "../legal/DisclaimerModal";

const MOBILE_BREAKPOINT = "(max-width: 767px)";

/**
 * App shell.
 *
 * - md+ (≥ 768px): three columns — Sidebar | main | ContextPane (right aside).
 *   The nav toggle collapses the sidebar width (w-52 ↔ w-14).
 * - <md: single column — main only. Sidebar becomes a left-edge drawer
 *   overlaid on top with a click-to-dismiss backdrop. ContextPane becomes a
 *   bottom sheet overlaying main content. Both share the same toggles.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <PaneProvider>
      <ShellInner>{children}</ShellInner>
    </PaneProvider>
  );
}

function ShellInner({ children }: { children: React.ReactNode }) {
  const [desktopCollapsed, setDesktopCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { pane, openTab, closePane } = usePaneContext();

  const onToggleNav = useCallback(() => {
    // matchMedia is the cheapest viewport probe; it stays correct after a
    // window resize without needing a resize listener in the tree.
    const isMobile =
      typeof window !== "undefined" &&
      window.matchMedia(MOBILE_BREAKPOINT).matches;
    if (isMobile) setMobileOpen((p) => !p);
    else setDesktopCollapsed((p) => !p);
  }, []);

  const closeMobileNav = useCallback(() => setMobileOpen(false), []);

  const onToggleCtx = useCallback(() => {
    if (pane.isOpen) closePane();
    else openTab("risk"); // open to the first tab; pages can call openPane(...) for detail mode
  }, [pane.isOpen, openTab, closePane]);

  return (
    <>
      <DisclaimerModal />
      <div className="flex flex-col h-screen overflow-hidden">
        <TopBar
          onToggleNav={onToggleNav}
          onToggleCtx={onToggleCtx}
          ctxVisible={pane.isOpen}
          mobileNavOpen={mobileOpen}
        />
        <div className="relative flex flex-1 overflow-hidden">
          <Sidebar
            collapsed={desktopCollapsed}
            mobileOpen={mobileOpen}
            onMobileClose={closeMobileNav}
          />
          {mobileOpen && (
            <div
              className="md:hidden fixed inset-0 top-11 z-20 bg-ink/40 backdrop-blur-sm"
              onClick={closeMobileNav}
              aria-hidden="true"
            />
          )}
          {/* tabIndex=0 makes the scrollable main keyboard-operable on pages
              that ship no focusable interactive content (empty state, error,
              disclaimer-modal-over-empty). Required by WCAG 2.1.1; equivalent
              to axe rule scrollable-region-focusable. focus:outline-none keeps
              the visible ring off when the page itself has interactive
              content the user is using. */}
          <main
            id="main-content"
            tabIndex={0}
            className="flex-1 overflow-y-auto p-pad bg-canvas focus-visible:outline-none"
          >
            {children}
          </main>
          {/* ContextPanePanel renders itself: bottom sheet on mobile, right aside on md+.
              It self-gates via pane.isOpen — nothing renders when closed. */}
          <ContextPanePanel />
        </div>
        <DisclaimerBanner />
      </div>
    </>
  );
}
