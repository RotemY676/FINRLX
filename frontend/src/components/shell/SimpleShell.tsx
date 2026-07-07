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

export function SimpleShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <header className="flex items-center gap-4 border-b border-line bg-surface px-4 py-3">
        <Link href="/" className="font-display text-card-title font-semibold tracking-[-0.01em] text-ink">
          FINRLX
        </Link>
        <nav className="ml-auto flex items-center gap-4 text-sm">
          <Link href="/compare" className="text-ink-2 underline-offset-2 hover:underline">
            Compare
          </Link>
          <Link href="/help" className="text-ink-2 underline-offset-2 hover:underline">
            Help
          </Link>
          <Link
            href="/pro"
            className="rounded-lg border border-line-strong px-3 py-1 text-ink"
            title="Pro mode: the full decision command center and manual tools"
          >
            Pro
          </Link>
        </nav>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
