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
import { Icon } from "@/components/icons/Icon";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

type ToastType = "success" | "error" | "info";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  toast: (message: string, type?: ToastType) => void;
}

/* ------------------------------------------------------------------ */
/*  Context                                                            */
/* ------------------------------------------------------------------ */

const ToastContext = createContext<ToastContextValue | null>(null);

/* ------------------------------------------------------------------ */
/*  Style helpers                                                      */
/* ------------------------------------------------------------------ */

const BORDER_COLOR: Record<ToastType, string> = {
  success: "border-l-pos",
  error: "border-l-breach",
  info: "border-l-primary",
};

const ICON_MAP: Record<ToastType, { name: string; className: string }> = {
  success: { name: "check", className: "text-pos" },
  error: { name: "close", className: "text-breach" },
  info: { name: "info", className: "text-primary" },
};

const MAX_VISIBLE = 5;

/* ------------------------------------------------------------------ */
/*  Provider                                                           */
/* ------------------------------------------------------------------ */

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counterRef = useRef(0);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, type: ToastType = "info") => {
      const id = `toast-${++counterRef.current}`;
      setToasts((prev) => {
        const next = [...prev, { id, message, type }];
        // If exceeding max, remove the oldest
        if (next.length > MAX_VISIBLE) {
          return next.slice(next.length - MAX_VISIBLE);
        }
        return next;
      });

      // Auto-dismiss after 4 seconds
      setTimeout(() => dismiss(id), 4000);
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}

      {/* Toast container — fixed bottom-right */}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        <AnimatePresence>
          {toasts.map((t) => {
            const iconMeta = ICON_MAP[t.type];
            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, x: 80 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, transition: { duration: 0.2 } }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className={`pointer-events-auto glass rounded-lg shadow-lg border-l-4 ${BORDER_COLOR[t.type]} flex items-center gap-3 px-4 py-3 min-w-[280px] max-w-[400px]`}
              >
                <Icon
                  name={iconMeta.name}
                  size={16}
                  className={iconMeta.className}
                />
                <span className="text-[12px] text-ink flex-1">{t.message}</span>
                <button
                  onClick={() => dismiss(t.id)}
                  className="text-ink-3 hover:text-ink transition-colors shrink-0"
                  aria-label="Dismiss"
                >
                  <Icon name="close" size={14} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

/* ------------------------------------------------------------------ */
/*  Hook                                                               */
/* ------------------------------------------------------------------ */

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within <ToastProvider>");
  }
  return ctx;
}
