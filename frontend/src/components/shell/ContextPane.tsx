"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import { Icon } from "@/components/icons/Icon";

// --- Context pane state management ---

type PaneTab = "risk" | "provenance" | "compare" | "notes" | "detail";

interface PaneState {
  isOpen: boolean;
  activeTab: PaneTab;
  detailTitle: string;
  detailContent: ReactNode | null;
}

interface PaneContextValue {
  pane: PaneState;
  openPane: (title: string, content: ReactNode) => void;
  openTab: (tab: PaneTab) => void;
  closePane: () => void;
}

const PaneContext = createContext<PaneContextValue | null>(null);

export function usePaneContext() {
  const ctx = useContext(PaneContext);
  if (!ctx) throw new Error("usePaneContext must be used within PaneProvider");
  return ctx;
}

export function PaneProvider({ children }: { children: ReactNode }) {
  const [pane, setPane] = useState<PaneState>({
    isOpen: false,
    activeTab: "detail",
    detailTitle: "",
    detailContent: null,
  });

  const openPane = useCallback((title: string, content: ReactNode) => {
    setPane({ isOpen: true, activeTab: "detail", detailTitle: title, detailContent: content });
  }, []);

  const openTab = useCallback((tab: PaneTab) => {
    setPane((prev) => ({ ...prev, isOpen: true, activeTab: tab }));
  }, []);

  const closePane = useCallback(() => {
    setPane((prev) => ({ ...prev, isOpen: false }));
  }, []);

  return (
    <PaneContext.Provider value={{ pane, openPane, openTab, closePane }}>
      {children}
    </PaneContext.Provider>
  );
}

// --- Tabbed context pane UI ---

const TABS: { key: PaneTab; label: string; flag?: boolean }[] = [
  { key: "risk", label: "Risk", flag: true },
  { key: "provenance", label: "Provenance" },
  { key: "compare", label: "Compare" },
  { key: "notes", label: "Notes" },
];

function RiskTab() {
  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-[12px] font-semibold text-ink-2 mb-2">Portfolio impact</h4>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[12.5px]">
          <span className="text-ink-3">Book weight</span><span className="text-ink font-mono">4.2%</span>
          <span className="text-ink-3">Sector (semis)</span><span className="text-caution font-mono">28.1% / 30%</span>
          <span className="text-ink-3">Single-name DDn</span><span className="text-ink font-mono">−8.4%</span>
          <span className="text-ink-3">Portfolio β</span><span className="text-ink font-mono">1.18</span>
          <span className="text-ink-3">Realized vol 30d</span><span className="text-ink font-mono">34.2%</span>
        </div>
      </div>
      <div>
        <h4 className="text-[12px] font-semibold text-ink-2 mb-2">Policy flags</h4>
        <div className="space-y-2">
          <div className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-caution mt-1.5 shrink-0" />
            <div>
              <p className="text-[12.5px] text-ink-2">Sector concentration approaching 30% limit</p>
              <p className="text-[11px] text-ink-4">constraint.semis.weight</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-pos mt-1.5 shrink-0" />
            <div>
              <p className="text-[12.5px] text-ink-2">Liquidity coverage passes</p>
              <p className="text-[11px] text-ink-4">ADV 48.2M shares</p>
            </div>
          </div>
        </div>
      </div>
      <p className="text-[11px] text-ink-4 pt-2 border-t border-line">
        Context pane risk data is illustrative. Real risk data pending backend integration.
      </p>
    </div>
  );
}

function PendingTab({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-32 text-center">
      <p className="text-[13px] text-ink-3">{label} tab</p>
      <p className="text-[11px] text-ink-4 mt-1">Awaiting backend integration</p>
    </div>
  );
}

export function ContextPanePanel() {
  const { pane, openTab, closePane } = usePaneContext();

  useEffect(() => {
    if (!pane.isOpen) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") closePane(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [pane.isOpen, closePane]);

  if (!pane.isOpen) return null;

  return (
    <>
      {/* Mobile-only backdrop. Click to dismiss, mirrors the nav drawer pattern. */}
      <div
        className="md:hidden fixed inset-0 z-30 bg-ink/40 backdrop-blur-sm"
        onClick={closePane}
        aria-hidden="true"
      />

      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Context pane"
        className={[
          // Mobile-first: bottom sheet
          "fixed inset-x-0 bottom-0 z-40 max-h-[85vh] rounded-t-2xl shadow-lg",
          // Desktop (≥md): right-side aside in flow
          "md:static md:inset-auto md:max-h-none md:rounded-none md:shadow-none md:z-auto md:w-[360px] md:shrink-0 md:border-l md:border-line",
          // Shared
          "bg-surface flex flex-col overflow-hidden safe-area-pb",
        ].join(" ")}
      >
        {/* Mobile drag-handle indicator. Not actually draggable yet, but reads as a sheet. */}
        <div className="md:hidden flex justify-center pt-2 pb-1 shrink-0">
          <span aria-hidden="true" className="block h-1 w-10 rounded-full bg-line-strong" />
        </div>

        {/* Tabs / title bar */}
        <div className="flex items-center border-b border-line px-1 shrink-0">
          {pane.activeTab === "detail" ? (
            <div className="flex-1 flex items-center gap-2 px-3 py-2.5 min-w-0">
              <h2 className="text-[13px] font-semibold text-ink truncate">{pane.detailTitle}</h2>
            </div>
          ) : (
            TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => openTab(tab.key)}
                className={`relative px-3 min-h-11 md:min-h-0 md:py-2.5 text-[12.5px] transition-colors ${
                  pane.activeTab === tab.key
                    ? "text-ink font-medium border-b-2 border-primary"
                    : "text-ink-3 hover:text-ink-2"
                }`}
              >
                {tab.label}
                {tab.flag && (
                  <span className="absolute top-2 right-1 w-1.5 h-1.5 rounded-full bg-caution" />
                )}
              </button>
            ))
          )}
          <div className="flex-1" />
          <button
            onClick={closePane}
            className="inline-flex items-center justify-center h-11 w-11 md:h-8 md:w-8 rounded-md hover:bg-surface-3 text-ink-3 mr-1 transition-colors"
            aria-label="Close context pane"
            title="Close (Esc)"
          >
            <Icon name="close" size={16} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {pane.activeTab === "detail" && pane.detailContent}
          {pane.activeTab === "risk" && <RiskTab />}
          {pane.activeTab === "provenance" && <PendingTab label="Provenance" />}
          {pane.activeTab === "compare" && <PendingTab label="Compare" />}
          {pane.activeTab === "notes" && <PendingTab label="Notes" />}
        </div>

        {/* Tab switcher from detail mode */}
        {pane.activeTab === "detail" && (
          <div className="flex items-center gap-1 px-2 py-2 border-t border-line shrink-0">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => openTab(tab.key)}
                className="px-3 min-h-11 md:min-h-0 md:py-1 text-[12px] md:text-[11px] rounded-md text-ink-3 hover:bg-surface-3 transition-colors"
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}
      </aside>
    </>
  );
}
