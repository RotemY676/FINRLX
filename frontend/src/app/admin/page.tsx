"use client";

import { Icon } from "@/components/icons/Icon";
import { StatusBadge } from "@/components/recommendation/StatusBadge";

function SectionCard({ title, icon, children }: {
  title: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
      <div className="flex items-center gap-2 mb-4">
        <Icon name={icon} size={16} className="text-ink-3" />
        <h3 className="text-[13px] font-semibold text-ink">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function PendingPlaceholder({ description }: { description: string }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-md bg-surface-2 border border-line/50">
      <Icon name="clock" size={14} className="text-ink-4 shrink-0" />
      <div>
        <p className="text-[12.5px] text-ink-3">{description}</p>
        <p className="text-[11px] text-ink-4 mt-0.5">Pending backend integration</p>
      </div>
    </div>
  );
}

export default function AdminPage() {
  return (
    <div className="space-y-gap max-w-[1200px]">
      {/* Header */}
      <div>
        <h1 className="text-[20px] font-semibold text-ink">Ops Command Center</h1>
        <p className="text-[11px] text-ink-4 mt-1">
          System health, publication queue, governance, and audit trail
        </p>
      </div>

      {/* Top row: Publication Queue + Data Feeds */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
        <SectionCard title="Publication Queue" icon="send">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Queued recommendations</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Awaiting approval</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Published today</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="border-t border-line/50 pt-3">
              <PendingPlaceholder description="Publish / reject actions and queue management" />
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Data Feeds" icon="database">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Market data feed</span>
              <StatusBadge status="stale" />
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Fundamental data feed</span>
              <StatusBadge status="stale" />
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Last ingestion</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="border-t border-line/50 pt-3">
              <PendingPlaceholder description="Feed status, staleness alerts, and manual refresh triggers" />
            </div>
          </div>
        </SectionCard>
      </div>

      {/* Middle row: Engine Health + Breach Watch */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
        <SectionCard title="Engine Health" icon="activity">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Pipeline status</span>
              <StatusBadge status="stale" />
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Last run</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Avg latency</span>
              <span className="text-ink-4 font-mono">-- ms</span>
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Error rate (24h)</span>
              <span className="text-ink-4 font-mono">--%</span>
            </div>
            <div className="border-t border-line/50 pt-3">
              <PendingPlaceholder description="Real-time engine metrics and restart controls" />
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Breach Watch" icon="alert-triangle">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Active breaches</span>
              <span className="text-breach font-mono font-medium">--</span>
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Caution-level warnings</span>
              <span className="text-caution font-mono font-medium">--</span>
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Last breach</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="border-t border-line/50 pt-3">
              <PendingPlaceholder description="Constraint violation details and override controls" />
            </div>
          </div>
        </SectionCard>
      </div>

      {/* Bottom row: Incidents + Audit Trail */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
        <SectionCard title="Incidents" icon="alert-circle">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Open incidents</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Resolved (7d)</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">MTTR</span>
              <span className="text-ink-4 font-mono">-- min</span>
            </div>
            <div className="border-t border-line/50 pt-3">
              <PendingPlaceholder description="Incident log, severity classification, and response tracking" />
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Audit Trail" icon="file-text">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Events today</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Last action</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="flex items-center justify-between text-[12.5px]">
              <span className="text-ink-3">Export status</span>
              <span className="text-ink-4 font-mono">--</span>
            </div>
            <div className="border-t border-line/50 pt-3">
              <PendingPlaceholder description="Searchable audit log with filtering and CSV export" />
            </div>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
