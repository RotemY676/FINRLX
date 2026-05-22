"use client";

import { useEffect, useState } from "react";

import { PageError } from "@/components/feedback/PageError";
import { PageLoading } from "@/components/feedback/PageLoading";
import { useAuth } from "@/contexts/AuthContext";

import { DataFreshnessBadge } from "./DataFreshnessBadge";
import { DecisionQueuePanel } from "./DecisionQueuePanel";
import { GovernanceStatusCard } from "./GovernanceStatusCard";
import { HomeStatusStrip } from "./HomeStatusStrip";
import { OpportunityRadarTable } from "./OpportunityRadarTable";
import { PortfolioImpactCard } from "./PortfolioImpactCard";
import { ResearchAssistantPreview } from "./ResearchAssistantPreview";
import { ResearchEventsFeed } from "./ResearchEventsFeed";
import { SectorHeatmapPreview } from "./SectorHeatmapPreview";
import { ShadowResearchSnapshot } from "./ShadowResearchSnapshot";
import { SystemHealthMiniPanel } from "./SystemHealthMiniPanel";
import { loadHomeData } from "./homeData";
import { HelpLink } from "@/components/help/HelpLink";

import type { HomeViewModel } from "./homeTypes";

interface State {
  status: "loading" | "ready" | "error";
  view: HomeViewModel | null;
  failures: Record<string, string>;
  errorMessage: string | null;
}

const INITIAL: State = {
  status: "loading",
  view: null,
  failures: {},
  errorMessage: null,
};

/**
 * FINRLX Home / Decision Command Center.
 *
 * Above-the-fold answers: what changed, what needs review, what evidence
 * supports it, and what is stale/shadow-only/blocked. Mobile order keeps
 * decision queue and radar above lower-priority panels. Each panel handles
 * its own unavailable state via Promise.allSettled aggregation in homeData.
 */
export function DecisionCommandCenter() {
  const { user } = useAuth();
  const [state, setState] = useState<State>(INITIAL);

  useEffect(() => {
    let cancelled = false;
    loadHomeData({ userEmail: user?.email ?? null })
      .then(({ view, failures }) => {
        if (cancelled) return;
        setState({
          status: "ready",
          view,
          failures,
          errorMessage: null,
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setState({
          status: "error",
          view: null,
          failures: {},
          errorMessage: err instanceof Error ? err.message : String(err),
        });
      });
    return () => {
      cancelled = true;
    };
  }, [user?.email]);

  if (state.status === "loading") {
    return <PageLoading label="Loading command center…" />;
  }

  if (state.status === "error" || !state.view) {
    return (
      <PageError
        title="Home unavailable"
        message={state.errorMessage ?? "Could not load the command center."}
        hint="Ensure the backend is reachable. Other workspaces may still be available."
      />
    );
  }

  const view = state.view;

  return (
    <div className="space-y-gap max-w-[1280px]" data-page="home-command-center">
      {/* Header — answers the four playbook questions in one read.
          Typography uses the Phase 3 named tokens (page-title / body-sm)
          instead of hand-rolled pixel sizes. */}
      <header className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-page-title text-ink flex items-center gap-2">
            Decision Command Center
            <HelpLink anchor="getting-started/reading-the-dashboard" label="Read the dashboard — tutorial" />
          </h1>
          <p className="text-body-sm text-ink-2 mt-1 max-w-xl leading-snug">
            Hi, {view.greetingName}. Below: what changed, what needs review,
            what evidence supports it, and what is stale, shadow-only, or
            blocked.
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {view.sourceStatuses.slice(0, 3).map((s) => (
            <DataFreshnessBadge
              key={s.source}
              label={s.label}
              asOf={s.asOf}
              state={s.status}
              warning={s.warning}
            />
          ))}
        </div>
      </header>

      {/* Pipeline warnings */}
      {view.pipelineWarnings.length > 0 && (
        <div
          role="status"
          className="rounded-lg border border-caution bg-caution-soft p-3 text-caption text-caution-soft-ink space-y-1"
        >
          {view.pipelineWarnings.map((w, i) => (
            <p key={i}>· {w}</p>
          ))}
        </div>
      )}

      {/* Status strip */}
      <HomeStatusStrip
        regime={view.regime}
        queue={view.decisionQueue}
        portfolio={view.portfolio}
        systemHealth={view.systemHealth}
        governance={view.governance}
        sourceStatuses={view.sourceStatuses}
      />

      {/* Main grid:
            - Mobile: stacked in this order — queue, radar, portfolio,
              assistant, governance, events, sector, shadow, health.
            - Desktop: 3-column grid with queue left, radar centre,
              assistant/governance/portfolio right.
       */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-gap">
        {/* Decision queue + portfolio left column on desktop */}
        <div className="lg:col-span-4 order-1 space-y-gap">
          <DecisionQueuePanel
            items={view.decisionQueue}
            isUnavailable={
              Boolean(state.failures.ops) && view.decisionQueue.length === 0
            }
            unavailableMessage={state.failures.ops}
          />
          <PortfolioImpactCard portfolio={view.portfolio} />
        </div>

        {/* Centre column: opportunity radar and research events */}
        <div className="lg:col-span-5 order-2 space-y-gap">
          <OpportunityRadarTable
            rows={view.opportunities}
            isUnavailable={Boolean(
              state.failures.recommendation && view.opportunities.length === 0,
            )}
            unavailableMessage={state.failures.recommendation}
            sourceLabel="Top-conviction picks · current recommendation"
          />
          <ResearchEventsFeed items={view.researchEvents} />
        </div>

        {/* Right column on desktop: assistant + governance + sector */}
        <div className="lg:col-span-3 order-3 space-y-gap">
          <ResearchAssistantPreview />
          <GovernanceStatusCard governance={view.governance} />
          <SectorHeatmapPreview rows={view.sectorTilts} />
        </div>
      </div>

      {/* Below-the-fold: shadow research + system health */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-gap">
        <ShadowResearchSnapshot summary={view.shadowResearch} />
        <SystemHealthMiniPanel rows={view.systemHealth} />
      </div>
    </div>
  );
}
