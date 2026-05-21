"use client";

/**
 * UI-1 — avatar dropdown menu (industry-standard pattern).
 *
 * Replaces the previous static UserChip + adjacent "Sign out" button.
 * Click the avatar to open a popover: signed-in email + Profile +
 * Templates + Send feedback + Sign out. Closes on outside click, Esc,
 * or selecting an item.
 */
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { useAuth } from "@/contexts/AuthContext";

interface MenuItem {
  label: string;
  href?: string;
  onClick?: () => void | Promise<void>;
  danger?: boolean;
}

export function UserMenu() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  const handleSignOut = useCallback(async () => {
    setOpen(false);
    await logout();
    router.push("/login");
  }, [logout, router]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!user) return null;

  const initials =
    user.email
      .split("@")[0]
      .split(/[._-]/)
      .map((p) => p[0]?.toUpperCase() ?? "")
      .join("")
      .slice(0, 2) || "?";

  const items: MenuItem[] = [
    { label: "My profile", href: "/profile" },
    { label: "Templates", href: "/templates" },
    { label: "Send feedback", href: "/feedback" },
    { label: "Sign out", onClick: handleSignOut, danger: true },
  ];

  return (
    <div className="relative" ref={wrapRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-9 h-9 md:w-8 md:h-8 rounded-full bg-primary flex items-center justify-center text-primary-ink text-[12px] font-semibold shrink-0 hover:ring-2 hover:ring-primary-soft transition"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Account menu — signed in as ${user.email}`}
        title={user.email}
      >
        {initials}
      </button>
      {open ? (
        <div
          role="menu"
          className="absolute right-0 top-[calc(100%+6px)] z-40 min-w-[220px] bg-surface border border-line rounded-lg shadow-lg py-1.5 text-[13px]"
        >
          <div className="px-3 py-2 text-[11px] text-ink-4">
            Signed in as
            <div className="text-ink truncate">{user.email}</div>
          </div>
          <div className="h-px bg-line mx-2 my-1" />
          {items.slice(0, 3).map((it) => (
            <Link
              key={it.label}
              role="menuitem"
              href={it.href ?? "#"}
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-ink-2 hover:bg-surface-3 hover:text-ink transition-colors min-h-[40px] leading-[24px]"
            >
              {it.label}
            </Link>
          ))}
          <div className="h-px bg-line mx-2 my-1" />
          <button
            type="button"
            role="menuitem"
            onClick={handleSignOut}
            className="block w-full text-left px-3 py-2 text-breach hover:bg-breach-soft hover:text-breach-soft-ink transition-colors min-h-[40px] leading-[24px]"
          >
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  );
}
