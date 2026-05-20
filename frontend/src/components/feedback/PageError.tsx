import { Icon } from "@/components/icons/Icon";

interface Props {
  title?: string;
  message: string;
  hint?: string;
}

export function PageError({ title, message, hint }: Props) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-breach/30 bg-breach-soft p-pad"
    >
      <div className="flex items-start gap-2">
        <Icon name="alert-triangle" size={16} className="text-breach mt-0.5 shrink-0" aria-hidden="true" />
        <div>
          <h2 className="text-[14px] font-semibold text-breach-soft-ink mb-1">
            {title || "Error"}
          </h2>
          <p className="text-[13px] text-breach-soft-ink/80">{message}</p>
          {/* Hint sits on bg-breach-soft (pink-tinted). text-ink-4 was 4.23 on
              that background — switch to the soft-ink token which is designed
              to contrast with its soft background. */}
          {hint && <p className="text-[11px] text-breach-soft-ink/80 mt-2">{hint}</p>}
        </div>
      </div>
    </div>
  );
}
