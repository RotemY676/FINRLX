"use client";

import { useState } from "react";
import { TopBar } from "./TopBar";
import { Sidebar } from "./Sidebar";
import { PaneProvider, ContextPanePanel } from "./ContextPane";
import { DisclaimerBanner } from "../legal/DisclaimerBanner";
import { DisclaimerModal } from "../legal/DisclaimerModal";

/**
 * Three-zone app shell per design handoff:
 * - TopBar (brand, breadcrumbs, scope chips, search, notifications, avatar)
 * - Left sidebar (navigation, collapsible)
 * - Central canvas (main content)
 * - Right context pane (tabbed: Risk/Provenance/Compare/Notes + detail panels)
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const [navCollapsed, setNavCollapsed] = useState(false);
  const [ctxVisible, setCtxVisible] = useState(false);

  return (
    <PaneProvider>
      <DisclaimerModal />
      <div className="flex flex-col h-screen overflow-hidden">
        <TopBar
          onToggleNav={() => setNavCollapsed((p) => !p)}
          onToggleCtx={() => setCtxVisible((p) => !p)}
          ctxVisible={ctxVisible}
        />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar collapsed={navCollapsed} />
          <main className="flex-1 overflow-y-auto p-pad bg-canvas">
            {children}
          </main>
          {ctxVisible && <ContextPanePanel />}
        </div>
        <DisclaimerBanner />
      </div>
    </PaneProvider>
  );
}
