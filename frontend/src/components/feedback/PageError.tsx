import { Icon } from "@/components/icons/Icon";

interface Props {
  title?: string;
  message: string;
  hint?: string;
}

export function PageError({ title, message, hint }: Props) {
  return (
    <div className="rounded-lg border border-breach/30 bg-breach-soft p-pad">
      <div className="flex items-start gap-2">
        <Icon name="alert-triangle" size={16} className="text-breach mt-0.5 shrink-0" />
        <div>
          <h2 className="text-[14px] font-semibold text-breach-soft-ink mb-1">
            {title || "Error"}
          </h2>
          <p className="text-[13px] text-breach-soft-ink/80">{message}</p>
          {hint && <p className="text-[11px] text-ink-4 mt-2">{hint}</p>}
        </div>
      </div>
    </div>
  );
}
