"use client";

import { useEffect, useState, useCallback } from "react";
import { Command } from "cmdk";
import { motion, AnimatePresence } from "framer-motion";
import { useAdmin } from "../_context/AdminContext";
import { Icon } from "@/components/icons/Icon";
import { PIPELINE_STEPS } from "./constants";

/* ------------------------------------------------------------------ */
/*  Props                                                              */
/* ------------------------------------------------------------------ */

interface CommandPaletteProps {
  onOpenWizard: () => void;
}

/* ------------------------------------------------------------------ */
/*  CommandPalette                                                     */
/* ------------------------------------------------------------------ */

export function CommandPalette({ onOpenWizard }: CommandPaletteProps) {
  const [open, setOpen] = useState(false);
  const {
    setActiveStep,
    filteredQueue,
    dsExportHistory,
    expList,
    ops,
    handleQueueAction,
  } = useAdmin();

  /* ── Keyboard shortcut: Cmd+K / Ctrl+K ── */
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  /* ── Expose open trigger for external callers ── */
  const openPalette = useCallback(() => setOpen(true), []);

  /* ── Derived counts ── */
  const pendingCount = filteredQueue.length;
  const exportCount = dsExportHistory.length;
  const experimentCount = expList.length;
  const incidentCount = ops?.incidents?.filter((i) => i.status === "active").length ?? 0;

  /* ── High-priority items for bulk approve (only those with an id) ── */
  const highPriorityItems = filteredQueue.filter((q) => q.priority === "high" && q.id);

  /* ── Select handler — runs action then closes ── */
  const select = (fn: () => void) => {
    fn();
    setOpen(false);
  };

  /* ── Navigate items ── */
  const navItems = PIPELINE_STEPS.map((step, idx) => ({
    label: `Go to ${step.label}`,
    icon: step.icon as string,
    shortcut: `${idx + 1}`,
    action: () => setActiveStep(idx),
  }));

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[90] flex items-start justify-center pt-[20vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-canvas/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          {/* Palette */}
          <motion.div
            className="relative z-10 w-full max-w-[500px] glass rounded-xl shadow-2xl border border-surface-3 overflow-hidden"
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
          >
            <Command
              label="Command Palette"
              className="flex flex-col"
            >
              {/* Search input */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-surface-3">
                <Icon name="search" size={16} className="text-ink-3 shrink-0" />
                <Command.Input
                  placeholder="Type a command or search..."
                  className="flex-1 bg-transparent text-[13px] text-ink placeholder:text-ink-3 outline-none"
                />
                <kbd className="text-[10px] text-ink-3 bg-surface-3 px-1.5 py-0.5 rounded font-mono">
                  ESC
                </kbd>
              </div>

              {/* Results list */}
              <Command.List className="max-h-[320px] overflow-y-auto p-2">
                <Command.Empty className="px-4 py-8 text-center text-[12px] text-ink-3">
                  No results found.
                </Command.Empty>

                {/* ── Navigate ── */}
                <Command.Group
                  heading="Navigate"
                  className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-ink-3 [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider"
                >
                  {navItems.map((item) => (
                    <Command.Item
                      key={item.label}
                      value={item.label}
                      onSelect={() => select(item.action)}
                      className="flex items-center gap-3 px-3 py-2 rounded-lg text-[12px] text-ink cursor-pointer data-[selected=true]:bg-surface-2 transition-colors"
                    >
                      <Icon name={item.icon} size={14} className="text-ink-2 shrink-0" />
                      <span className="flex-1">{item.label}</span>
                      <kbd className="text-[10px] text-ink-3 bg-surface-3 px-1.5 py-0.5 rounded font-mono">
                        {item.shortcut}
                      </kbd>
                    </Command.Item>
                  ))}
                </Command.Group>

                {/* ── Actions ── */}
                <Command.Group
                  heading="Actions"
                  className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-ink-3 [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider"
                >
                  <Command.Item
                    value="Start Research Workflow"
                    onSelect={() => select(onOpenWizard)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-[12px] text-ink cursor-pointer data-[selected=true]:bg-surface-2 transition-colors"
                  >
                    <Icon name="sparkle" size={14} className="text-ink-2 shrink-0" />
                    <span className="flex-1">Start Research Workflow</span>
                  </Command.Item>

                  {highPriorityItems.length > 0 && (
                    <Command.Item
                      value="Approve All High Priority"
                      onSelect={() =>
                        select(() => {
                          highPriorityItems.forEach((item) => {
                            if (item.id) handleQueueAction(item.id, "approve");
                          });
                        })
                      }
                      className="flex items-center gap-3 px-3 py-2 rounded-lg text-[12px] text-ink cursor-pointer data-[selected=true]:bg-surface-2 transition-colors"
                    >
                      <Icon name="check" size={14} className="text-pos shrink-0" />
                      <span className="flex-1">
                        Approve All High Priority ({highPriorityItems.length})
                      </span>
                    </Command.Item>
                  )}
                </Command.Group>

                {/* ── Quick Info ── */}
                <Command.Group
                  heading="Quick Info"
                  className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-ink-3 [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider"
                >
                  <Command.Item
                    value={`Queue: ${pendingCount} pending`}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-[12px] text-ink-2 cursor-default"
                  >
                    <Icon name="overview" size={14} className="text-ink-3 shrink-0" />
                    <span>Queue: {pendingCount} pending</span>
                  </Command.Item>
                  <Command.Item
                    value={`Exports: ${exportCount}`}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-[12px] text-ink-2 cursor-default"
                  >
                    <Icon name="database" size={14} className="text-ink-3 shrink-0" />
                    <span>Exports: {exportCount}</span>
                  </Command.Item>
                  <Command.Item
                    value={`Experiments: ${experimentCount}`}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-[12px] text-ink-2 cursor-default"
                  >
                    <Icon name="sparkle" size={14} className="text-ink-3 shrink-0" />
                    <span>Experiments: {experimentCount}</span>
                  </Command.Item>
                  <Command.Item
                    value={`Incidents: ${incidentCount} active`}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-[12px] text-ink-2 cursor-default"
                  >
                    <Icon name="alert-triangle" size={14} className="text-ink-3 shrink-0" />
                    <span>Incidents: {incidentCount} active</span>
                  </Command.Item>
                </Command.Group>
              </Command.List>
            </Command>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
