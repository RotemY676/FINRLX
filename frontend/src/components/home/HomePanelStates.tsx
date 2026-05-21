import { Icon } from "@/components/icons/Icon";

import type { ReactNode } from "react";

/**
 * Panel-level partial-failure rendering. When a single source fails, the rest
 * of the home page must still be useful — these helpers ensure each card
 * narrates its own unavailable state instead of crashing the whole tree.
 */

interface PanelShellProps {
  title: string;
  subtitle?: string;
  right?: ReactNode;
  icon?: string;
  children: ReactNode;
  className?: string;
}

export function PanelShell({
  title,
  subtitle,
  right,
  icon,
  children,
  className = "",
}: PanelShellProps) {
  return (
    <section
      className={`rounded-lg border border-line bg-surface shadow-sm ${className}`}
    >
      <header className="flex items-center gap-2 px-4 py-3 border-b border-line">
        {icon && <Icon name={icon} size={14} className="text-primary" />}
        <div className="min-w-0">
          <h2 className="text-[13px] font-semibold text-ink truncate">{title}</h2>
          {subtitle && <p className="text-[11px] text-ink-3 truncate">{subtitle}</p>}
        </div>
        {right && <div className="ml-auto flex items-center gap-2">{right}</div>}
      </header>
      <div className="p-4">{children}</div>
    </section>
  );
}

export function PanelUnavailable({
  message,
  hint,
}: {
  message: string;
  hint?: string;
}) {
  return (
    <div
      role="status"
      className="rounded-md border border-line bg-surface-2 p-3 text-[12.5px] text-ink-3"
    >
      <div className="flex items-start gap-2">
        <Icon name="info" size={14} className="mt-0.5 shrink-0 text-ink-4" />
        <div>
          <p className="text-ink-2 font-medium">{message}</p>
          {hint && <p className="text-[11px] text-ink-4 mt-0.5">{hint}</p>}
        </div>
      </div>
    </div>
  );
}

export function PanelEmpty({
  message,
  hint,
}: {
  message: string;
  hint?: string;
}) {
  return (
    <div className="text-center py-4 text-[12.5px]">
      <p className="text-ink-2">{message}</p>
      {hint && <p className="text-[11px] text-ink-4 mt-1">{hint}</p>}
    </div>
  );
}
