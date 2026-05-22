"use client";

/**
 * Phase 14.4 — Notifications dropdown panel.
 *
 * Wraps the bell icon. Opens on click; closes on Esc or outside-click.
 * Pulls items from `composeNotifications()` which composes from
 * existing endpoints (no /notifications endpoint exists).
 *
 * Read-state lives in localStorage per user email. "Mark all read"
 * snapshots the current item IDs; new items naturally re-appear as
 * unread until the next snapshot.
 *
 * Tabs: All / Unread. Empty states are honest — if the underlying
 * endpoints failed, the panel surfaces the per-source error.
 *
 * Owned by skills:
 *   - finrlx-fintech-dashboard-patterns (each item carries source +
 *     severity + freshness)
 *   - finrlx-ui-redesign-director (rule 10 evidence not optional —
 *     per-item source pill)
 *   - fintech-disclaimer-and-marketing-guard (no execution copy in
 *     notification titles or descriptions)
 *   - vercel-web-design-guidelines-mirror (dialog semantics, focus
 *     restoration, Esc, outside-click)
 */
import Link from "next/link";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { Icon } from "@/components/icons/Icon";
import { useAuth } from "@/contexts/AuthContext";
import {
  composeNotifications,
  loadReadIds,
  markAllRead,
  markOneRead,
  type NotificationItem,
  type NotificationSeverity,
} from "@/lib/notifications";
import { fmtDateTime } from "@/lib/format";

type Tab = "all" | "unread";

const SEVERITY_STYLE: Record<NotificationSeverity, { dot: string; chip: string }> = {
  breach: { dot: "bg-breach", chip: "text-breach-soft-ink bg-breach-soft" },
  caution: { dot: "bg-caution", chip: "text-caution-soft-ink bg-caution-soft" },
  governance: { dot: "bg-primary", chip: "text-primary-soft-ink bg-primary-soft" },
  info: { dot: "bg-ink-3", chip: "text-ink-2 bg-surface-3" },
};

