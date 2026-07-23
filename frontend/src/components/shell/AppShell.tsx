"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { TopBar } from "./TopBar";
import { AppBar } from "./AppBar";
import { ContextStrip } from "./ContextStrip";
import { usePathname } from "next/navigation";
import { SimpleShell } from "./SimpleShell";
import { Sidebar } from "./Sidebar";
import { PaneProvider, ContextPanePanel, usePaneContext } from "./ContextPane";
import { CommandPalette } from "./CommandPalette";
import { DisclaimerBanner } from "../legal/DisclaimerBanner";
import { DisclaimerModal } from "../legal/DisclaimerModal";

const TOPBAR_FLAG_KEY = "finrlx-topbar-v3";
const SCROLL_SHRINK_THRESHOLD = 24;

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
  // LEAP S7a fix: Simple Mode routes get minimal chrome (spec J0/S7.4);
  // everything else keeps the full Pro shell untouched.
  const pathname = usePathname();
  const SIMPLE_ROUTES = new Set(["/", "/simple", "/compare"]);
  if (pathname && SIMPLE_ROUTES.has(pathname)) {
    return <SimpleShell>{children}</SimpleShell>;
  }
  return (
    <PaneProvider>
      <ShellInner>{children}</ShellInner>
    </PaneProvider>
  );
}

function ShellInner({ children }: { children: React.ReactNode }) {
  const [desktopCollapsed, setDesktopCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  // Phase 15 — v3 chrome (AppBar + ContextStrip) is the default;
  // operator can opt out via the UserMenu (Phase 15.4). The first
  // render is the v3 path so server + client agree; localStorage
  // post-hydration may flip to v2 if the user has opted out.
  const [useV3, setUseV3] = useState(true);
  const [scrolled, setScrolled] = useState(false);
  const mainRef = useRef<HTMLElement | null>(null);
  const { pane, openTab, closePane } = usePaneContext();

  // Phase 14.3 — global ⌘K / Ctrl+K opens the command palette.
  // Hook lives here so the keybind is available on every page, and
  // so the palette renders above the AppShell content (z-index).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const isCmdK =
        (e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K");
      if (!isCmdK) return;
      e.preventDefault();
      setPaletteOpen((v) => !v);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Phase 15.3 — hydrate the v3 opt-out preference once on mount and
  // listen for cross-tab changes (so flipping the toggle in the
  // UserMenu in one tab takes effect in others).
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const saved = window.localStorage.getItem(TOPBAR_FLAG_KEY);
      if (saved === "false") setUseV3(false);
    } catch {
      // ignore (private mode, quota)
    }
    const onStorage = (e: StorageEvent) => {
      if (e.key !== TOPBAR_FLAG_KEY) return;
      setUseV3(e.newValue !== "false");
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  // Phase 15.2 — scroll-shrink for the ContextStrip. Listens to the
  // main scrollable area (not window) because AppShell uses a
  // flex-column layout with main as the scroll container. The
  // threshold (24 px) is high enough to avoid jitter from rubber-
  // band scrolling on macOS but low enough to feel responsive.
  useEffect(() => {
    if (!useV3) return;
    const el = mainRef.current;
    if (!el) return;
    let raf = 0;
    const onScroll = () => {
      if (raf) return;
      raf = window.requestAnimationFrame(() => {
        raf = 0;
        const isScrolled = el.scrollTop > SCROLL_SHRINK_THRESHOLD;
        setScrolled((prev) => (prev === isScrolled ? prev : isScrolled));
      });
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      el.removeEventListener("scroll", onScroll);
      if (raf) window.cancelAnimationFrame(raf);
    };
  }, [useV3]);

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
      {/* h-dvh, not h-screen: iOS Safari sizes `vh` against the largest
          viewport, so a 100vh column with overflow-hidden pushes its last row
          under the address bar where it can never be scrolled to. */}
      <div className="flex flex-col h-dvh overflow-hidden">
        {/* Skip-to-content: visually hidden until focused, then floats above the
            TopBar. First focusable element on the page so keyboard users can
            jump past the brand/nav and land directly on page content. */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:inline-flex focus:items-center focus:justify-center focus:min-h-11 focus:px-4 focus:rounded-md focus:bg-primary focus:text-primary-ink focus:text-[13px] focus:font-medium focus:shadow-lg"
        >
          Skip to main content
        </a>
        {useV3 ? (
          // Phase 15 chrome — AppBar (identity row) + ContextStrip
          // (workspace row). Two strips, each with a single job.
          <>
            <AppBar onOpenPalette={() => setPaletteOpen(true)} />
            <ContextStrip
              onToggleNav={onToggleNav}
              onToggleCtx={onToggleCtx}
              ctxVisible={pane.isOpen}
              mobileNavOpen={mobileOpen}
              scrolled={scrolled}
            />
          </>
        ) : (
          // Legacy v2 TopBar — kept while the v3 opt-out toggle exists.
          // Scheduled for removal in Phase 15.6.
          <TopBar
            onToggleNav={onToggleNav}
            onToggleCtx={onToggleCtx}
            ctxVisible={pane.isOpen}
            mobileNavOpen={mobileOpen}
            onOpenPalette={() => setPaletteOpen(true)}
          />
        )}
        <CommandPalette
          open={paletteOpen}
          onClose={() => setPaletteOpen(false)}
        />
        <div className="relative flex flex-1 overflow-hidden">
          <Sidebar
            collapsed={desktopCollapsed}
            mobileOpen={mobileOpen}
            onMobileClose={closeMobileNav}
            chromeOffsetClass={useV3 ? "top-28" : "top-14"}
          />
          {mobileOpen && (
            // Phase 15.3 — top offset tracks the actual chrome
            // height: v2 TopBar = h-14 (56 px), v3 AppBar+ContextStrip
            // = 64 + 48 = 112 px (top-28).  Mobile chrome shows
            // ContextStrip below `md`? No — ContextStrip is full-width
            // on mobile too, so the drawer must clear both rows.
            <div
              className={`md:hidden fixed inset-0 ${useV3 ? "top-28" : "top-14"} z-20 bg-ink/40 backdrop-blur-sm`}
              onClick={closeMobileNav}
              aria-hidden="true"
            />
          )}
          {/* tabIndex=0 makes the scrollable main keyboard-operable on pages
              that ship no focusable interactive content (empty state, error,
              disclaimer-modal-over-empty). Required by WCAG 2.1.1; equivalent
              to axe rule scrollable-region-focusable. focus:outline-none keeps
              the visible ring off when the page itself has interactive
              content the user is using.
              Phase 15.2 — mainRef drives the ContextStrip's shrink-on-scroll
              by exposing this element's scrollTop. */}
          <main
            id="main-content"
            ref={mainRef}
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
