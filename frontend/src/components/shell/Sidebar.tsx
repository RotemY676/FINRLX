"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Left navigation sidebar per doc 17 sitemap.
 * Routes: Overview, Decision, Comparison, Replay, Backtests, Paper, Admin.
 */

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: "O" },
  { href: "/decision", label: "Decision", icon: "D" },
  { href: "/comparison", label: "Comparison", icon: "C" },
  { href: "/replay", label: "Replay", icon: "R" },
  { href: "/backtests", label: "Backtests", icon: "B" },
  { href: "/paper", label: "Paper", icon: "P" },
  { href: "/admin", label: "Admin / Ops", icon: "A" },
];

export function Sidebar() {
  const pathname = usePathname() ?? "/";

  return (
    <aside className="w-56 shrink-0 bg-qp-bg-sidebar border-r border-qp-border flex flex-col">
      <div className="p-qp-4 border-b border-qp-border">
        <h1 className="text-qp-h2 text-qp-blue-700 tracking-tight">FINRLX</h1>
        <p className="text-qp-small text-qp-text-muted mt-1">Decision Intelligence</p>
      </div>

      <nav className="flex-1 py-qp-2">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-qp-3 px-qp-4 py-qp-2 mx-qp-2 rounded-qp text-qp-body transition-colors duration-qp ${
                isActive
                  ? "bg-qp-blue-50 text-qp-blue-700 font-medium"
                  : "text-qp-text-secondary hover:bg-qp-bg-hover"
              }`}
            >
              <span
                className={`w-6 h-6 rounded-qp-sm flex items-center justify-center text-qp-small font-mono ${
                  isActive
                    ? "bg-qp-blue-600 text-white"
                    : "bg-qp-border text-qp-text-muted"
                }`}
              >
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-qp-4 border-t border-qp-border">
        <p className="text-qp-small text-qp-text-muted">v0.1.0</p>
      </div>
    </aside>
  );
}
