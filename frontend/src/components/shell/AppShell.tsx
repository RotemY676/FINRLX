"use client";

import { Sidebar } from "./Sidebar";
import { PaneProvider, ContextPanePanel } from "./ContextPane";

/**
 * Three-zone app shell per doc 17/18:
 * - Left sidebar (navigation)
 * - Central canvas (main content)
 * - Right context pane (contextual detail panels)
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <PaneProvider>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-qp-6">{children}</main>
        <ContextPanePanel />
      </div>
    </PaneProvider>
  );
}
