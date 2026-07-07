"use client";

/**
 * LEAP A5 — the Analyst Desk: one long, dense, streamed research screen.
 * Section registry + sticky mini-map; each section lazy-mounts near the
 * viewport and fetches its own D42 endpoint, so the page assembles
 * progressively and degrades per-section, never as a whole.
 */

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import {
  DeskCard,
  SectionSkeleton,
  SectionDegraded,
  useDeskSection,
  useNearViewport,
} from "@/components/desk/primitives";
import {
  ChartSection,
  FilingsSection,
  FundamentalsSection,
  HeaderSection,
  InsiderSection,
  NewsSocialSection,
  RiskSection,
  RLLabSection,
  SignalMatrixSection,
  TournamentSection,
} from "@/components/desk/sections";

const REGISTRY: {
  id: string;
  title: string;
  subtitle?: string;
  Component: (p: { payload: any }) => React.ReactNode;
}[] = [
  { id: "chart", title: "Price, regimes & events", subtitle: "hover markers for evidence", Component: ChartSection },
  { id: "signals", title: "Signal matrix", subtitle: "each vs its own history", Component: SignalMatrixSection },
  { id: "tournament", title: "Model tournament", subtitle: "walk-forward, penalized", Component: TournamentSection },
  { id: "rl", title: "RL research lab", subtitle: "isolated FinRL ensemble", Component: RLLabSection },
  { id: "news_social", title: "News & social tape", subtitle: "dual scored lanes", Component: NewsSocialSection },
  { id: "fundamentals", title: "Fundamentals", subtitle: "SEC XBRL trends", Component: FundamentalsSection },
  { id: "filings", title: "Filings intelligence", subtitle: "tone & disclosure change", Component: FilingsSection },
  { id: "insider", title: "Insider flow", subtitle: "context gauge", Component: InsiderSection },
  { id: "risk", title: "Risk & regimes", Component: RiskSection },
];

function StreamedSection({
  ticker,
  id,
  title,
  subtitle,
  Component,
}: {
  ticker: string;
  id: string;
  title: string;
  subtitle?: string;
  Component: (p: { payload: any }) => React.ReactNode;
}) {
  const [ref, near] = useNearViewport<HTMLDivElement>();
  const state = useDeskSection<any>(ticker, id, near);
  return (
    <div ref={ref}>
      <DeskCard id={id} title={title} subtitle={subtitle}>
        {state.kind === "ready" ? (
          <Component payload={state.payload} />
        ) : state.kind === "error" ? (
          <SectionDegraded reason={state.detail} />
        ) : (
          <SectionSkeleton lines={4} />
        )}
      </DeskCard>
    </div>
  );
}

export default function DeskPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = decodeURIComponent(params.ticker ?? "").toUpperCase();
  const header = useDeskSection<any>(ticker, "header", true);
  const [active, setActive] = useState<string>("chart");

  return (
    <div className="mx-auto flex max-w-6xl gap-6 px-4 py-6" data-testid="analyst-desk">
      <nav aria-label="Desk sections"
        className="sticky top-6 hidden h-fit w-44 shrink-0 flex-col gap-1 lg:flex">
        {REGISTRY.map((s) => (
          <a key={s.id} href={`#${s.id}`} onClick={() => setActive(s.id)}
            className={`rounded px-2 py-1 text-xs ${active === s.id ? "bg-surface-2 text-ink" : "text-ink-4 hover:text-ink-2"}`}>
            {s.title}
          </a>
        ))}
        <Link href={`/compare?tickers=${ticker}`}
          className="mt-3 rounded px-2 py-1 text-xs text-primary hover:underline">
          Compare with…
        </Link>
      </nav>

      <main className="min-w-0 flex-1 space-y-5">
        <DeskCard id="header" title="Analyst Desk" subtitle="evidence-first research">
          {header.kind === "ready" ? (
            <HeaderSection payload={header.payload} />
          ) : header.kind === "error" ? (
            <SectionDegraded reason={header.detail} />
          ) : (
            <SectionSkeleton lines={2} />
          )}
        </DeskCard>

        {REGISTRY.map((s) => (
          <StreamedSection key={s.id} ticker={ticker} {...s} />
        ))}

        <footer className="rounded-lg border border-line bg-surface-2 p-3 text-xs text-ink-4"
          data-testid="desk-disclaimer">
          Research information from the FINRLX engine ensemble — not investment
          advice. Every section names its sources; degraded sections state what
          is missing rather than estimating it.
        </footer>
      </main>
    </div>
  );
}
