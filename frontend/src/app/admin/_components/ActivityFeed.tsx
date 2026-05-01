"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { motion, AnimatePresence } from "framer-motion";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface ActivityEntry {
  id: string;
  action: string;
  detail?: string;
  status: "success" | "error" | "pending";
  timestamp: Date;
  duration?: number; // ms
  rerunFn?: () => void;
}

export interface ActivityContextValue {
  entries: ActivityEntry[];
  addEntry: (entry: Omit<ActivityEntry, "id" | "timestamp">) => void;
  clearAll: () => void;
  dismissEntry: (id: string) => void;
}

/* ------------------------------------------------------------------ */
/*  Context                                                            */
/* ------------------------------------------------------------------ */

const ActivityContext = createContext<ActivityContextValue | null>(null);

const MAX_ENTRIES = 50;

let _idCounter = 0;
function genId(): string {
  _idCounter += 1;
  return `act_${Date.now()}_${_idCounter}`;
}

/* ------------------------------------------------------------------ */
/*  Provider                                                           */
/* ------------------------------------------------------------------ */

export function ActivityProvider({ children }: { children: ReactNode }) {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);

  const addEntry = useCallback(
    (entry: Omit<ActivityEntry, "id" | "timestamp">) => {
      const newEntry: ActivityEntry = {
        ...entry,
        id: genId(),
        timestamp: new Date(),
      };
      setEntries((prev) => [newEntry, ...prev].slice(0, MAX_ENTRIES));
    },
    [],
  );

  const clearAll = useCallback(() => setEntries([]), []);

  const dismissEntry = useCallback(
    (id: string) => setEntries((prev) => prev.filter((e) => e.id !== id)),
    [],
  );

  return (
    <ActivityContext.Provider value={{ entries, addEntry, clearAll, dismissEntry }}>
      {children}
    </ActivityContext.Provider>
  );
}

/* ------------------------------------------------------------------ */
/*  Hook                                                               */
/* ------------------------------------------------------------------ */

export function useActivity(): ActivityContextValue {
  const ctx = useContext(ActivityContext);
  if (!ctx) {
    throw new Error("useActivity must be used within <ActivityProvider>");
  }
  return ctx;
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function relativeTime(date: Date): string {
  const now = Date.now();
  const diff = now - date.getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const seconds = (ms / 1000).toFixed(1);
  return `${seconds}s`;
}

/* ---- Icons (inline SVG to avoid external deps) ---- */

function ChevronLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 12L6 8L10 4" />
    </svg>
  );
}

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 12L10 8L6 4" />
    </svg>
  );
}

function ChevronDownIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 4.5L6 7.5L9 4.5" />
    </svg>
  );
}

function ActivityIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1 7 4 4 6 6.5 9 2 13 7" />
      <polyline points="1 11 4 8 6 10.5 9 6 13 11" />
    </svg>
  );
}

function RefreshIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 2v3h3" />
      <path d="M11 10V7H8" />
      <path d="M2.5 7.5A4.5 4.5 0 0 1 6 1.5a4.5 4.5 0 0 1 3.5 1.7L11 5" />
      <path d="M9.5 4.5A4.5 4.5 0 0 1 6 10.5a4.5 4.5 0 0 1-3.5-1.7L1 7" />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/*  Status dot                                                         */
/* ------------------------------------------------------------------ */

function StatusDot({ status }: { status: ActivityEntry["status"] }) {
  if (status === "pending") {
    return (
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-caution opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-caution" />
      </span>
    );
  }
  if (status === "error") {
    return <span className="inline-flex rounded-full h-2 w-2 bg-breach" />;
  }
  return <span className="inline-flex rounded-full h-2 w-2 bg-pos" />;
}

/* ------------------------------------------------------------------ */
/*  Activity Block                                                     */
/* ------------------------------------------------------------------ */

