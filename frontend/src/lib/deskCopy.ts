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
