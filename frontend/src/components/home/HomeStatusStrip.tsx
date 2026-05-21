import Link from "next/link";

import { Icon } from "@/components/icons/Icon";

import type {
  GovernanceStatus,
  HomeDecisionItem,
  HomeSourceStatus,
  PortfolioImpactSummary,
  RegimeStatus,
  SystemHealthRow,
} from "./homeTypes";

interface Props {
  regime: RegimeStatus | null;
  queue: HomeDecisionItem[];
  portfolio: PortfolioImpactSummary;
  systemHealth: SystemHealthRow[];
  governance: GovernanceStatus;
  sourceStatuses: HomeSourceStatus[];
}

function pct(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `${(v * 100).toFixed(0)}%`;
}

/**
 * Above-the-fold status strip — five compact cards answering "what changed,
 * what needs review, what is safe to act on right now."
 */
export function HomeStatusStrip({
  regime,
  queue,
  portfolio,
  systemHealth,
  governance,
  sourceStatuses,
}: Props) {
  const queueCritical = queue.filter((q) => q.severity === "critical").length;
  const queueWarning = queue.filter((q) => q.severity === "warning").length;
  const queueTotal = queue.length;

  const unavailableSources = sourceStatuses.filter((s) => s.status === "unavailable").length;
  const staleSources = sourceStatuses.filter((s) => s.status === "stale").length;

  const healthIssues = systemHealth.filter((s) => s.state !== "ok").length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      {/* Regime / market context */}
      <Card
        label="Regime"
        icon="trend-up"
        primary={regime?.label ?? "Unavailable"}
        secondary={
          regime
            ? `confidence ${regime.confidence?.toFixed(2) ?? "—"} · ${regime.persistenceDays ?? 0}d`
            : "no regime snapshot"
        }
        tone={regime ? "neutral" : "muted"}
      />

      {/* Decision queue */}
      <Card
        label="Needs review"
        icon="decision"
        primary={String(queueTotal)}
        secondary={
          queueTotal === 0
            ? "nothing pending"
            : `${queueCritical} critical · ${queueWarning} warning`
        }
        tone={queueCritical > 0 ? "breach" : queueWarning > 0 ? "caution" : "neutral"}
        href={queueTotal > 0 ? "#decision-queue" : undefined}
      />

      {/* Portfolio / risk impact */}
      <Card
        label="Paper portfolio"
        icon="paper"
        primary={
          portfolio.hasPortfolio
            ? `${pct(portfolio.invested)} invested`
            : "—"
        }
        secondary={
          portfolio.hasPortfolio
            ? portfolio.riskWarning ?? `${pct(portfolio.cash)} cash`
            : "no active portfolio"
        }
        tone={portfolio.riskWarning ? "caution" : "neutral"}
        href={portfolio.hasPortfolio ? "/paper" : "/templates"}
      />

      {/* Data / system health */}
      <Card
        label="Data health"
        icon="database"
        primary={healthIssues === 0 && unavailableSources === 0 ? "OK" : "Attention"}
        secondary={
          healthIssues === 0 && unavailableSources === 0
            ? "all sources reporting"
            : `${unavailableSources} unavailable · ${staleSources} stale`
        }
        tone={
          healthIssues > 0 || unavailableSources > 0 || staleSources > 0
            ? "caution"
            : "pos"
        }
      />

      {/* Governance */}
      <Card
        label="Governance"
        icon="check"
        primary={governance.livePipelineInfluence ? "Review" : "Research-only"}
        secondary={
          governance.livePipelineInfluence
            ? "live pipeline influence flag"
            : "no broker · shadow research only"
        }
        tone={governance.livePipelineInfluence ? "breach" : "pos"}
      />
    </div>
  );
}

type Tone = "neutral" | "pos" | "caution" | "breach" | "muted";

interface CardProps {
  label: string;
  icon: string;
  primary: string;
  secondary?: string;
  tone?: Tone;
  href?: string;
}

const TONE_CLASSES: Record<Tone, { value: string; bar: string }> = {
  neutral: { value: "text-ink", bar: "bg-ink-4" },
  pos: { value: "text-pos", bar: "bg-pos" },
  caution: { value: "text-caution", bar: "bg-caution" },
  breach: { value: "text-breach", bar: "bg-breach" },
  muted: { value: "text-ink-3", bar: "bg-ink-4" },
};

function Card({ label, icon, primary, secondary, tone = "neutral", href }: CardProps) {
  const tc = TONE_CLASSES[tone];
  const baseClass = `rounded-md border border-line bg-surface p-3 flex flex-col gap-1 ${
    href ? "hover:border-primary transition-colors" : ""
  }`;
  const body = (
    <>
      <div className="flex items-center gap-1.5 text-[11px] text-ink-3">
        <Icon name={icon} size={12} className={tc.bar.replace("bg-", "text-")} />
        <span className="font-semibold uppercase tracking-wide">{label}</span>
      </div>
      <div className={`text-[18px] font-display font-semibold leading-tight ${tc.value}`}>
        {primary}
      </div>
      {secondary && (
        <div className="text-[11px] text-ink-3 leading-snug">{secondary}</div>
      )}
    </>
  );
  if (href) {
    return (
      <Link href={href} className={baseClass}>
        {body}
      </Link>
    );
  }
  return <div className={baseClass}>{body}</div>;
}
