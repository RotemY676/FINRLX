"use client";

/**
 * Desk W1 — DeskV2 assembly (SPEC-03 blueprint zones 1,3,4,9; DEC-6 deep
 * links). W1 scope shipped from this environment: Verdict band + dials +
 * Forensic drawer + v2 Panels A/B; panels C\u2013F reuse the tested A5 sections
 * pending their v2 skins in the browser-equipped phase (honest scope,
 * recorded in RESUME.md). Everything renders only when flags.desk_v2 is ON.
 */
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

import {
  ChartSection,
  FilingsSection,
  FundamentalsSection,
  InsiderSection,
  NewsSocialSection,
} from "@/components/desk/sections";
import { useDeskSection } from "@/components/desk/primitives";
import { tokens } from "@/design/deskTokens";
import { deskCopy } from "@/lib/deskCopy";

import { ErrorCard, ForensicDrawer, MethodBlock, useDeskStatus } from "./core";
import {
  DeskHead,
  SignalMatrixV2,
  TournamentArenaV2,
  VerdictBand,
} from "./panels";

function PanelShell({ id, title, children }: {
  id: string; title: string; children: React.ReactNode;
}) {
  return (
    <section id={`panel-${id}`} data-testid={`panelshell-${id}`}
             style={{ border: tokens.border.hairline,
                      borderRadius: tokens.radius.panel,
                      padding: tokens.space(2) }}>
      <h2 style={{ marginTop: 0, fontSize: tokens.type.scale.md }}>{title}</h2>
      {children}
    </section>
  );
}

export default function DeskV2({ ticker }: { ticker: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const drawerPanel = params.get("drawer");

  const statusFetch = useDeskStatus(ticker);
  const header = useDeskSection<any>(ticker, "header", true);
  const signals = useDeskSection<any>(ticker, "signals", true);
  const tournament = useDeskSection<any>(ticker, "tournament", true);
  const chart = useDeskSection<any>(ticker, "chart", true);
  const newsSocial = useDeskSection<any>(ticker, "news_social", true);
  const fundamentals = useDeskSection<any>(ticker, "fundamentals", true);
  const filings = useDeskSection<any>(ticker, "filings", true);
  const insider = useDeskSection<any>(ticker, "insider", true);

  const reuse = (s: { kind: string; payload?: any; detail?: string },
                 C: (p: { payload: any }) => React.ReactNode) =>
    s.kind === "ready" ? (
      <C payload={s.payload} />
    ) : s.kind === "error" ? (
      <ErrorCard source={s.detail ?? "section"} healthHref="/pro/ops" />
    ) : (
      <p>loading\u2026</p>
    );

  const openDrawer = useCallback(
    (panel: string) => {
      const q = new URLSearchParams(params.toString());
      q.set("drawer", panel);
      router.replace(`?${q.toString()}`, { scroll: false });
    },
    [params, router],
  );
  const closeDrawer = useCallback(() => {
    const q = new URLSearchParams(params.toString());
    q.delete("drawer");
    router.replace(q.size ? `?${q.toString()}` : "?", { scroll: false });
  }, [params, router]);

  const head: DeskHead =
    header.kind === "ready"
      ? {
          ticker,
          price: {
            last: header.payload?.summary?.latest_close,
            as_of: header.payload?.freshness?.latest_bar,
          },
          stance: {
            state: header.payload?.summary?.stance,
            evidence_coverage:
              statusFetch.kind === "ready"
                ? {
                    have: statusFetch.status.sections.filter(
                      (s) => s.state === "live",
                    ).length,
                    of: statusFetch.status.sections.length,
                    gated: statusFetch.status.sections
                      .filter((s) => s.detail_code === "E7_GATED"
                                  || s.detail_code === "E8_GATED")
                      .map((s) => s.id),
                  }
                : undefined,
          },
        }
      : { ticker };

  const methodFor = (panel: string): MethodBlock | null => {
    if (panel === "A" && signals.kind === "ready")
      return signals.payload?.method ?? null;
    if (panel === "B" && tournament.kind === "ready")
      return tournament.payload?.method ?? null;
    return null;
  };

  return (
    <main style={{ display: "grid", gap: tokens.space(3),
                   padding: tokens.space(2) }}>
      <VerdictBand head={head} statusFetch={statusFetch}
                   onStanceClick={() => openDrawer("stance")} />

      <PanelShell id="chart" title="Price \u00B7 regime \u00B7 evidence">
        {reuse(chart, ChartSection)}
      </PanelShell>

      <div style={{ display: "grid", gap: tokens.space(3),
                    gridTemplateColumns: "repeat(auto-fit,minmax(420px,1fr))" }}>
        <PanelShell id="A" title="A \u00B7 Technical signals">
          <button onClick={() => openDrawer("A")}
                  data-testid="how-A" style={{ float: "right" }}>
            How was this computed?
          </button>
          {signals.kind === "ready" ? (
            <SignalMatrixV2
              rows={signals.payload?.signal_matrix ?? []}
              elevation={signals.payload?.elevation}
              source="price provider chain"
            />
          ) : signals.kind === "error" ? (
            <ErrorCard source={signals.detail} healthHref="/pro/ops" />
          ) : (
            <p>loading\u2026</p>
          )}
        </PanelShell>

        <PanelShell id="B" title="B \u00B7 Model tournament arena">
          <button onClick={() => openDrawer("B")}
                  data-testid="how-B" style={{ float: "right" }}>
            How was this computed?
          </button>
          {tournament.kind === "ready" ? (
            <TournamentArenaV2 payload={tournament.payload ?? {}} />
          ) : tournament.kind === "error" ? (
            <ErrorCard source={tournament.detail} healthHref="/pro/ops" />
          ) : (
            <p>loading\u2026</p>
          )}
        </PanelShell>

        <PanelShell id="C" title="C \u00B7 News & social sentiment">
          {reuse(newsSocial, NewsSocialSection)}
        </PanelShell>

        <PanelShell id="E" title="E \u00B7 Fundamentals & filings">
          {reuse(fundamentals, FundamentalsSection)}
          {reuse(filings, FilingsSection)}
          {reuse(insider, InsiderSection)}
        </PanelShell>

        <PanelShell id="F" title="F \u00B7 Sector context">
          <p style={{ color: tokens.color.neutral.n600 }}>
            {deskCopy.sector.benchmarkScope}
          </p>
        </PanelShell>
      </div>

      <footer style={{ fontSize: tokens.type.scale.xs,
                       color: tokens.color.neutral.n600 }}>
        {deskCopy.disclaimers.footer}
      </footer>

      {drawerPanel && (
        <ForensicDrawer
          panel={drawerPanel}
          method={methodFor(drawerPanel)}
          fingerprint={statusFetch.kind === "ready"
            ? statusFetch.status.fingerprint : undefined}
          computedAt={statusFetch.kind === "ready"
            ? statusFetch.status.computed_at : undefined}
          onClose={closeDrawer}
        />
      )}
    </main>
  );
}
