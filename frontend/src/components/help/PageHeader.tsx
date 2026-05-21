import { DiataxisBadge } from "./DiataxisBadge";
import { Updated } from "./Updated";
import type { HelpFrontmatter } from "@/lib/help/types";

export function PageHeader({ fm }: { fm: HelpFrontmatter }) {
  return (
    <header className="mb-6">
      <div className="flex items-center gap-2 mb-2">
        <DiataxisBadge kind={fm.diataxis} />
        <Updated date={fm.updated} />
      </div>
      <h1 className="font-display text-[32px] leading-tight font-bold text-ink m-0">
        {fm.title}
      </h1>
      {fm.summary && (
        <p className="mt-2 text-[15px] text-ink-2 leading-7">{fm.summary}</p>
      )}
    </header>
  );
}
