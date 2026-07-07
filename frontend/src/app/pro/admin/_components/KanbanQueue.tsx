"use client";

import { useState, useCallback, type DragEvent } from "react";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import type { OpsQueueItem } from "@/services/api";
import { STANCE_STYLE, PRIORITY_STYLE } from "./constants";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

type QueueAction = "approve" | "defer" | "challenge";

interface KanbanQueueProps {
  queue: OpsQueueItem[];
  onAction: (id: string, action: QueueAction) => Promise<void>;
  actionLoading: string | null;
}

type ColumnKey = "pending" | "approved" | "deferred" | "challenged";

interface ColumnDef {
  key: ColumnKey;
  label: string;
  action: QueueAction | null;
  borderColor: string;
  headerBg: string;
  dropGlow: string;
}

const COLUMNS: ColumnDef[] = [
  {
    key: "pending",
    label: "Pending",
    action: null,
    borderColor: "border-ink-3/40",
    headerBg: "bg-surface-3/60",
    dropGlow: "ring-ink-3/30",
  },
  {
    key: "approved",
    label: "Approved",
    action: "approve",
    borderColor: "border-pos/60",
    headerBg: "bg-pos/10",
    dropGlow: "ring-pos/40",
  },
  {
    key: "deferred",
    label: "Deferred",
    action: "defer",
    borderColor: "border-caution/60",
    headerBg: "bg-caution/10",
    dropGlow: "ring-caution/40",
  },
  {
    key: "challenged",
    label: "Challenged",
    action: "challenge",
    borderColor: "border-breach/60",
    headerBg: "bg-breach/10",
    dropGlow: "ring-breach/40",
  },
];

const COLUMN_HEADER_BADGE: Record<ColumnKey, string> = {
  pending: "bg-surface-3 text-ink-2",
  approved: "bg-pos/20 text-pos",
  deferred: "bg-caution/20 text-caution",
  challenged: "bg-breach/20 text-breach",
};

const PRIORITY_DOT: Record<string, string> = {
  high: "bg-breach",
  mid: "bg-caution",
  low: "bg-ink-3",
};

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function getItemId(item: OpsQueueItem): string {
  return item.id ?? item.recommendation_id;
}

/* ------------------------------------------------------------------ */
/*  Kanban Card                                                        */
/* ------------------------------------------------------------------ */