export function NotificationsPanel() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("all");
  const [items, setItems] = useState<NotificationItem[] | null>(null);
  const [errors, setErrors] = useState<Array<{ source: string; message: string }>>([]);
  const [readIds, setReadIds] = useState<Set<string>>(new Set());
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const dialogRef = useRef<HTMLDivElement | null>(null);

  // Initial load + load on each open (so a long-open browser session
  // gets fresh data on every bell click). Read-state hydrates from
  // localStorage the moment the user signs in.
  useEffect(() => {
    setReadIds(loadReadIds(user?.email));
  }, [user?.email]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    composeNotifications().then((res) => {
      if (cancelled) return;
      setItems(res.items);
      setErrors(res.errors);
    });
    return () => {
      cancelled = true;
    };
  }, [open]);

  // Outside-click + Esc to close.
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (
        !dialogRef.current?.contains(e.target as Node) &&
        !triggerRef.current?.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        setOpen(false);
        window.setTimeout(() => triggerRef.current?.focus(), 0);
      }
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const unreadIds = useMemo(() => {
    if (!items) return new Set<string>();
    return new Set(items.filter((it) => !readIds.has(it.id)).map((it) => it.id));
  }, [items, readIds]);

  const visible = useMemo<NotificationItem[]>(() => {
    if (!items) return [];
    if (tab === "unread") return items.filter((it) => unreadIds.has(it.id));
    return items;
  }, [items, tab, unreadIds]);

  const handleMarkAllRead = useCallback(() => {
    if (!items) return;
    const ids = items.map((it) => it.id);
    markAllRead(user?.email, ids);
    setReadIds(new Set(ids));
  }, [items, user?.email]);

  const handleItemClick = useCallback(
    (id: string) => {
      markOneRead(user?.email, id);
      setReadIds((prev) => {
        const next = new Set(prev);
        next.add(id);
        return next;
      });
      setOpen(false);
    },
    [user?.email],
  );

  const unreadCount = unreadIds.size;

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={
          unreadCount > 0
            ? `Notifications — ${unreadCount} unread`
            : "Notifications"
        }
        className="hidden md:inline-flex items-center justify-center h-10 w-10 rounded-md hover:bg-surface-3 text-ink-2 transition-colors relative focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <Icon name="bell" size={20} />
        {unreadCount > 0 && (
          <span
            aria-hidden="true"
            className="absolute top-1 right-1 min-w-[16px] h-[16px] px-1 rounded-full bg-breach text-primary-ink text-[10px] font-mono font-semibold flex items-center justify-center"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          ref={dialogRef}
          role="dialog"
          aria-labelledby="notifications-heading"
          // Phase 14.7 — same fix as UserMenu. The inner item list already
          // capped at max-h-[60vh], but the header + tabs + per-source error
          // footer + provenance footer can still push the whole panel past
          // a short viewport. Cap the outer panel at viewport height minus
          // TopBar + gutter and let it scroll inside the rounded container.
          className="absolute right-0 top-[calc(100%+8px)] z-50 w-96 max-w-[calc(100vw-1rem)] max-h-[calc(100vh-5rem)] bg-surface border border-line rounded-xl shadow-lg overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between gap-2 px-4 py-3 border-b border-line">
            <h2 id="notifications-heading" className="text-card-title text-ink">
              Notifications
            </h2>
            <button
              type="button"
              onClick={handleMarkAllRead}
              disabled={unreadCount === 0}
              className="text-meta text-ink-3 hover:text-ink-2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Mark all read
            </button>
          </div>

          {/* Tabs */}
          <div role="tablist" aria-label="Notification filter" className="flex gap-1 px-4 py-2 border-b border-line">
            <TabButton active={tab === "all"} onClick={() => setTab("all")}>
              All{items ? ` (${items.length})` : ""}
            </TabButton>
            <TabButton active={tab === "unread"} onClick={() => setTab("unread")}>
              Unread ({unreadCount})
            </TabButton>
          </div>

          {/* Body */}
          <div className="max-h-[60vh] overflow-y-auto">
            {items === null ? (
              <p className="px-4 py-6 text-body-sm text-ink-3 text-center">Loading…</p>
            ) : visible.length === 0 ? (
              <EmptyState tab={tab} hasItems={items.length > 0} />
            ) : (
              <ul role="list">
                {visible.map((item) => {
                  const isUnread = !readIds.has(item.id);
                  const style = SEVERITY_STYLE[item.severity];
                  return (
                    <li key={item.id}>
                      <Link
                        href={item.href}
                        onClick={() => handleItemClick(item.id)}
                        className={`flex items-start gap-3 px-4 py-3 border-b border-line transition-colors ${
                          isUnread ? "bg-surface" : "bg-surface-2"
                        } hover:bg-surface-3`}
                      >
                        <span
                          aria-hidden="true"
                          className={`shrink-0 mt-1 w-2 h-2 rounded-full ${
                            isUnread ? style.dot : "bg-transparent border border-line"
                          }`}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className={`text-body-sm truncate ${isUnread ? "text-ink font-semibold" : "text-ink-2"}`}>
                              {item.title}
                            </p>
                            <span className={`text-meta px-1.5 py-0.5 rounded-sm font-medium ${style.chip}`}>
                              {item.severity}
                            </span>
                          </div>
                          <p className="text-caption text-ink-3 mt-0.5 line-clamp-2">
                            {item.description}
                          </p>
                          <p className="text-meta text-ink-4 mt-1 font-mono">
                            {item.asOf ? fmtDateTime(item.asOf) : "—"}
                            {" · "}
                            <span className="not-italic">{item.source}</span>
                          </p>
                        </div>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          {/* Errors footer — honest about which endpoints didn't answer */}
          {errors.length > 0 && (
            <div className="px-4 py-2 bg-caution-soft border-t border-caution text-caption text-caution-soft-ink">
              <p className="font-medium">Some sources could not load:</p>
              <ul className="font-mono text-meta mt-0.5">
                {errors.map((e) => (
                  <li key={e.source}>
                    {e.source}: {e.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Footer */}
          <div className="px-4 py-2 bg-surface-2 border-t border-line text-meta text-ink-4 text-center">
            Composed from existing endpoints — no separate notifications service yet.
          </div>
        </div>
      )}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`px-3 py-1.5 rounded-md text-body-sm transition-colors ${
        active
          ? "bg-primary-soft text-primary-soft-ink font-medium"
          : "text-ink-2 hover:bg-surface-3"
      }`}
    >
      {children}
    </button>
  );
}

function EmptyState({ tab, hasItems }: { tab: Tab; hasItems: boolean }) {
  return (
    <div className="px-4 py-8 text-center">
      <Icon name="bell" size={20} className="text-ink-4 mx-auto" />
      <p className="text-body-sm text-ink-2 mt-2">
        {tab === "unread" && hasItems
          ? "No unread notifications."
          : "No notifications right now."}
      </p>
      <p className="text-caption text-ink-4 mt-1 max-w-sm mx-auto leading-snug">
        Pipeline alerts, policy breaches, and published recommendations will appear here.
      </p>
    </div>
  );
}
