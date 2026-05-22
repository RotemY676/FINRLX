"use client";

/**
 * Phase 14.2 — Gmail-style account menu.
 *
 * Replaces the prior minimalist popover. Click the avatar to open a
 * rich card with:
 *   - Large avatar + name + email
 *   - "Manage your FINRLX account" primary CTA
 *   - Account-management section (sign-in-with-another / add-another)
 *     — both are "coming later" stubs because the current AuthContext
 *     is single-user. They render as disabled with explanatory titles
 *     rather than dead buttons (anti-phantom-affordance rule).
 *   - Workspace shortcuts: My profile, Templates, Send feedback
 *   - Personalisation: Theme toggle, Density cycle (so they're
 *     reachable on mobile where they leave the TopBar)
 *   - Sign out
 *   - Footer: Privacy + Terms links + app version
 *
 * Accessibility:
 *   - role="dialog" + aria-labelledby
 *   - Focus restored to the trigger on close
 *   - Esc closes
 *   - Outside-click closes
 *
 * Owned by skills:
 *   - finrlx-ux-redesign-director (rule 4 readable density, rule 8 one
 *     palette / one menu, rule 10 evidence not optional)
 *   - vercel-web-design-guidelines-mirror (aria-haspopup, aria-expanded,
 *     role="dialog", focus trap on close, 44 px touch targets)
 *   - fintech-disclaimer-and-marketing-guard (no execution copy)
 *   - anthropic-frontend-design-mirror (composition: clear hierarchy,
 *     no glass overuse)
 */
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { Icon } from "@/components/icons/Icon";

type Density = "default" | "compact" | "comfortable";
const DENSITIES: ReadonlyArray<Density> = ["default", "compact", "comfortable"];

// Phase 15.4 — shared key with AppShell so the v3-chrome opt-out can
// be flipped from inside the avatar menu. Must match the value in
// AppShell.tsx (`TOPBAR_FLAG_KEY`).
const TOPBAR_FLAG_KEY = "finrlx-topbar-v3";

function computeInitials(email: string): string {
  return (
    email
      .split("@")[0]
      .split(/[._-]/)
      .map((p) => p[0]?.toUpperCase() ?? "")
      .join("")
      .slice(0, 2) || "?"
  );
}

