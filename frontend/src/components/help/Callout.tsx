import { Icon } from "@/components/icons/Icon";

type CalloutKind = "note" | "tip" | "warning" | "danger";

const STYLES: Record<CalloutKind, { bg: string; ink: string; ring: string; icon: string; label: string }> = {
  note:    { bg: "bg-primary-soft", ink: "text-primary-soft-ink",  ring: "ring-primary/20",  icon: "info",            label: "Note" },
  tip:     { bg: "bg-pos-soft",     ink: "text-pos-soft-ink",      ring: "ring-pos/20",      icon: "lightbulb",       label: "Tip" },
  warning: { bg: "bg-caution-soft", ink: "text-caution-soft-ink",  ring: "ring-caution/30",  icon: "alert-triangle",  label: "Warning" },
  danger:  { bg: "bg-breach-soft",  ink: "text-breach-soft-ink",   ring: "ring-breach/30",   icon: "alert-triangle",  label: "Important" },
};

export function Callout({
  type = "note",
  title,
  children,
}: {
  type?: CalloutKind;
  title?: string;
  children: React.ReactNode;
}) {
  const s = STYLES[type];
  return (
    <aside
      role="note"
      aria-label={title ?? s.label}
      className={`my-5 rounded-md p-4 ${s.bg} ${s.ink} ring-1 ${s.ring}`}
    >
      <div className="flex items-start gap-2">
        <Icon name={s.icon} size={16} className="mt-0.5 shrink-0" />
        <div className="flex-1 text-[14px] leading-6">
          <div className="font-semibold mb-1">{title ?? s.label}</div>
          <div className="[&>p:first-child]:mt-0 [&>p:last-child]:mb-0">{children}</div>
        </div>
      </div>
    </aside>
  );
}
