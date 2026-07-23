"use client";

/**
 * LEAP S7a fix — minimal chrome for Simple Mode routes (/, /simple, /compare).
 *
 * SIMPLE_MODE_SPEC J0 + S7.4: "Simple shows nothing but the product — logo,
 * ticker box, compare, help, account"; nothing competes with the ticker
 * field. The original S7a flip mounted the hero inside the full Pro chrome
 * (Sidebar + AppBar search + ContextStrip), which both violated the spec and
 * looked broken (two competing inputs, nested chrome). This shell replaces
 * that for Simple routes only; Pro routes keep AppShell untouched.
 */

import Link from "next/link";

/*
 * iOS notes (Phase UX — iPhone/iPad pass):
 *  - The document sets `viewport-fit=cover`, so on notched iPhones the page
 *    paints *under* the status bar and home indicator. Without the safe-area
 *    padding below, the brand row sits under the clock in portrait and under
 *    the notch in landscape. `env()` resolves to 0 everywhere else, so this
 *    costs desktop nothing.
 *  - `min-h-dvh` (not `min-h-screen`) — `vh` on iOS Safari measures the
 *    *largest* viewport, so a `100vh` column is taller than the visible area
 *    while the address bar is showing and the last row is unreachable.
 *  - Nav targets carry `min-h-11` (44pt, Apple HIG / WCAG 2.5.5). These are
 *    <Link>s, which the touch-target lint does not scan — it only walks
 *    <button> — so the floor is applied by hand here.
 */
export function SimpleShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <header
        className="safe-area-pt safe-area-pl safe-area-pr flex items-center gap-3 border-b border-line bg-surface px-4 py-2"
      >
        <Link
          href="/"
          className="inline-flex min-h-11 items-center font-display text-card-title font-semibold tracking-[-0.01em] text-ink"
        >
          FINRLX
        </Link>
        <nav className="ml-auto flex items-center gap-1 text-sm">
          <Link
            href="/compare"
            className="inline-flex min-h-11 items-center rounded-lg px-3 text-ink-2 underline-offset-2 hover:underline"
          >
            Compare
          </Link>
          <Link
            href="/help"
            className="inline-flex min-h-11 items-center rounded-lg px-3 text-ink-2 underline-offset-2 hover:underline"
          >
            Help
          </Link>
          <Link
            href="/pro"
            className="inline-flex min-h-11 items-center rounded-lg border border-line-strong px-3 text-ink"
            title="Pro mode: the full decision command center and manual tools"
          >
            Pro
          </Link>
        </nav>
      </header>
      <main className="safe-area-pl safe-area-pr safe-area-pb flex-1">{children}</main>
    </div>
  );
}