function computeDisplayName(email: string): string {
  const local = email.split("@")[0] ?? "";
  return local
    .split(/[._-]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ") || email;
}

export function UserMenu() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const [density, setDensity] = useState<Density>("default");
  // Phase 15.4 — mirror the AppShell flag so the menu label matches
  // what the chrome is actually rendering.  Default is true (v3 ON).
  const [useV3, setUseV3] = useState(true);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const dialogRef = useRef<HTMLDivElement | null>(null);

  // Hydrate density from localStorage on mount so the menu's label
  // matches whatever the user picked previously via the TopBar control.
  // Also hydrate the v3 opt-out flag for the chrome toggle label.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const saved = window.localStorage.getItem("finrlx-density") as Density | null;
    if (saved && DENSITIES.includes(saved)) setDensity(saved);
    const flag = window.localStorage.getItem(TOPBAR_FLAG_KEY);
    if (flag === "false") setUseV3(false);
  }, []);

  const toggleChrome = useCallback(() => {
    const next = !useV3;
    setUseV3(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(TOPBAR_FLAG_KEY, String(next));
      // AppShell listens to the same key via a `storage` event
      // listener, but `storage` only fires on OTHER tabs. Dispatch a
      // synthetic event so the current tab also reacts without a
      // page reload.
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: TOPBAR_FLAG_KEY,
          newValue: String(next),
        }),
      );
    }
  }, [useV3]);

  const cycleDensity = useCallback(() => {
    const idx = DENSITIES.indexOf(density);
    const next = DENSITIES[(idx + 1) % DENSITIES.length];
    setDensity(next);
    if (typeof document !== "undefined") {
      if (next === "default") document.documentElement.removeAttribute("data-density");
      else document.documentElement.setAttribute("data-density", next);
    }
    if (typeof window !== "undefined") {
      window.localStorage.setItem("finrlx-density", next);
    }
  }, [density]);

  const close = useCallback(() => {
    setOpen(false);
    // Restore focus to the trigger after the dialog closes (Vercel mirror rule).
    window.setTimeout(() => triggerRef.current?.focus(), 0);
  }, []);

  const handleSignOut = useCallback(async () => {
    setOpen(false);
    await logout();
    router.push("/login");
  }, [logout, router]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!dialogRef.current?.contains(e.target as Node) && !triggerRef.current?.contains(e.target as Node)) {
        close();
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        close();
      }
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, close]);

  // Phase 14.6 — when signed out, render a Gmail-style "Sign in" CTA in
  // the TopBar's account slot instead of nothing. This is the only
  // sign-in / sign-up entry point in the shell (sidebar hides auth-
  // required entries for anonymous users).
  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Link
          href="/signup"
          className="hidden sm:inline-flex items-center justify-center min-h-10 px-3 rounded-md text-ink-2 hover:bg-surface-3 text-body-sm font-medium transition-colors"
        >
          Create account
        </Link>
        <Link
          href="/login"
          className="inline-flex items-center justify-center gap-1.5 min-h-10 px-4 rounded-md bg-primary text-primary-ink text-body-sm font-medium hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary transition-opacity"
        >
          <Icon name="user" size={16} />
          Sign in
        </Link>
      </div>
    );
  }

  const initials = computeInitials(user.email);
  const displayName = computeDisplayName(user.email);
  const densityLabel =
    density === "compact" ? "Compact" : density === "comfortable" ? "Comfortable" : "Default";

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-primary-ink text-body-sm font-semibold shrink-0 hover:ring-2 hover:ring-primary-soft focus:ring-2 focus:ring-primary outline-none transition"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={`Account menu — signed in as ${user.email}`}
        title={user.email}
      >
        {initials}
      </button>

      {open && (
        <div
          ref={dialogRef}
          role="dialog"
          aria-labelledby="user-menu-heading"
          // Phase 14.7 fix — `overflow-hidden` clipped the bottom of the
          // menu (sign-out / theme / density / footer) on short viewports
          // because the content can be ~520 px tall. Cap height to viewport
          // minus the TopBar+gutter (5 rem ≈ 80 px) and scroll inside the
          // rounded container.
          className="absolute right-0 top-[calc(100%+8px)] z-50 w-80 max-w-[calc(100vw-1rem)] max-h-[calc(100vh-5rem)] bg-surface border border-line rounded-xl shadow-lg overflow-y-auto"
        >
          {/* Header card — large avatar + name + email */}
          <div className="px-4 pt-5 pb-4 flex flex-col items-center text-center border-b border-line bg-surface-2">
            <div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center text-primary-ink text-section-title font-semibold mb-2">
              {initials}
            </div>
            <h2 id="user-menu-heading" className="text-card-title text-ink truncate max-w-full">
              {displayName}
            </h2>
            <p className="text-body-sm text-ink-3 truncate max-w-full">{user.email}</p>
            <Link
              href="/profile"
              onClick={close}
              className="mt-3 inline-flex items-center justify-center min-h-10 px-4 rounded-full border border-line bg-surface text-ink-2 text-body-sm font-medium hover:bg-surface-3 transition-colors"
            >
              Manage your FINRLX account
            </Link>
          </div>

          {/* Account management — coming-later stubs.
              We do NOT render them as buttons that go nowhere. They're
              clearly labelled as "coming later" so the user understands. */}
          <div className="border-b border-line">
            <MenuRowDisabled
              icon="user"
              primary="Add another account"
              secondary="Coming later — FINRLX is currently single-account per user."
            />
            <MenuRowDisabled
              icon="compare"
              primary="Switch account"
              secondary="Coming later — multi-account session not enabled yet."
            />
          </div>

          {/* Workspace shortcuts */}
          <div className="border-b border-line py-1">
            <MenuRow icon="layers" href="/templates" onClick={close}>
              Templates
            </MenuRow>
            <MenuRow icon="message" href="/feedback" onClick={close}>
              Send feedback
            </MenuRow>
            <MenuRow icon="help-circle" href="/help" onClick={close}>
              Help center
            </MenuRow>
          </div>

          {/* Personalisation — theme + density (mobile-friendly since they
              leave the TopBar on small viewports). */}
          <div className="border-b border-line py-1">
            <MenuButton
              icon={theme === "light" ? "moon" : "sun"}
              onClick={() => {
                toggleTheme();
              }}
            >
              <span className="flex-1">Theme</span>
              <span className="text-meta text-ink-4 font-mono">
                {theme === "light" ? "Light" : "Dark"}
              </span>
            </MenuButton>
            <MenuButton
              icon="overview"
              onClick={() => {
                cycleDensity();
              }}
            >
              <span className="flex-1">Density</span>
              <span className="text-meta text-ink-4 font-mono">{densityLabel}</span>
            </MenuButton>
            {/* Phase 15.4 — chrome version toggle. Operator can flip
                between the Phase 15 two-strip layout and the legacy
                v2 single-strip without a page reload. */}
            <MenuButton
              icon="compare"
              onClick={() => {
                toggleChrome();
              }}
            >
              <span className="flex-1">TopBar layout</span>
              <span className="text-meta text-ink-4 font-mono">
                {useV3 ? "New (v3)" : "Classic"}
              </span>
            </MenuButton>
          </div>

          {/* Sign out */}
          <button
            type="button"
            onClick={handleSignOut}
            className="flex items-center gap-3 w-full text-left px-4 min-h-11 text-breach hover:bg-breach-soft hover:text-breach-soft-ink transition-colors"
          >
            <Icon name="alert-triangle" size={16} />
            <span className="text-body-sm font-medium">Sign out</span>
          </button>

          {/* Footer */}
          <div className="px-4 py-3 bg-surface-2 border-t border-line flex items-center justify-between gap-3 text-meta text-ink-4">
            <div className="flex items-center gap-3">
              <Link href="/privacy" onClick={close} className="hover:text-ink-3">
                Privacy
              </Link>
              <span aria-hidden="true">·</span>
              <Link href="/terms" onClick={close} className="hover:text-ink-3">
                Terms
              </Link>
              <span aria-hidden="true">·</span>
              <Link href="/disclaimer" onClick={close} className="hover:text-ink-3">
                Disclaimer
              </Link>
            </div>
            <span className="font-mono">v0.3.0</span>
          </div>
        </div>
      )}
    </div>
  );
}

