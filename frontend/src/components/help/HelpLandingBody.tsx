import Link from "next/link";
import { Icon } from "@/components/icons/Icon";
import { AREA_META, AREAS_IN_ORDER } from "@/lib/help/toc";
import type { HelpPage } from "@/lib/help/types";

const AREA_ICONS: Record<string, string> = {
  "getting-started": "compass",
  concepts: "lightbulb",
  guides: "book-open",
  reference: "list-tree",
  glossary: "search",
  faq: "info",
  troubleshooting: "alert-triangle",
  changelog: "history",
  disclaimers: "info",
};

export function HelpLandingBody({ pages }: { pages: HelpPage[] }) {
  return (
    <div className="mt-4">
      <section aria-labelledby="help-areas" className="mt-4">
        <h2 id="help-areas" className="sr-only">Browse Help</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {AREAS_IN_ORDER.map((area) => {
            const meta = AREA_META[area];
            const inArea = pages.filter((p) => p.area === area);
            const first = inArea[0];
            const href = first ? first.href : "/help";
            return (
              <Link
                key={area}
                href={href}
                className="group block rounded-lg border border-line bg-surface hover:bg-surface-2 hover:border-line-strong transition-colors p-4"
              >
                <div className="flex items-start gap-3">
                  <span className="inline-flex items-center justify-center h-9 w-9 rounded-md bg-primary-soft text-primary-soft-ink shrink-0">
                    <Icon name={AREA_ICONS[area] ?? "info"} size={16} />
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-[15px] font-semibold text-ink m-0">{meta.title}</h3>
                      <span className="text-[11px] text-ink-4">{inArea.length} {inArea.length === 1 ? "page" : "pages"}</span>
                    </div>
                    <p className="mt-1 text-[13px] text-ink-3 leading-5 m-0">{meta.description}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <section aria-labelledby="help-tips" className="mt-8 rounded-lg border border-line bg-surface-2 p-4">
        <h2 id="help-tips" className="text-[13px] font-semibold text-ink uppercase tracking-wider m-0">
          Looking for something specific?
        </h2>
        <ul className="mt-3 grid gap-2 sm:grid-cols-2 text-[13.5px] text-ink-2">
          <li>Click the <strong className="text-ink">?</strong> icon next to any control inside the app to jump here in context.</li>
          <li>The <Link href="/help/glossary" className="text-primary hover:underline">glossary</Link> defines every jargon term in one page.</li>
          <li>Have you completed the <Link href="/onboarding" className="text-primary hover:underline">welcome wizard</Link>? Most defaults come from there.</li>
          <li>Found a problem? Use <Link href="/feedback" className="text-primary hover:underline">Send feedback</Link> — the form is connected to the team.</li>
        </ul>
      </section>
    </div>
  );
}
