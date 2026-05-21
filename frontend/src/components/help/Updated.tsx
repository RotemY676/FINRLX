import { Icon } from "@/components/icons/Icon";

export function Updated({ date }: { date?: string }) {
  if (!date) return null;
  const d = new Date(date);
  if (Number.isNaN(d.getTime())) return null;
  const days = Math.floor((Date.now() - d.getTime()) / (1000 * 60 * 60 * 24));
  const fresh = days <= 30;
  const formatted = d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  return (
    <span
      className={`inline-flex items-center gap-1 text-[12px] ${
        fresh ? "text-pos-soft-ink" : "text-ink-3"
      }`}
      title={fresh ? `Updated ${days === 0 ? "today" : `${days} day${days === 1 ? "" : "s"} ago`}` : `Last updated ${formatted}`}
    >
      <Icon name="clock" size={11} />
      {fresh ? "Updated" : "Updated"} {formatted}
    </span>
  );
}
