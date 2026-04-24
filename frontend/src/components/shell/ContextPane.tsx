"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";

// --- Context pane state management ---

interface PaneState {
  isOpen: boolean;
  title: string;
  content: ReactNode | null;
}

interface PaneContextValue {
  pane: PaneState;
  openPane: (title: string, content: ReactNode) => void;
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
    title: "",
    content: null,
  });

  const openPane = useCallback((title: string, content: ReactNode) => {
    setPane({ isOpen: true, title, content });
  }, []);

  const closePane = useCallback(() => {
    setPane({ isOpen: false, title: "", content: null });
  }, []);

  return (
    <PaneContext.Provider value={{ pane, openPane, closePane }}>
      {children}
    </PaneContext.Provider>
  );
}

// --- Right pane UI ---

export function ContextPanePanel() {
  const { pane, closePane } = usePaneContext();

  // Close on Escape key
  useEffect(() => {
    if (!pane.isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") closePane();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [pane.isOpen, closePane]);

  if (!pane.isOpen) return null;

  return (
    <aside
      className="w-80 shrink-0 border-l border-qp-border bg-qp-bg-card overflow-y-auto flex flex-col"
      role="complementary"
      aria-label="Detail panel"
    >
      {/* Header with clear close affordance */}
      <div className="flex items-center justify-between p-qp-4 border-b border-qp-border bg-qp-bg-sidebar sticky top-0 z-10">
        <h2 className="text-qp-h3 truncate pr-qp-2">{pane.title}</h2>
        <button
          onClick={closePane}
          className="w-7 h-7 flex items-center justify-center rounded-qp-sm
                     bg-qp-border/50 hover:bg-qp-border text-qp-text-secondary hover:text-qp-text-primary
                     transition-colors duration-qp text-base leading-none"
          aria-label="Close panel"
          title="Close (Esc)"
        >
          &times;
        </button>
      </div>

      {/* Content */}
      <div className="p-qp-4 flex-1">
        {pane.content}
      </div>

      {/* Footer hint */}
      <div className="p-qp-3 border-t border-qp-border">
        <p className="text-qp-small text-qp-text-muted text-center">
          Press Esc or click &times; to close
        </p>
      </div>
    </aside>
  );
}
