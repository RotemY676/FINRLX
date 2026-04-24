"use client";

import { Sidebar } from "./Sidebar";

/**
 * Three-zone app shell per doc 17/18:
 * - Left sidebar (navigation)
 * - Central canvas (main content)
 * - Right context pane (future — not implemented in Phase 0)
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-qp-6">{children}</main>
    </div>
  );
}
