"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "@/components/icons/Icon";

const WORKSPACES = [
  { key: "overview", href: "/", label: "Overview", icon: "overview", badge: "4" },
  { key: "decision", href: "/decision", label: "Decisions", icon: "decision", badge: "12" },
  { key: "comparison", href: "/comparison", label: "Engine comparison", icon: "compare" },
  { key: "risk", href: "#", label: "Risk workspace", icon: "risk", badge: "2" },
  { key: "replay", href: "/replay", label: "Replay & forensics", icon: "replay" },
  { key: "backtests", href: "/backtests", label: "Backtests", icon: "backtest" },
  { key: "paper", href: "/paper", label: "Paper portfolio", icon: "paper" },
  { key: "universe", href: "#", label: "Universe", icon: "universe" },
  { key: "news", href: "#", label: "News intelligence", icon: "news" },
];

const OPS = [
  { key: "admin", href: "/admin", label: "Ops command", icon: "ops", badge: "1" },
];

const SAVED = [
  { label: "Momentum leaders · 3M", tone: "" },
  { label: "Breach watch · concentration", tone: "text-accent" },
  { label: "Fresh changes · today", tone: "text-pos" },
  { label: "Post-mortem cases", tone: "text-breach" },
];

interface SidebarProps {
  collapsed: boolean;
}

export function Sidebar({ collapsed }: SidebarProps) {
  const pathname = usePathname() ?? "/";

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <aside
      className={`shrink-0 border-r border-line bg-surface flex flex-col overflow-y-auto transition-all ${
        collapsed ? "w-14" : "w-52"
      }`}
    >
      {/* Workspaces */}
      <div className="py-2">
        {!collapsed && (
          <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-4">
            Workspaces
          </div>
        )}
        {WORKSPACES.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.key}
              href={item.href}
              className={`flex items-center gap-2.5 px-3 py-1.5 mx-1.5 rounded-md text-[13px] transition-colors ${
                active
                  ? "bg-primary-soft text-primary-soft-ink font-medium"
                  : "text-ink-2 hover:bg-surface-3"
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon name={item.icon} size={16} className={active ? "text-primary" : "text-ink-3"} />
              {!collapsed && (
                <>
                  <span className="flex-1 truncate">{item.label}</span>
                  {item.badge && (
                    <span className={`text-[11px] font-mono min-w-[20px] text-center rounded-sm px-1 ${
                      active ? "text-primary" : "text-ink-4 bg-surface-2"
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </Link>
          );
        })}
      </div>

      {/* Operations */}
      <div className="py-2 border-t border-line">
        {!collapsed && (
          <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-4">
            Operations
          </div>
        )}
        {OPS.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.key}
              href={item.href}
              className={`flex items-center gap-2.5 px-3 py-1.5 mx-1.5 rounded-md text-[13px] transition-colors ${
                active
                  ? "bg-primary-soft text-primary-soft-ink font-medium"
                  : "text-ink-2 hover:bg-surface-3"
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon name={item.icon} size={16} className={active ? "text-primary" : "text-ink-3"} />
              {!collapsed && (
                <>
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span className="text-[11px] font-mono text-ink-4 bg-surface-2 px-1 rounded-sm">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </Link>
          );
        })}
      </div>

      {/* Saved views */}
      {!collapsed && (
        <div className="py-2 border-t border-line mt-auto">
          <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-4">
            Saved views
          </div>
          {SAVED.map((s, i) => (
            <div
              key={i}
              className="flex items-center gap-2 px-3 py-1 mx-1.5 rounded-md text-[12px] text-ink-3 hover:bg-surface-3 cursor-pointer transition-colors"
            >
              <span className={`w-1.5 h-1.5 rounded-full ${s.tone ? "bg-current " + s.tone : "bg-ink-4"}`} />
              <span className="truncate">{s.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Version */}
      {!collapsed && (
        <div className="px-3 py-2 border-t border-line">
          <span className="text-[11px] text-ink-4">v0.2.0</span>
        </div>
      )}
    </aside>
  );
}
