/**
 * Desk W1 — the copy deck (SPEC-03 §4). Every user-facing Desk v2 string
 * lives here so the wording scan has one surface. Research vocabulary only;
 * advice verbs are banned (tested). Reasons from API payloads render
 * verbatim — the client never rewrites server honesty.
 */
export const deskCopy = {
  stanceKind: "research stance — not advice",
  evidenceCoverage: (have: number, of: number) => `evidence ${have}/${of}`,
  dialAria: (engine: string, state: string, reason?: string) =>
    `${engine}: ${state}${reason ? `, ${reason}` : ""}`,
  engines: {
    technical: "Technical",
    tournament: "Model",
    news: "News",
    social: "Social",
    fundamentals: "Fund",
    sector: "Sector",
  } as Record<string, string>,

  /**
   * What each lane actually measures. The dial row previously showed a
   * two-letter label and a 30px arc with a `title` tooltip: readable only on
   * hover, unreachable on touch, and it never said what the lane *was*.
   */
  engineWhat: {
    technical: "Price-derived signals: momentum, volatility, drawdown and volume behaviour.",
    tournament: "The walk-forward model tournament — which candidate won and how it was validated.",
    news: "Scored 7-day headline sentiment from the news provider.",
    social: "Retail/social mention volume and tone, kept in its own lane so it never dilutes news.",
    fundamentals: "Filing-derived company figures (SEC XBRL).",
    sector: "Relative strength against the benchmark and sector peers.",
  } as Record<string, string>,

  /** Plain-language reading of each closed DialState (SPEC-02 §3). */
  dialState: {
    live: {
      label: "live",
      meaning: "This lane has current data and is contributing to the reading.",
    },
    degraded: {
      label: "degraded",
      meaning:
        "This lane answered, but with reduced coverage or quality. It still contributes — read it with the stated caveat.",
    },
    unavailable: {
      label: "unavailable",
      meaning:
        "This lane produced nothing usable, so it contributes nothing. It is shown hollow rather than filled with a guess.",
    },
  } as Record<string, { label: string; meaning: string }>,

  /**
   * The closed DetailCode enum, explained. Without this the UI showed an
   * opaque token like `E7_GATED` and expected the reader to know what it meant.
   */
  detailCode: {
    E7_GATED:
      "Reinforcement-learning candidates are gated behind the isolated research worker (E7). They run only after real training — their output is never simulated.",
    E8_GATED:
      "The scored social lane needs the paid provider tier (E8). Until then this lane reports mention volume only, unscored.",
    THIN_COVERAGE:
      "Too few source items in the window to read confidently. The count is reported rather than padded out.",
    SOURCE_DOWN:
      "The upstream source did not respond. The desk degrades this lane instead of substituting another source.",
    STALE_BEYOND_POLICY:
      "The newest data is older than the freshness policy allows, so this lane is not treated as current.",
    PARTIAL_DATA:
      "Some inputs are present and some are missing; the lane reports on what exists and names the gap.",
  } as Record<string, string>,

  rail: {
    hint: "Select a lane for the reasoning behind its state.",
    expand: (engine: string) => `Show details for ${engine}`,
    collapse: (engine: string) => `Hide details for ${engine}`,
    whyTitle: "Why this state",
    reasonTitle: "Reported reason",
    scopeTitle: "Scope",
    freshnessTitle: "Data through",
    jump: "Go to this panel",
    noReason: "No further reason was reported for this lane.",
  },
  drawer: {
    title: (panel: string) => `How was this computed — ${panel}`,
    provenance: "Provenance",
    factors: "Contributing factors",
    detail: "Full method",
    methodMissing: "methodology unavailable for this section",
  },
  arena: {
    winner: "Winner",
    colCandidate: "Candidate",
    colVal: "Validation",
    colDivergence: "Train−val divergence",
    colPenalty: "Penalty",
    tieNote: "tie broken toward the simpler model",
    queueTitle: "PPO / A2C — queued for the research worker (E7)",
    queueBody: (legs: string) =>
      `tournament completed with ${legs} — RL candidates run only after real training in the isolated research container; their output is never simulated.`,
    firstRun: "first analysis of this ticker — no selection history yet",
  },
  signals: {
    insufficient: "insufficient history (<1y) — percentile omitted",
    collapseTitle: "Signals need more real history",
    collapseBody: (nulls: number, source: string) =>
      `${nulls} signals are unpopulated — a data-depth limitation from ${source}. No value here is estimated.`,
    retry: "Retry",
    healthLink: "data health",
  },
  lanes: {
    newsThin: (n: number) => `7-day news count: ${n} — thin coverage`,
    fallbackNote: "mentions only, unscored — scored lane needs the Finnhub tier (E8)",
    divergenceTitle: "Lanes disagree",
    divergenceBody: (news: string, social: string) =>
      `news lane: ${news} · social lane: ${social} — the desk flags disagreement instead of averaging it away.`,
  },
  sector: {
    benchmarkScope:
      "benchmark view (vs SPY). Peer relative strength and sector percentile arrive with the sector module.",
  },
  errors: {
    sectionTitle: "This panel’s source is unavailable",
    sectionBody: (source: string) => `${source} — the rest of the desk continues.`,
    statusUnavailable:
      "engine status is unavailable right now — dials are hidden rather than guessed.",
  },
  disclaimers: {
    footer: "Research analysis, not investment advice.",
  },
} as const;
