"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Phase 20.4 — universe create/rename dialog.
 *
 * Used for both "New universe" (initial = null) and "Rename" (initial set
 * to the current universe). Closes on submit success, Escape, or backdrop
 * click. The parent owns the actual API call and passes back any 4xx
 * detail via the `error` prop so the dialog can render it inline.
 */
export interface UniverseDialogInitial {
  name: string;
  description: string | null;
}

export function UniverseDialog({
  open,
  mode,
  initial,
  busy,
  error,
  onSubmit,
  onClose,
}: {
  open: boolean;
  mode: "create" | "rename";
  initial?: UniverseDialogInitial | null;
  busy: boolean;
  error: string | null;
  onSubmit: (name: string, description: string) => void;
  onClose: () => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const nameRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(initial?.name ?? "");
    setDescription(initial?.description ?? "");
    // Focus the name field shortly after the modal mounts so the user
    // can start typing without an extra click.
    const t = setTimeout(() => nameRef.current?.focus(), 30);
    return () => clearTimeout(t);
  }, [open, initial]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !busy) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  if (!open) return null;

  const canSubmit = name.trim().length > 0 && !busy;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40"
      role="dialog"
      aria-modal="true"
      aria-labelledby="universe-dialog-title"
      onClick={(e) => {
        // Backdrop click closes — but only if the click started on the
        // backdrop itself, not on the inner card (drag-select edge case).
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <div className="bg-surface border border-line rounded-lg shadow-lg w-full max-w-md p-pad">
        <h2 id="universe-dialog-title" className="text-[15px] font-semibold text-ink mb-1">
          {mode === "create" ? "New universe" : "Rename universe"}
        </h2>
        <p className="text-[12px] text-ink-3 mb-4">
          {mode === "create"
            ? "Universes group assets that pass through the same pipeline."
            : "Update the name or description. Memberships are unchanged."}
        </p>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (canSubmit) onSubmit(name.trim(), description.trim());
          }}
          className="space-y-3"
        >
          <div>
            <label htmlFor="universe-name" className="block text-[12px] text-ink-2 mb-1">
              Name
            </label>
            <input
              id="universe-name"
              ref={nameRef}
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={100}
              required
              className="w-full bg-surface-2 border border-line rounded-md px-3 py-2 text-body text-ink focus:outline-none focus:border-primary"
              placeholder="e.g. US Mid-Cap Tech"
            />
          </div>

          <div>
            <label htmlFor="universe-description" className="block text-[12px] text-ink-2 mb-1">
              Description <span className="text-ink-4">(optional)</span>
            </label>
            <textarea
              id="universe-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={1024}
              rows={3}
              className="w-full bg-surface-2 border border-line rounded-md px-3 py-2 text-body text-ink focus:outline-none focus:border-primary resize-none"
              placeholder="What this universe is for, who it's tuned for, etc."
            />
          </div>

          {error && (
            <div
              className="text-body-sm text-breach-soft-ink bg-breach-soft border border-breach-soft-ink/20 rounded-md p-2"
              role="alert"
            >
              {error}
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={busy}
              className="px-3 py-1.5 rounded-md text-[12px] text-ink-2 hover:bg-surface-3 disabled:opacity-40"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="px-3 py-1.5 rounded-md bg-primary text-primary-ink text-[12px] font-medium hover:opacity-90 disabled:opacity-40"
            >
              {busy
                ? mode === "create"
                  ? "Creating…"
                  : "Saving…"
                : mode === "create"
                ? "Create"
                : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
