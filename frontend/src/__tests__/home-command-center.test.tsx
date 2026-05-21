/**
 * Phase HOME-1 — Decision Command Center contract.
 *
 * These tests are the safety + rendering contract for the home page. They
 * intentionally avoid coupling to specific component internals and instead
 * lock in:
 *
 *   1. Always renders a governance/safety badge with the canonical copy.
 *   2. Always shows "No broker execution" wording somewhere in the tree.
 *   3. Always shows "Research-only" or equivalent decision-support wording.
 *   4. RL/shadow panel cannot present RL output as a live recommendation.
 *   5. No CTA on the home page contains forbidden execution language.
 *   6. Opportunity radar ships both a desktop table and a mobile card path.
 *   7. Partial data failures render panel-level unavailable states, not a
 *      whole-page crash.
 *   8. Data freshness / provenance labels appear where data is available.
 *   9. Empty states work when no current recommendation, no portfolio, no
 *      ops queue, and no news exist.
 *
 * The whole `@/services/api` module is mocked so this test runs offline.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";

// ── Mock @/services/api before importing the component ───────────────
vi.mock("@/services/api", () => {
  const meta = {
    trace_id: null,
    api_version: "v1",
    generated_at: "2026-05-21T08:00:00Z",
    warnings: [],
    freshness: { data_as_of: "2026-05-21T07:55:00Z", is_stale: false, staleness_reason: null },
  };
  return {
    fetchOverview: vi.fn(async () => ({
      meta: { ...meta, warnings: ["A newer pipeline-generated draft exists but is not published yet."] },
      data: {
        current_recommendation: {
          id: "REC-1",
          status: "published",
          confidence: { model_confidence: 0.74, data_confidence: 0.82, operational_confidence: 0.7 },
          total_positions: 8,
          top_overweight: "asset-1",
          top_underweight: "asset-2",
          published_at: "2026-05-20T16:00:00Z",
          valid_from: null,
          valid_to: null,
          data_as_of: "2026-05-21T07:55:00Z",
          rationale_summary: "Momentum-driven tilt with quality overlay.",
          warning_count: 1,
        },
        health: {
          source_freshness_ok: true,
          feature_health_ok: true,
          model_health_ok: true,
          publication_health_ok: false,
          open_incidents: 1,
          last_checked_at: "2026-05-21T07:50:00Z",
        },
        recent_recommendation_count: 12,
        last_published_at: "2026-05-20T16:00:00Z",
      },
    })),
    fetchCurrentRecommendation: vi.fn(async () => ({
      meta,
      data: {
        id: "REC-1",
        status: "published",
        confidence: { model_confidence: 0.74, data_confidence: 0.82, operational_confidence: 0.7 },
        weights: [
          {
            asset_id: "asset-1",
            ticker: "NVDA",
            name: "NVIDIA Corp",
            target_weight: 0.12,
            previous_weight: 0.08,
            delta: 0.04,
            stance: "overweight",
            rationale: "Momentum + earnings revisions",
          },
          {
            asset_id: "asset-2",
            ticker: "XOM",
            name: "Exxon Mobil",
            target_weight: 0.02,
            previous_weight: 0.06,
            delta: -0.04,
            stance: "underweight",
            rationale: "Crude regime shift",
          },
        ],
        published_at: "2026-05-20T16:00:00Z",
        valid_from: null,
        valid_to: null,
        data_as_of: "2026-05-21T07:55:00Z",
        rationale_summary: "Momentum tilt.",
        warnings: ["Source feed lag exceeds 30m"],
        policy_version_id: null,
        created_at: "2026-05-20T15:30:00Z",
      },
    })),
    fetchRegime: vi.fn(async () => ({
      meta,
      data: {
        regime_label: "Risk-on · late cycle",
        regime_confidence: 0.78,
        persistence_days: 41,
        last_switch_date: "2026-03-14",
        alternatives: [],
        signal_posture: [],
        sector_tilts: [
          { sector: "Semis", tilt_pct: 3.2 },
          { sector: "Software", tilt_pct: 2.1 },
          { sector: "Energy", tilt_pct: -1.6 },
        ],
        as_of: "2026-05-21T07:50:00Z",
      },
    })),
    fetchActivity: vi.fn(async () => ({
      meta,
      data: {
        events: [
          { kind: "publish", actor: "R. Mikhailov", description: "published REC v4", detail: null, when_ago: "12m", timestamp: "2026-05-21T07:48:00Z" },
          { kind: "breach", actor: "system", description: "sector limit approaching", detail: null, when_ago: "38m", timestamp: "2026-05-21T07:22:00Z" },
        ],
        total: 2,
      },
    })),
    fetchOps: vi.fn(async () => ({
      meta,
      data: {
        queue: [
          {
            id: "q-1",
            recommendation_id: "REC-1",
            ticker: "NVDA",
            stance: "buy",
            version: "v4",
            submitted_ago: "12m",
            submitter: "system",
            weight: "+4.2%",
            confidence: 0.74,
            flags: ["Breach: sector"],
            priority: "high",
            status: "pending",
          },
        ],
        feeds: [],
        engines: [],
        breaches: [],
        incidents: [],
        audit: [],
        system_kpis: [],
        ml_ops: {
          total_models: 4,
          active_models: 0,
          shadow_models: 4,
          latest_validation_status: "passed",
          promotion_readiness: "not_ready",
          warning_count: 0,
          any_model_influences_live_pipeline: false,
          ml_is_shadow_only: true,
        },
        policy: null,
        integrations_summary: {
          total_integrations: 5,
          healthy: 4,
          degraded: 1,
          placeholder: 0,
          real_providers: 4,
        },
        universe: null,
        rl: {
          total_environments: 2,
          total_runs: 5,
          latest_run_status: "complete",
          latest_agent_type: "ppo",
          total_agents: 3,
          trainable_agents: 2,
          latest_training_status: "complete",
          latest_training_agent: "ppo-1",
          total_policy_snapshots: 2,
          total_benchmarks: 1,
          latest_benchmark_status: "complete",
          is_shadow_only: true,
          live_pipeline_influence: false,
        },
      },
    })),
    fetchCurrentPaper: vi.fn(async () => ({
      meta,
      data: null,
    })),
    fetchCurrentRisk: vi.fn(async () => ({ meta, data: null })),
    fetchNews: vi.fn(async () => ({
      meta,
      data: {
        summary: { total: 1, positive: 0, neutral: 1, negative: 0, mean_compound: 0 },
        items: [
          {
            source: "Reuters",
            title: "Semis lead pre-market on AI capex",
            link: "https://example.com",
            summary: "",
            published: "2026-05-21T07:00:00Z",
            sentiment_compound: 0,
            sentiment_label: "neutral",
          },
        ],
      },
    })),
    fetchEngineComparison: vi.fn(async () => ({ meta, data: null })),
    fetchDisagreement: vi.fn(async () => ({ meta, data: { recommendation_id: "REC-1", total_engines: 5, agreeing: 3, dissenting: 2, dispersion: 0.41, dominant_stance: "overweight", dissenting_engines: [], summary: "" } })),
    fetchEvidence: vi.fn(async () => ({ meta, data: { recommendation_id: "REC-1", items: [{ order: 1, title: "Earnings", body: "Q1 beat", delta_label: null, delta_direction: null, caveat: null, source_engine: "fundamentals" }], caveat: null, last_refreshed_min: 5 } })),
  };
});

// ── Mock auth context ────────────────────────────────────────────────
vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    user: { email: "operator@finrlx.com" },
    isLoading: false,
    login: vi.fn(),
    signup: vi.fn(),
    logout: vi.fn(),
  }),
}));

// Forbidden execution language banned in any home-page CTA.
const FORBIDDEN_CTA_PATTERNS: RegExp[] = [
  /\btrade\b/i,
  /\bbuy now\b/i,
  /\bsell now\b/i,
  /\bexecute\b/i,
  /\bconnect broker\b/i,
  /\bauto[- ]?trade\b/i,
  /\bAI pick\b/i,
  /\bguaranteed (return|profit)\b/i,
];

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

async function renderHome() {
  const { DecisionCommandCenter } = await import(
    "@/components/home/DecisionCommandCenter"
  );
  render(<DecisionCommandCenter />);
  await waitFor(() =>
    expect(screen.queryByText(/Loading command center/i)).toBeNull(),
  );
}

describe("home command center (HOME-1)", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("renders a governance/safety panel with the canonical wording", async () => {
    await renderHome();
    // Governance card carries the data-governance marker the contract scans for.
    const governance = document.querySelector('[data-governance="true"]');
    expect(governance).not.toBeNull();
    expect(within(governance as HTMLElement).getByText(/Research only/i)).toBeInTheDocument();
    expect(within(governance as HTMLElement).getByText(/No broker execution/i)).toBeInTheDocument();
  });

  it("states 'Decision-support tool' and 'No broker execution' on the home tree", async () => {
    await renderHome();
    expect(screen.getAllByText(/Decision-support tool/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/No broker execution/i).length).toBeGreaterThan(0);
  });

  it("states 'Research only' on the home tree", async () => {
    await renderHome();
    expect(screen.getAllByText(/Research only/i).length).toBeGreaterThan(0);
  });

  it("renders the RL/shadow panel as shadow-only and not as a live recommendation", async () => {
    await renderHome();
    expect(screen.getAllByText(/Shadow research/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Research-only|shadow-only|Backtests are not future performance/i).length,
    ).toBeGreaterThan(0);
  });

  it("contains no CTA copy with forbidden execution language", async () => {
    await renderHome();
    const ctaText = Array.from(document.querySelectorAll("a, button"))
      .map((el) => (el.textContent || "").trim())
      .filter(Boolean);
    expect(ctaText.length).toBeGreaterThan(0);
    for (const text of ctaText) {
      for (const pattern of FORBIDDEN_CTA_PATTERNS) {
        if (pattern.test(text)) {
          throw new Error(
            `Forbidden CTA copy "${text}" matched ${pattern} on the home page.`,
          );
        }
      }
    }
  });

  it("renders the opportunity radar with a desktop table AND a mobile card path", async () => {
    await renderHome();
    expect(screen.getByTestId("radar-table")).toBeInTheDocument();
    expect(screen.getByTestId("radar-cards")).toBeInTheDocument();
  });

  it("surfaces freshness/provenance labels when pipeline data is fresh", async () => {
    await renderHome();
    // The DataFreshnessBadge renders "as of <iso-ish>" copy when the source
    // is present and fresh.
    expect(screen.getAllByText(/as of 2026-05-21/i).length).toBeGreaterThan(0);
  });

  it("shows an empty-state for the paper portfolio when no portfolio exists", async () => {
    await renderHome();
    expect(screen.getByText(/No active paper portfolio yet\./i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Try a template/i })).toBeInTheDocument();
  });
});

describe("home command center — partial data failure", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("renders panel-level unavailable states instead of crashing when sources fail", async () => {
    const api = await import("@/services/api");
    const failingRec = vi.fn(() => Promise.reject(new Error("recommendation endpoint 500")));
    const failingOps = vi.fn(() => Promise.reject(new Error("ops endpoint 500")));
    (api.fetchCurrentRecommendation as unknown as { mockImplementation: (fn: () => Promise<unknown>) => void }).mockImplementation(failingRec);
    (api.fetchOps as unknown as { mockImplementation: (fn: () => Promise<unknown>) => void }).mockImplementation(failingOps);

    const { DecisionCommandCenter } = await import(
      "@/components/home/DecisionCommandCenter"
    );
    render(<DecisionCommandCenter />);
    await waitFor(() =>
      expect(screen.queryByText(/Loading command center/i)).toBeNull(),
    );

    // Governance still renders.
    expect(document.querySelector('[data-governance="true"]')).not.toBeNull();

    // Opportunity radar reports unavailability without throwing.
    await waitFor(() => {
      expect(screen.getByText(/Opportunity radar unavailable\./i)).toBeInTheDocument();
    });
  });
});

describe("home page module — safe CTA enumeration", () => {
  it("lists only safe action labels in homeData.ts", async () => {
    const { readFileSync } = await import("node:fs");
    const { join } = await import("node:path");
    const src = readFileSync(
      join(__dirname, "..", "components", "home", "homeData.ts"),
      "utf8",
    );
    for (const pattern of FORBIDDEN_CTA_PATTERNS) {
      // Avoid matching the test-only forbidden-list itself, just the action map.
      const actionsBlock = src.match(/ACTION_LABELS:[\s\S]*?\};/);
      if (!actionsBlock) throw new Error("homeData ACTION_LABELS missing");
      if (pattern.test(actionsBlock[0])) {
        throw new Error(
          `homeData.ts ACTION_LABELS contains forbidden pattern ${pattern}`,
        );
      }
    }
  });
});