function KanbanCard({
  item,
  isLoading,
  onDragStart,
}: {
  item: OpsQueueItem;
  isLoading: boolean;
  onDragStart: (e: DragEvent<HTMLDivElement>, item: OpsQueueItem) => void;
}) {
  const stanceClass = STANCE_STYLE[item.stance] ?? "text-ink-3 bg-surface-3";

  return (
    <motion.div
      layout
      layoutId={getItemId(item)}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
      transition={{ type: "spring", stiffness: 400, damping: 30 }}
      draggable={!isLoading}
      onDragStart={(e) => onDragStart(e as unknown as DragEvent<HTMLDivElement>, item)}
      className={`
        glass rounded-lg p-3 cursor-grab active:cursor-grabbing
        border border-white/5 shadow-sm hover:shadow-md
        transition-shadow select-none
        ${isLoading ? "opacity-50 pointer-events-none" : ""}
      `}
    >
      {/* Top row: ticker + stance */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-sm font-bold text-ink tracking-wide">
          {item.ticker}
        </span>
        <span
          className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${stanceClass}`}
        >
          {item.stance}
        </span>
      </div>

      {/* Metrics row */}
      <div className="flex items-center gap-3 text-[11px] text-ink-2 mb-2">
        <span>
          Conf&nbsp;
          <span className="text-ink font-medium">
            {(item.confidence * 100).toFixed(0)}%
          </span>
        </span>
        <span>
          Wt&nbsp;
          <span className="text-ink font-medium">{item.weight}</span>
        </span>
      </div>

      {/* Submitter + priority */}
      <div className="flex items-center justify-between text-[11px] text-ink-3">
        <span className="truncate max-w-[110px]">{item.submitter}</span>
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${PRIORITY_DOT[item.priority] ?? "bg-ink-3"}`}
          />
          <span className={PRIORITY_STYLE[item.priority] ?? "text-ink-3"}>
            {item.priority}
          </span>
        </div>
      </div>

      {/* Flags */}
      {item.flags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {item.flags.map((f) => (
            <span
              key={f}
              className="text-[9px] px-1.5 py-0.5 rounded bg-caution/15 text-caution font-medium"
            >
              {f}
            </span>
          ))}
        </div>
      )}

      {isLoading && (
        <div className="mt-2 flex items-center gap-1 text-[10px] text-ink-3">
          <motion.span
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
            className="inline-block w-3 h-3 border border-ink-3 border-t-transparent rounded-full"
          />
          Processing...
        </div>
      )}
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Table Row (for table view)                                         */
/* ------------------------------------------------------------------ */

function TableView({
  items,
  onAction,
  actionLoading,
  actionedItems,
}: {
  items: OpsQueueItem[];
  onAction: (id: string, action: QueueAction) => Promise<void>;
  actionLoading: string | null;
  actionedItems: Map<string, ColumnKey>;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-ink-3 border-b border-white/5">
            <th className="text-left py-2 px-3 font-medium">Ticker</th>
            <th className="text-left py-2 px-3 font-medium">Stance</th>
            <th className="text-left py-2 px-3 font-medium">Confidence</th>
            <th className="text-left py-2 px-3 font-medium">Weight</th>
            <th className="text-left py-2 px-3 font-medium">Priority</th>
            <th className="text-left py-2 px-3 font-medium">Submitter</th>
            <th className="text-left py-2 px-3 font-medium">Flags</th>
            <th className="text-left py-2 px-3 font-medium">Status</th>
            <th className="text-right py-2 px-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <AnimatePresence>
            {items.map((item) => {
              const id = getItemId(item);
              const isLoading = actionLoading === id;
              const actionedTo = actionedItems.get(id);
              const statusLabel = actionedTo
                ? actionedTo.charAt(0).toUpperCase() + actionedTo.slice(1)
                : "Pending";

              return (
                <motion.tr
                  key={id}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className={`border-b border-white/5 ${isLoading ? "opacity-50" : ""}`}
                >
                  <td className="py-2 px-3 font-bold text-ink">{item.ticker}</td>
                  <td className="py-2 px-3">
                    <span
                      className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${STANCE_STYLE[item.stance] ?? "text-ink-3 bg-surface-3"}`}
                    >
                      {item.stance}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-ink-2">
                    {(item.confidence * 100).toFixed(0)}%
                  </td>
                  <td className="py-2 px-3 text-ink-2">{item.weight}</td>
                  <td className="py-2 px-3">
                    <span className="flex items-center gap-1">
                      <span
                        className={`w-2 h-2 rounded-full ${PRIORITY_DOT[item.priority] ?? "bg-ink-3"}`}
                      />
                      <span className={PRIORITY_STYLE[item.priority] ?? "text-ink-3"}>
                        {item.priority}
                      </span>
                    </span>
                  </td>
                  <td className="py-2 px-3 text-ink-3">{item.submitter}</td>
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap gap-1">
                      {item.flags.map((f) => (
                        <span
                          key={f}
                          className="text-[9px] px-1 py-0.5 rounded bg-caution/15 text-caution"
                        >
                          {f}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-2 px-3 text-ink-2">{statusLabel}</td>
                  <td className="py-2 px-3 text-right">
                    {!actionedTo && (
                      <div className="flex items-center justify-end gap-1">
                        <button
                          disabled={isLoading}
                          onClick={() => onAction(id, "approve")}
                          className="px-2 py-1 rounded text-[10px] font-medium bg-pos/15 text-pos hover:bg-pos/25 transition-colors disabled:opacity-40"
                        >
                          Approve
                        </button>
                        <button
                          disabled={isLoading}
                          onClick={() => onAction(id, "defer")}
                          className="px-2 py-1 rounded text-[10px] font-medium bg-caution/15 text-caution hover:bg-caution/25 transition-colors disabled:opacity-40"
                        >
                          Defer
                        </button>
                        <button
                          disabled={isLoading}
                          onClick={() => onAction(id, "challenge")}
                          className="px-2 py-1 rounded text-[10px] font-medium bg-breach/15 text-breach hover:bg-breach/25 transition-colors disabled:opacity-40"
                        >
                          Challenge
                        </button>
                      </div>
                    )}
                  </td>
                </motion.tr>
              );
            })}
          </AnimatePresence>
        </tbody>
      </table>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Kanban Queue Component                                        */
/* ------------------------------------------------------------------ */

export default function KanbanQueue({
  queue,
  onAction,
  actionLoading,
}: KanbanQueueProps) {
  const [view, setView] = useState<"kanban" | "table">("kanban");
  const [draggedItem, setDraggedItem] = useState<OpsQueueItem | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<ColumnKey | null>(null);
  const [actionedItems, setActionedItems] = useState<Map<string, ColumnKey>>(
    new Map(),
  );

  /* ── Drag handlers ── */

  const handleDragStart = useCallback(
    (e: DragEvent<HTMLDivElement>, item: OpsQueueItem) => {
      setDraggedItem(item);
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", getItemId(item));
      // Make drag image slightly transparent
      if (e.currentTarget instanceof HTMLElement) {
        e.currentTarget.style.opacity = "0.5";
      }
    },
    [],
  );

  const handleDragOver = useCallback(
    (e: DragEvent<HTMLDivElement>, colKey: ColumnKey) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      setDragOverColumn(colKey);
    },
    [],
  );

  const handleDragLeave = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      // Only clear if leaving the column entirely (not entering a child)
      const related = e.relatedTarget as Node | null;
      if (!e.currentTarget.contains(related)) {
        setDragOverColumn(null);
      }
    },
    [],
  );

  const handleDrop = useCallback(
    async (e: DragEvent<HTMLDivElement>, col: ColumnDef) => {
      e.preventDefault();
      setDragOverColumn(null);

      if (!draggedItem || !col.action) return;

      const id = getItemId(draggedItem);
      const currentColumn = actionedItems.get(id);

      // Can't drop on pending or on the same column
      if (col.key === "pending" || col.key === currentColumn) {
        setDraggedItem(null);
        return;
      }

      // Optimistically move card to target column
      setActionedItems((prev) => {
        const next = new Map(prev);
        next.set(id, col.key);
        return next;
      });

      setDraggedItem(null);

      try {
        await onAction(id, col.action);
      } catch {
        // Revert on failure
        setActionedItems((prev) => {
          const next = new Map(prev);
          next.delete(id);
          return next;
        });
      }
    },
    [draggedItem, actionedItems, onAction],
  );

  const handleDragEnd = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      if (e.currentTarget instanceof HTMLElement) {
        e.currentTarget.style.opacity = "1";
      }
      setDraggedItem(null);
      setDragOverColumn(null);
    },
    [],
  );

  /* ── Build column data ── */

  const columnItems: Record<ColumnKey, OpsQueueItem[]> = {
    pending: [],
    approved: [],
    deferred: [],
    challenged: [],
  };

  for (const item of queue) {
    const id = getItemId(item);
    const target = actionedItems.get(id) ?? "pending";
    columnItems[target].push(item);
  }

  /* ── Handle action from table view ── */

  const handleTableAction = useCallback(
    async (id: string, action: QueueAction) => {
      const colKey: ColumnKey =
        action === "approve"
          ? "approved"
          : action === "defer"
            ? "deferred"
            : "challenged";

      setActionedItems((prev) => {
        const next = new Map(prev);
        next.set(id, colKey);
        return next;
      });

      try {
        await onAction(id, action);
      } catch {
        setActionedItems((prev) => {
          const next = new Map(prev);
          next.delete(id);
          return next;
        });
      }
    },
    [onAction],
  );

  /* ── Render ── */

  return (
    <div className="space-y-3">
      {/* View toggle */}
      <div className="flex items-center justify-end gap-1">
        <button
          onClick={() => setView("kanban")}
          className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
            view === "kanban"
              ? "bg-accent/15 text-accent"
              : "text-ink-3 hover:text-ink-2"
          }`}
        >
          Board
        </button>
        <button
          onClick={() => setView("table")}
          className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
            view === "table"
              ? "bg-accent/15 text-accent"
              : "text-ink-3 hover:text-ink-2"
          }`}
        >
          Table
        </button>
      </div>

      {view === "table" ? (
        <TableView
          items={queue}
          onAction={handleTableAction}
          actionLoading={actionLoading}
          actionedItems={actionedItems}
        />
      ) : (
        <LayoutGroup>
          <div className="grid grid-cols-4 gap-3">
            {COLUMNS.map((col) => {
              const items = columnItems[col.key];
              const isOver = dragOverColumn === col.key;
              const canDrop = col.key !== "pending" && draggedItem !== null;

              return (
                <div
                  key={col.key}
                  onDragOver={(e) => handleDragOver(e, col.key)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, col)}
                  className={`
                    rounded-xl border-t-2 ${col.borderColor}
                    bg-surface-2/40 backdrop-blur-sm
                    min-h-[300px] flex flex-col
                    transition-all duration-200
                    ${isOver && canDrop ? `ring-2 ${col.dropGlow} bg-surface-2/70` : ""}
                  `}
                >
                  {/* Column header */}
                  <div
                    className={`
                      flex items-center justify-between px-3 py-2.5
                      rounded-t-xl ${col.headerBg}
                    `}
                  >
                    <span className="text-xs font-semibold text-ink">
                      {col.label}
                    </span>
                    <span
                      className={`
                        text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[20px] text-center
                        ${COLUMN_HEADER_BADGE[col.key]}
                      `}
                    >
                      {items.length}
                    </span>
                  </div>

                  {/* Cards */}
                  <div className="flex-1 p-2 space-y-2 overflow-y-auto max-h-[520px]">
                    <AnimatePresence mode="popLayout">
                      {items.map((item) => (
                        <KanbanCard
                          key={getItemId(item)}
                          item={item}
                          isLoading={actionLoading === getItemId(item)}
                          onDragStart={handleDragStart}
                        />
                      ))}
                    </AnimatePresence>

                    {/* Empty state */}
                    {items.length === 0 && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-center justify-center h-24 text-[11px] text-ink-3/50"
                      >
                        {col.key === "pending"
                          ? "Queue empty"
                          : "Drop cards here"}
                      </motion.div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </LayoutGroup>
      )}
    </div>
  );
}
