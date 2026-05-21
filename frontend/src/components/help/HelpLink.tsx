import Link from "next/link";
import { Icon } from "@/components/icons/Icon";

/**
 * Contextual help anchor used outside the /help section.
 * Renders a small "?" glyph that deep-links into the Help center.
 *
 * Usage:
 *   <HelpLink anchor="reference/policy-controls#cash-floor" label="Cash floor explained" />
 *   <HelpLink to="/help/guides/promote-to-paper" label="How to promote to paper" />
 */
export function HelpLink({
  anchor,
  to,
  label,
  variant = "icon",
  className = "",
}: {
  /** Path under /help, may include #anchor — e.g. "reference/status-chips#warn". */
  anchor?: string;
  /** Absolute href (overrides `anchor`). */
  to?: string;
  /** Accessible label / tooltip text. */
  label: string;
  variant?: "icon" | "inline";
  className?: string;
}) {
  const href = to ?? (anchor ? `/help/${anchor.replace(/^\//, "")}` : "/help");
  if (variant === "inline") {
    return (
      <Link
        href={href}
        className={`inline-flex items-center gap-1 text-primary hover:underline text-[12px] ${className}`}
        title={label}
        aria-label={label}
      >
        <Icon name="help-circle" size={12} />
        <span>Learn more</span>
      </Link>
    );
  }
  return (
    <Link
      href={href}
      className={`inline-flex items-center justify-center h-5 w-5 rounded-full text-ink-4 hover:text-primary hover:bg-primary-soft transition-colors ${className}`}
      title={label}
      aria-label={label}
    >
      <Icon name="help-circle" size={14} />
    </Link>
  );
}
