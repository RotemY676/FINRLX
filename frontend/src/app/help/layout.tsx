import type { Metadata } from "next";

export const metadata: Metadata = {
  title: { default: "Help center · FINRLX", template: "%s · Help · FINRLX" },
  description: "Tutorials, concepts, how-to guides, and reference for the FINRLX decision-intelligence workspace.",
};

export default function HelpLayout({ children }: { children: React.ReactNode }) {
  return <div className="bg-canvas min-h-full">{children}</div>;
}
