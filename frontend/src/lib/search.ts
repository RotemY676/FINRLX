/**
 * Phase 14.3 — Command palette search composer.
 *
 * No new backend endpoints. Results are composed from data already
 * available to the frontend:
 *   - Routes: hardcoded list mirroring the Phase 4 sidebar AREAS.
 *   - Tickers: if the query parses as a valid symbol, offer a deep-link
 *     to /research/[ticker]. The actual ticker existence check happens
 *     when the user lands on /research/[ticker]; we do not pretend the
 *     symbol is valid here.
 *   - Operator analyses: filtered from listOperatorAnalyses() when the
 *     user is authenticated. Skipped silently if the call fails
 *     (no auth, network, or backend down).
 *
 * Categories that are NOT included and why:
 *   - Recommendations list: backend exposes /current but not a list
 *     endpoint typed on the frontend; surfacing a single "current" rec
 *     in a search results UI would be misleading.
 *   - Help articles: MDX content lives under frontend/src/content/help/**
 *     but there's no runtime index. Adding an index requires a build
 *     step; out of 14.3 scope.
 *
 * Recent searches are stored in localStorage per browser, keyed by the
 * raw query string.
 */

import type { OperatorAnalysis } from "@/services/operatorApi";

export type SearchCategory = "route" | "ticker" | "operator" | "recent";

export interface SearchResult {
  id: string;
  category: SearchCategory;
  label: string;
  /** Optional secondary line (path, source, timestamp). */
  description?: string;
  /** Where to navigate when the user picks this result. */
  href: string;
  /** Optional icon name from the Icon component. */
  icon?: string;
}

interface RouteEntry {
  label: string;
  href: string;
  area: string;
  icon: string;
  /** Extra keywords to widen matching beyond the visible label. */
  keywords?: ReadonlyArray<string>;
}

const ROUTES: ReadonlyArray<RouteEntry> = [
  { label: "Home", href: "/", area: "Home", icon: "overview", keywords: ["dashboard", "command center"] },
  { label: "Research hub", href: "/research", area: "Research", icon: "search" },
  { label: "Universe", href: "/universe", area: "Research", icon: "universe", keywords: ["coverage", "readiness"] },
  { label: "Backtests", href: "/backtests", area: "Research", icon: "backtest" },
  { label: "Current recommendation", href: "/decision", area: "Decisions", icon: "decision", keywords: ["recommendation", "thesis"] },
  { label: "Engine comparison", href: "/comparison", area: "Decisions", icon: "compare" },
  { label: "Replay & forensics", href: "/replay", area: "Decisions", icon: "replay" },
  { label: "Templates", href: "/templates", area: "Decisions", icon: "layers" },
  { label: "Paper portfolio", href: "/paper", area: "Portfolio & Risk", icon: "paper" },
  { label: "Risk workspace", href: "/risk", area: "Portfolio & Risk", icon: "risk" },
  { label: "News intelligence", href: "/news", area: "Insights", icon: "news" },
  { label: "Ops command", href: "/ops", area: "Ops & Governance", icon: "ops" },
  { label: "Policies", href: "/policies", area: "Ops & Governance", icon: "check" },
  { label: "Integrations", href: "/integrations", area: "Ops & Governance", icon: "database" },
  { label: "Research lab", href: "/admin", area: "Ops & Governance", icon: "compare", keywords: ["wizard", "pipeline canvas", "kanban"] },
  { label: "Operator console", href: "/operator", area: "Ops & Governance", icon: "user" },
  { label: "My profile", href: "/profile", area: "Settings", icon: "user" },
  { label: "Help center", href: "/help", area: "Settings", icon: "help-circle" },
  { label: "Send feedback", href: "/feedback", area: "Settings", icon: "message" },
];

const TICKER_RE = /^[A-Z]{1,8}(\.[A-Z]{1,4})?$/;

function normalize(q: string): string {
  return q.trim().toLowerCase();
}

function matches(label: string, keywords: ReadonlyArray<string> | undefined, n: string): boolean {
  if (label.toLowerCase().includes(n)) return true;
  if (keywords?.some((k) => k.toLowerCase().includes(n))) return true;
  return false;
}

export function searchRoutes(query: string): SearchResult[] {
  const n = normalize(query);
  if (!n) {
    // Surface a curated top-7 list when the input is empty so the
    // palette doesn't read as a blank "ask anything" surface (rule 3
    // of finrlx-ai-ux-governance).
    const featured = ["/", "/research", "/decision", "/paper", "/risk", "/news", "/ops"];
    return ROUTES.filter((r) => featured.includes(r.href)).map(routeToResult);
  }
  return ROUTES.filter((r) => matches(r.label, r.keywords, n) || r.area.toLowerCase().includes(n))
    .map(routeToResult);
}

function routeToResult(r: RouteEntry): SearchResult {
  return {
    id: `route:${r.href}`,
    category: "route",
    label: r.label,
    description: r.area,
    href: r.href,
    icon: r.icon,
  };
}

export function searchTicker(query: string): SearchResult | null {
  const upper = query.trim().toUpperCase();
  if (!upper) return null;
  if (!TICKER_RE.test(upper)) return null;
  return {
    id: `ticker:${upper}`,
    category: "ticker",
    label: upper,
    description: "Open research workspace",
    href: `/research/${upper}`,
    icon: "search",
  };
}

export function searchOperatorAnalyses(
  analyses: ReadonlyArray<OperatorAnalysis>,
  query: string,
  limit = 5,
): SearchResult[] {
  const n = normalize(query);
  if (!n) return [];
  return analyses
    .filter(
      (a) =>
        (a.prompt && a.prompt.toLowerCase().includes(n)) ||
        a.response.toLowerCase().includes(n) ||
        (a.note && a.note.toLowerCase().includes(n)) ||
        (a.recommendation_id && a.recommendation_id.toLowerCase().includes(n)),
    )
    .slice(0, limit)
    .map<SearchResult>((a) => ({
      id: `operator:${a.id}`,
      category: "operator",
      label: a.prompt?.slice(0, 60) || a.response.slice(0, 60),
      description: `${a.source} · ${a.surface}${a.recommendation_id ? ` · ${a.recommendation_id.slice(0, 8)}` : ""}`,
      href: `/operator?id=${encodeURIComponent(a.id)}`,
      icon: "message",
    }));
}

// ── Recent searches (localStorage) ─────────────────────────────────────

const RECENT_KEY = "finrlx-palette-recent";
const RECENT_LIMIT = 8;

export function loadRecent(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(RECENT_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    if (!Array.isArray(arr)) return [];
    return arr.filter((x): x is string => typeof x === "string").slice(0, RECENT_LIMIT);
  } catch {
    return [];
  }
}

export function recordRecent(query: string): void {
  if (typeof window === "undefined") return;
  const trimmed = query.trim();
  if (!trimmed) return;
  const prev = loadRecent().filter((q) => q.toLowerCase() !== trimmed.toLowerCase());
  const next = [trimmed, ...prev].slice(0, RECENT_LIMIT);
  try {
    window.localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  } catch {
    // ignore storage failures (quota, private mode)
  }
}

export function clearRecent(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(RECENT_KEY);
  } catch {
    // ignore
  }
}
