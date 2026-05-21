"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "@/components/icons/Icon";
import { AREA_META, AREAS_IN_ORDER } from "@/lib/help/toc";
import type { HelpPage } from "@/lib/help/types";

export function HelpSidebar({ pages }: { pages: HelpPage[] }) {
  const pathname = usePathname() ?? "/help";
  return (
    <nav
      aria-label="Help center navigation"
      className="hidden lg:block w-64 shrink-0 border-r border-line bg-surface overflow-y-auto"
    >
      <div className="p-pad">
        <Link
          href="/help"
          className={`flex items-center gap-2 text-[13px] font-semibold ${
            pathname === "/help" ? "text-primary" : "text-ink"
          }`}
        >
          <Icon name="book-open" size={14} />
          Help center
        </Link>
        <p className="mt-1 text-[12px] text-ink-3">
          Search, learn, and look things up.
        </p>
      </div>
      <ul className="px-pad pb-pad space-y-5">
        {AREAS_IN_ORDER.map((area) => {
          const meta = AREA_META[area];
          const inArea = pages.filter((p) => p.area === area);
          return (
            <li key={area}>
              <div className="text-[10px] uppercase tracking-wider text-ink-4 font-semibold mb-1.5">
                {meta.title}
              </div>
              <ul className="space-y-0.5">
                {inArea.map((p) => {
                  const active = pathname === p.href;
                  return (
                    <li key={p.slug}>
                      <Link
                        href={p.href}
                        className={`block px-2 py-1 rounded text-[13px] leading-5 transition-colors ${
                          active
                            ? "bg-primary-soft text-primary-soft-ink font-medium"
                            : "text-ink-2 hover:bg-surface-2 hover:text-ink"
                        }`}
                        aria-current={active ? "page" : undefined}
                      >
                        {p.frontmatter.title}
                      </Link>
                    </li>
                  );
                })}
                {inArea.length === 0 && (
                  <li className="px-2 py-1 text-[12px] text-ink-4 italic">Coming soon</li>
                )}
              </ul>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
