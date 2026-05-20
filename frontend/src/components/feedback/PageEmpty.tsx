import Link from "next/link";

import { Icon } from "@/components/icons/Icon";

interface Props {
  title: string;
  message: string;
  /** Optional Icon name to anchor the empty state visually (e.g. "paper", "replay"). */
  icon?: string;
  /** Optional primary action — surfaced as a button (onClick) or link (href). */
  action?: { label: string; onClick?: () => void; href?: string };
}

export function PageEmpty({ title, message, icon, action }: Props) {
  const ActionEl = action?.href ? (
    <Link
      href={action.href}
      className="inline-flex items-center justify-center min-h-11 px-4 rounded-md bg-primary text-primary-ink text-[13px] font-medium hover:opacity-90 transition-opacity"
    >
      {action.label}
    </Link>
  ) : action?.onClick ? (
    <button
      type="button"
      onClick={action.onClick}
      className="inline-flex items-center justify-center min-h-11 px-4 rounded-md bg-primary text-primary-ink text-[13px] font-medium hover:opacity-90 transition-opacity"
    >
      {action.label}
    </button>
  ) : null;

  return (
    <div className="rounded-lg border border-line bg-surface p-pad text-center py-12 px-4">
      {icon && (
        <div className="flex justify-center mb-3" aria-hidden="true">
          <span className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-surface-3 text-ink-3">
            <Icon name={icon} size={22} />
          </span>
        </div>
      )}
      <h2 className="text-[15px] font-semibold text-ink mb-1">{title}</h2>
      <p className="text-[13px] text-ink-3 max-w-md mx-auto">{message}</p>
      {ActionEl && <div className="mt-5 flex justify-center">{ActionEl}</div>}
    </div>
  );
}