function MenuRow({
  icon,
  href,
  onClick,
  children,
}: {
  icon: string;
  href: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className="flex items-center gap-3 px-4 min-h-11 text-ink-2 hover:bg-surface-3 hover:text-ink transition-colors text-body-sm"
    >
      <Icon name={icon} size={16} className="text-ink-3" />
      <span className="flex-1 truncate">{children}</span>
    </Link>
  );
}

function MenuButton({
  icon,
  onClick,
  children,
}: {
  icon: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-3 w-full text-left px-4 min-h-11 text-ink-2 hover:bg-surface-3 hover:text-ink transition-colors text-body-sm"
    >
      <Icon name={icon} size={16} className="text-ink-3" />
      {children}
    </button>
  );
}

function MenuRowDisabled({
  icon,
  primary,
  secondary,
}: {
  icon: string;
  primary: string;
  secondary: string;
}) {
  return (
    <div
      className="flex items-start gap-3 px-4 py-3 text-ink-4 cursor-not-allowed"
      title={secondary}
      aria-disabled="true"
    >
      <Icon name={icon} size={16} className="mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="text-body-sm">{primary}</p>
        <p className="text-meta">{secondary}</p>
      </div>
      <span className="text-meta font-mono uppercase tracking-wider shrink-0 mt-0.5">
        soon
      </span>
    </div>
  );
}
