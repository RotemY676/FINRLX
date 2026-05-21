import { HelpSidebar } from "./HelpSidebar";
import { getAllHelpPages } from "@/lib/help/content";

export function HelpShell({ children }: { children: React.ReactNode }) {
  const pages = getAllHelpPages();
  return (
    <div className="flex min-h-full">
      <HelpSidebar pages={pages} />
      <div className="flex-1 min-w-0">
        <div className="mx-auto max-w-3xl px-pad py-8 lg:py-10">{children}</div>
      </div>
    </div>
  );
}