function ActivityBlock({
  entry,
  onDismiss,
}: {
  entry: ActivityEntry;
  onDismiss: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  const borderClass =
    entry.status === "error"
      ? "border-l-2 border-l-breach"
      : entry.status === "pending"
        ? "border-l-2 border-l-caution"
        : "border-l-2 border-l-pos";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 40, transition: { duration: 0.15 } }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`rounded-lg border border-line/30 ${borderClass} p-2.5 relative group`}
    >
      {/* Dismiss button */}
      <button
        onClick={() => onDismiss(entry.id)}
        className="absolute top-1.5 right-1.5 text-ink-3 hover:text-ink opacity-0 group-hover:opacity-100 transition-opacity text-[11px] leading-none p-0.5"
        aria-label="Dismiss"
      >
        &times;
      </button>

      {/* Header row */}
      <div className="flex items-center gap-1.5 pr-4">
        <ActivityIcon className="text-ink-3 shrink-0" />
        <span className="text-[12px] font-medium text-ink truncate">{entry.action}</span>
        <span className="ml-auto shrink-0">
          <StatusDot status={entry.status} />
        </span>
      </div>

      {/* Meta row */}
      <div className="flex items-center gap-2 mt-1 text-[11px] text-ink-3">
        <span>{relativeTime(entry.timestamp)}</span>
        {entry.duration != null && (
          <>
            <span className="text-line">|</span>
            <span>{formatDuration(entry.duration)}</span>
          </>
        )}
      </div>

      {/* Detail toggle */}
      {entry.detail && (
        <button
          onClick={() => setExpanded((p) => !p)}
          className="flex items-center gap-1 mt-1.5 text-[11px] text-ink-3 hover:text-ink transition-colors"
        >
          <ChevronDownIcon
            className={`transition-transform duration-150 ${expanded ? "rotate-180" : ""}`}
          />
          <span>Details</span>
        </button>
      )}

      <AnimatePresence initial={false}>
        {expanded && entry.detail && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <pre className="mt-1.5 text-[10px] text-ink-3 bg-surface/50 rounded p-2 whitespace-pre-wrap break-words leading-relaxed border border-line/20">
              {entry.detail}
            </pre>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Re-run button */}
      {entry.rerunFn && (
        <button
          onClick={entry.rerunFn}
          className="flex items-center gap-1 mt-1.5 text-[11px] text-ink-3 hover:text-ink transition-colors"
        >
          <RefreshIcon />
          <span>Re-run</span>
        </button>
      )}
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  ActivityFeed sidebar                                               */
/* ------------------------------------------------------------------ */

export function ActivityFeed() {
  const { entries, clearAll, dismissEntry } = useActivity();
  const [open, setOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  return (
    <>
      {/* Toggle button — always visible at right edge */}
      <button
        onClick={() => setOpen((p) => !p)}
        className="fixed top-1/2 -translate-y-1/2 right-0 z-40 flex items-center justify-center w-6 h-12 rounded-l-md bg-surface border border-r-0 border-line/40 text-ink-3 hover:text-ink hover:bg-surface/80 transition-colors shadow-sm"
        aria-label={open ? "Close activity feed" : "Open activity feed"}
      >
        {open ? <ChevronRightIcon /> : <ChevronLeftIcon />}
      </button>

      {/* Sidebar */}
      <AnimatePresence>
        {open && (
          <motion.aside
            initial={{ x: 320 }}
            animate={{ x: 0 }}
            exit={{ x: 320 }}
            transition={{ type: "spring", stiffness: 400, damping: 34 }}
            className="fixed top-0 right-0 z-30 h-screen w-[320px] glass border-l border-line/30 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-3 border-b border-line/20">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-semibold text-ink">Activity</span>
                {entries.length > 0 && (
                  <span className="text-[10px] bg-surface border border-line/30 text-ink-3 rounded-full px-1.5 py-0.5 leading-none font-medium">
                    {entries.length}
                  </span>
                )}
              </div>
              {entries.length > 0 && (
                <button
                  onClick={clearAll}
                  className="text-[11px] text-ink-3 hover:text-ink transition-colors"
                >
                  Clear all
                </button>
              )}
            </div>

            {/* Entry list */}
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto px-2.5 py-2 space-y-2 scrollbar-thin"
            >
              {entries.length === 0 && (
                <p className="text-[11px] text-ink-3 text-center mt-8">
                  No activity yet.
                </p>
              )}

              <AnimatePresence initial={false}>
                {entries.map((entry) => (
                  <ActivityBlock
                    key={entry.id}
                    entry={entry}
                    onDismiss={dismissEntry}
                  />
                ))}
              </AnimatePresence>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  );
}
