"use client";

/**
 * LEAP A5 — Analyst Desk primitives: the streaming section hook (D42) and
 * shared shells. Every section fetches independently, mounts lazily
 * (IntersectionObserver), renders a skeleton, and degrades honestly with the
 * backend's named reason. Motion rules (D49): one entrance animation per
 * section via DeskCard; zero looped animation.
 */

import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

export type SectionState<T> =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; payload: T; generatedAt: string }
  | { kind: "error"; detail: string };

export function useDeskSection<T>(
  ticker: string,
  section: string,
  active: boolean,
  revision = 0,
) {
  const [state, setState] = useState<SectionState<T>>({ kind: "idle" });
  // LEAP A6: one effect keyed on revision — a freshness bump refetches; the
  // cleanup only cancels when inputs truly change (never mid-flight on our
  // own state transitions).
  useEffect(() => {
    if (!active) return;
    let cancelled = false;
    setState({ kind: "loading" });
    void (async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/v1/autopilot/desk/${encodeURIComponent(ticker)}/${section}`,
        );
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          if (!cancelled)
            setState({ kind: "error", detail: String(body.detail ?? res.status) });
          return;
        }
        const body = (await res.json()) as {
          data: { payload: T; generated_at: string };
        };
        if (!cancelled)
          setState({
            kind: "ready",
            payload: body.data.payload,
            generatedAt: body.data.generated_at,
          });
      } catch {
        if (!cancelled) setState({ kind: "error", detail: "unreachable" });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ticker, section, active, revision]);
  return state;
}

/**
 * LEAP A6 — freshness watcher: polls the lightweight header section every
 * 5 minutes (visible tab only). When generated_at moves, the returned
 * revision increments and streamed sections revalidate. One-shot polls on an
 * interval — not an animation loop (D49 governs motion, not data freshness).
 */
export function useDeskFreshness(ticker: string, intervalMs = 300_000) {
  const [revision, setRevision] = useState(0);
  const lastRef = useRef<string | null>(null);
  useEffect(() => {
    let stop = false;
    const probe = async () => {
      if (stop || document.visibilityState !== "visible") return;
      try {
        const res = await fetch(
          `${API_BASE}/api/v1/autopilot/desk/${encodeURIComponent(ticker)}/header`,
        );
        if (!res.ok) return;
        const body = await res.json();
        const stamp = String(body?.data?.generated_at ?? "");
        if (lastRef.current && stamp && stamp !== lastRef.current) {
          setRevision((r) => r + 1);
        }
        if (stamp) lastRef.current = stamp;
      } catch {
        /* freshness probing never surfaces errors */
      }
    };
    const id = window.setInterval(() => void probe(), intervalMs);
    return () => {
      stop = true;
      window.clearInterval(id);
    };
  }, [ticker, intervalMs]);
  return revision;
}

/** Lazy-mount wrapper: children render only once scrolled near the viewport. */
export function useNearViewport<T extends HTMLElement>(): [React.RefObject<T>, boolean] {
  const ref = useRef<T>(null) as React.RefObject<T>;
  const [near, setNear] = useState(false);
  useEffect(() => {
    if (near || !ref.current) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) setNear(true);
      },
      { rootMargin: "600px 0px" },
    );
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, [near]);
  return [ref, near];
}

export function DeskCard({
  id,
  title,
  subtitle,
  children,
}: {
  id: string;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <motion.section
      id={id}
      data-desk-section={id}
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="rounded-xl border border-line bg-surface p-5 shadow-sm"
    >
      <header className="mb-3 flex items-baseline gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-2">{title}</h2>
        {subtitle && <span className="text-xs text-ink-4">{subtitle}</span>}
      </header>
      {children}
    </motion.section>
  );
}

export function SectionSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div aria-busy="true" className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-4 animate-pulse rounded bg-surface-2" />
      ))}
    </div>
  );
}

export function SectionDegraded({ reason, note }: { reason?: string; note?: string }) {
  return (
    <p className="text-sm text-ink-2">
      {note ?? "This section's source is unavailable"}
      {reason ? <span className="text-ink-4"> ({reason})</span> : null}. The rest of the
    desk is unaffected.
    </p>
  );
}

export function Pill({ tone = "neutral", title, children }: {
  tone?: "pos" | "neutral" | "caution" | "breach";
  title?: string;
  children: React.ReactNode;
}) {
  const cls =
    tone === "pos"
      ? "bg-pos-soft text-pos-soft-ink"
      : tone === "caution"
        ? "bg-caution-soft text-caution-soft-ink"
        : tone === "breach"
          ? "bg-breach-soft text-breach-soft-ink"
          : "bg-surface-2 text-ink-2";
  return (
    <span title={title}
      className={`inline-flex items-center rounded-full border border-line px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {children}
    </span>
  );
}

/** One-shot count-in number (D49: animates once on mount, never loops). */
export function CountIn({ value, decimals = 2 }: { value: number; decimals?: number }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const start = performance.now();
    let raf = 0;
    const tick = (t: number) => {
      const p = Math.min((t - start) / 500, 1);
      setShown(value * (1 - Math.pow(1 - p, 3)));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);
  return <span>{shown.toFixed(decimals)}</span>;
}
