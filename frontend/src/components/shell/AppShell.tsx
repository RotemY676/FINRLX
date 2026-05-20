"use client";

import { useState, useCallback } from "react";
import { TopBar } from "./TopBar";
import { Sidebar } from "./Sidebar";
import { PaneProvider, ContextPanePanel } from "./ContextPane";
import { DisclaimerBanner } from "../legal/DisclaimerBanner";
import { DisclaimerModal } from "../legal/DisclaimerModal";

const MOBILE_BREAKPOINT = "(max-width: 767px)";

/**
 * App shell.
 *
 * - md+ (≥ 768px): three columns — Sidebar | main | ContextPane.
 *   The nav toggle collapses the sidebar width (w-52 ↔ w-14).
 * - <md: single column — main only. Sidebar becomes a left-edge drawer
 *   overlaid on top with a click-to-dismiss backdrop. The same nav toggle
 *   opens/closes the drawer. ContextPane is hidden on mobile (it returns
 *   in UX-1.3 as a bottom sheet).
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const [desktopCollapsed, setDesktopCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [ctxVisible, setCtxVisible] = useState(false);

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

  return (
    <PaneProvider>
      <DisclaimerModal />
      <div className="flex flex-col h-screen overflow-hidden">
        <TopBar
          onToggleNav={onToggleNav}
          onToggleCtx={() => setCtxVisible((p) => !p)}
          ctxVisible={ctxVisible}
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
          <main className="flex-1 overflow-y-auto p-pad bg-canvas">
            {children}
          </main>
          {ctxVisible && (
            <div className="hidden md:block">
              <ContextPanePanel />
            </div>
          )}
        </div>
        <DisclaimerBanner />
      </div>
    </PaneProvider>
  );
}
