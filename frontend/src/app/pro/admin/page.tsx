"use client";

import { useEffect, useState } from "react";

import { AdminProvider } from "./_context/AdminContext";
import { AdminShell } from "./_components/AdminShell";
import { ToastProvider } from "./_components/ToastProvider";
import { ActivityProvider } from "./_components/ActivityFeed";

const MOBILE_BREAKPOINT = "(max-width: 767px)";

export default function AdminPage() {
  // Admin is a multi-panel control surface (pipeline canvas, kanban queue,
  // 7-col publication panel, wizard modal, command palette) built for a
  // desktop input model. Rather than half-port it, we show a clear notice on
  // mobile and let the user opt into "view anyway" — which renders the full
  // shell horizontally scrollable.
  const [override, setOverride] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia(MOBILE_BREAKPOINT);
    const sync = () => setIsMobile(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  if (isMobile && !override) {
    return (
      <div className="max-w-md mx-auto py-12 px-4 text-center">
        <h1 className="text-[18px] font-semibold text-ink mb-2">Ops Command — desktop only</h1>
        <p className="text-[13px] text-ink-2 mb-4 leading-relaxed">
          The pipeline canvas, kanban queue, and publication panel are dense
          multi-panel surfaces built for a desktop input model. They don&apos;t
          render usefully at this screen size.
        </p>
        <p className="text-[12.5px] text-ink-3 mb-6">
          Open this view on a desktop browser, or continue anyway — the layout
          will scroll horizontally and some controls will be hard to reach.
        </p>
        <button
          type="button"
          onClick={() => setOverride(true)}
          className="inline-flex items-center justify-center min-h-11 px-4 rounded-md bg-surface-3 text-ink-2 text-[13px] font-medium hover:bg-line transition-colors"
        >
          Continue anyway
        </button>
      </div>
    );
  }

  return (
    <AdminProvider>
      <ToastProvider>
        <ActivityProvider>
          <AdminShell />
        </ActivityProvider>
      </ToastProvider>
    </AdminProvider>
  );
}
