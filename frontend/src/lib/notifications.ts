/**
 * Phase 14.4 — Notifications composer.
 *
 * Composes notifications from data the frontend already has access to.
 * No new backend endpoint, no `/api/v1/notifications`. Sources:
 *
 *   - `fetchOps()` → active breaches (caution / breach severity) and
 *     active incidents become notifications.
 *   - `fetchOverview()` → recently-published recommendation becomes a
 *     "New recommendation published" item.
 *
 * Read-state lives in `localStorage` keyed by user email so multi-
 * profile browsers do not leak read-state between accounts. When the
 * key is missing (signed-out, browser cleared), nothing is read.
 *
 * Anti-patterns this composer avoids:
 *   - Inventing notifications when both calls fail. The panel renders
 *     an honest empty state instead.
 *   - Marking a non-existent endpoint as the "source of truth" — the
 *     composer notes the source endpoint on each item.
 *   - Auto-marking everything read; the user has to act.
 */

import {
  fetchOps,
  fetchOverview,
  type OpsBreach,
  type OpsIncident,
  type OverviewData,
} from "@/services/api";

export type NotificationSeverity = "info" | "caution" | "breach" | "governance";

export interface NotificationItem {
  id: string;
  severity: NotificationSeverity;
  title: string;
  description: string;
  /** ISO timestamp of the underlying event, or null if unknown. */
  asOf: string | null;
  /** Where the user should land to act on this item. */
  href: string;
  /** Endpoint that contributed this item — surfaced for provenance. */
  source: string;
  /** Optional icon hint. */
  icon: string;
}

interface ComposeResult {
  items: NotificationItem[];
  /** Per-source errors, surfaced honestly in the panel footer. */
  errors: Array<{ source: string; message: string }>;
}

function mapOpsBreachSeverity(s: string): NotificationSeverity {
  const lower = (s || "").toLowerCase();
  if (lower === "critical" || lower === "breach" || lower === "high") return "breach";
  if (lower === "warning" || lower === "caution" || lower === "medium") return "caution";
  return "info";
}

function mapOpsIncidentSeverity(s: string): NotificationSeverity {
  return mapOpsBreachSeverity(s);
}

function breachToNotification(b: OpsBreach, idx: number): NotificationItem {
  return {
    id: `breach:${b.kind}:${idx}`,
    severity: mapOpsBreachSeverity(b.severity),
    title: b.label,
    description: `Utilisation ${(b.utilization * 100).toFixed(0)}% — trend ${b.trend} — related ${b.related}`,
    asOf: null,
    href: "/pro/ops",
    source: "/api/v1/ops",
    icon: "risk",
  };
}

function incidentToNotification(i: OpsIncident): NotificationItem {
  return {
    id: `incident:${i.id}`,
    severity: mapOpsIncidentSeverity(i.severity),
    title: i.title,
    description: `${i.owner} · ${i.status}${i.affected_recs ? ` · ${i.affected_recs} affected` : ""}`,
    asOf: i.started || null,
    href: "/pro/ops",
    source: "/api/v1/ops",
    icon: "alert-triangle",
  };
}

function overviewToNotification(o: OverviewData): NotificationItem | null {
  if (!o.current_recommendation || !o.last_published_at) return null;
  const rec = o.current_recommendation;
  return {
    id: `overview:rec:${rec.id}`,
    severity: "governance",
    title: "New recommendation published",
    description: `${rec.total_positions} position${rec.total_positions === 1 ? "" : "s"} · status ${rec.status}`,
    asOf: o.last_published_at,
    href: "/pro/decision",
    source: "/api/v1/overview",
    icon: "decision",
  };
}

export async function composeNotifications(): Promise<ComposeResult> {
  const errors: Array<{ source: string; message: string }> = [];
  const items: NotificationItem[] = [];

  const [opsRes, overviewRes] = await Promise.allSettled([
    fetchOps(),
    fetchOverview(),
  ]);

  if (opsRes.status === "fulfilled") {
    const data = opsRes.value.data;
    data.breaches.forEach((b, idx) => items.push(breachToNotification(b, idx)));
    data.incidents
      .filter((i) => (i.status || "").toLowerCase() !== "resolved")
      .forEach((i) => items.push(incidentToNotification(i)));
  } else {
    errors.push({
      source: "/api/v1/ops",
      message: opsRes.reason instanceof Error ? opsRes.reason.message : String(opsRes.reason),
    });
  }

  if (overviewRes.status === "fulfilled") {
    const n = overviewToNotification(overviewRes.value.data);
    if (n) items.push(n);
  } else {
    errors.push({
      source: "/api/v1/overview",
      message: overviewRes.reason instanceof Error ? overviewRes.reason.message : String(overviewRes.reason),
    });
  }

  // Sort: breach first, then caution, then governance, then info; within
  // a tier, newest first.
  const order: Record<NotificationSeverity, number> = {
    breach: 0,
    caution: 1,
    governance: 2,
    info: 3,
  };
  items.sort((a, b) => {
    const d = order[a.severity] - order[b.severity];
    if (d !== 0) return d;
    if (a.asOf && b.asOf) return a.asOf < b.asOf ? 1 : -1;
    return 0;
  });

  return { items, errors };
}

// ── Read-state (localStorage) ─────────────────────────────────────────

function readKey(userEmail: string | null | undefined): string | null {
  if (!userEmail) return null;
  return `finrlx-notifications-read:${userEmail.toLowerCase()}`;
}

export function loadReadIds(userEmail: string | null | undefined): Set<string> {
  if (typeof window === "undefined") return new Set();
  const key = readKey(userEmail);
  if (!key) return new Set();
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return new Set();
    const arr = JSON.parse(raw);
    if (!Array.isArray(arr)) return new Set();
    return new Set(arr.filter((x): x is string => typeof x === "string"));
  } catch {
    return new Set();
  }
}

export function markAllRead(
  userEmail: string | null | undefined,
  itemIds: ReadonlyArray<string>,
): void {
  if (typeof window === "undefined") return;
  const key = readKey(userEmail);
  if (!key) return;
  try {
    window.localStorage.setItem(key, JSON.stringify(itemIds));
  } catch {
    // ignore
  }
}

export function markOneRead(
  userEmail: string | null | undefined,
  itemId: string,
): void {
  if (typeof window === "undefined") return;
  const key = readKey(userEmail);
  if (!key) return;
  const current = loadReadIds(userEmail);
  current.add(itemId);
  try {
    window.localStorage.setItem(key, JSON.stringify(Array.from(current)));
  } catch {
    // ignore
  }
}
