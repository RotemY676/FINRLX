import type {
  EvidenceNarrativeData,
  NewsBundle,
  RecommendationDetail,
  ReplayDetail,
} from "@/services/api";

export interface LLMContextBundle {
  surface: "decision" | "replay" | "news" | "manual";
  recommendation_id: string | null;
  /** The system / instruction prompt the operator should paste at the top. */
  prompt: string;
  /** The full pastable string, system prompt + structured context. */
  text: string;
}

const SYSTEM_PROMPT = `You are FINRLX Analyst — an assistant specialized in the FINRLX decision-intelligence platform.

Rules:
1. Answer ONLY from the context provided below (plus your uploaded knowledge if you are the FINRLX Analyst GPT or Claude Project). Do not invent figures.
2. Cite the section you used ("per the evidence narrative", "per stage 'allocation'", etc.).
3. Do not give investment advice. Do not predict market direction. If asked, decline and explain that FINRLX is decision support, not advice.
4. If the context is insufficient, say so plainly rather than guessing.

The user will paste the FINRLX context block below. They will then ask their question in a follow-up chat message. Acknowledge the context briefly (one line) and wait for the question.`;

function fmtPct(n: number, digits = 2): string {
  return `${(n * 100).toFixed(digits)}%`;
}

function fmtNum(n: number | null | undefined, digits = 2): string {
  if (n == null || Number.isNaN(n)) return "n/a";
  return n.toFixed(digits);
}

export function buildDecisionContext(args: {
  rec: RecommendationDetail | null;
  evidence: EvidenceNarrativeData | null;
}): LLMContextBundle {
  const lines: string[] = [];
  lines.push(SYSTEM_PROMPT, "");
  lines.push("--- FINRLX context: current recommendation ---", "");

  const rec = args.rec;
  if (!rec) {
    lines.push("No recommendation is currently published.");
    return {
      surface: "decision",
      recommendation_id: null,
      prompt: SYSTEM_PROMPT,
      text: lines.join("\n"),
    };
  }

  lines.push(`Recommendation ID: ${rec.id}`);
  lines.push(`Status: ${rec.status}`);
  if (rec.published_at) lines.push(`Published at: ${rec.published_at}`);
  if (rec.data_as_of) lines.push(`Data as of: ${rec.data_as_of}`);
  lines.push(
    `Confidence — data: ${fmtNum(rec.confidence?.data_confidence, 2)}, model: ${fmtNum(rec.confidence?.model_confidence, 2)}, operational: ${fmtNum(rec.confidence?.operational_confidence, 2)}`,
  );
  if (rec.rationale_summary) {
    lines.push("", "Rationale summary:", rec.rationale_summary);
  }

  if (rec.warnings && rec.warnings.length > 0) {
    lines.push("", "Warnings:");
    for (const w of rec.warnings) lines.push(`- ${w}`);
  }

  if (rec.weights && rec.weights.length > 0) {
    lines.push("", "Portfolio weights (top 20 by weight):");
    const top = [...rec.weights]
      .sort((a, b) => (b.target_weight ?? 0) - (a.target_weight ?? 0))
      .slice(0, 20);
    for (const w of top) {
      lines.push(`- ${w.ticker}: ${fmtPct(w.target_weight ?? 0)}`);
    }
  }

  const ev = args.evidence;
  if (ev && ev.items && ev.items.length > 0) {
    lines.push("", "Evidence narrative:");
    for (const item of ev.items) {
      const delta = item.delta_label ? ` [${item.delta_label}]` : "";
      const src = item.source_engine ? ` (engine: ${item.source_engine})` : "";
      lines.push(`${item.order}. ${item.title}${delta}${src}`);
      lines.push(`   ${item.body}`);
      if (item.caveat) lines.push(`   Caveat: ${item.caveat}`);
    }
  }

  lines.push("", "--- end context ---");
  lines.push(
    "",
    "(Acknowledge in one line that you have the context. I will ask my question in the next chat message. Answer strictly from the context above plus your uploaded FINRLX knowledge, with citations, and no investment advice.)",
  );

  return {
    surface: "decision",
    recommendation_id: rec.id,
    prompt: SYSTEM_PROMPT,
    text: lines.join("\n"),
  };
}

export function buildReplayContext(args: {
  replay: ReplayDetail | null;
}): LLMContextBundle {
  const lines: string[] = [];
  lines.push(SYSTEM_PROMPT, "");
  lines.push("--- FINRLX context: replay snapshot ---", "");

  const r = args.replay;
  if (!r) {
    lines.push("No replay loaded.");
    return {
      surface: "replay",
      recommendation_id: null,
      prompt: SYSTEM_PROMPT,
      text: lines.join("\n"),
    };
  }

  lines.push(`Replay ID: ${r.id}`);
  lines.push(`Recommendation ID at snapshot: ${r.recommendation_id}`);
  lines.push(`Captured at: ${r.captured_at}`);
  lines.push(`Status at snapshot: ${r.status}`);
  if (r.data_as_of) lines.push(`Data as of: ${r.data_as_of}`);
  lines.push(
    `Confidence at snapshot — data: ${fmtNum(r.confidence?.data_confidence, 2)}, model: ${fmtNum(r.confidence?.model_confidence, 2)}, operational: ${fmtNum(r.confidence?.operational_confidence, 2)}`,
  );
  if (r.rationale_summary) {
    lines.push("", "Rationale at snapshot:", r.rationale_summary);
  }
  if (r.warnings && r.warnings.length > 0) {
    lines.push("", "Warnings at snapshot:");
    for (const w of r.warnings) lines.push(`- ${w}`);
  }
  if (r.weights && r.weights.length > 0) {
    lines.push("", "Weights at snapshot (top 20):");
    const top = [...r.weights]
      .sort((a, b) => (b.target_weight ?? 0) - (a.target_weight ?? 0))
      .slice(0, 20);
    for (const w of top) lines.push(`- ${w.ticker}: ${fmtPct(w.target_weight ?? 0)}`);
  }
  if (r.stages && r.stages.length > 0) {
    lines.push("", "Pipeline-stage snapshots:");
    for (const stage of r.stages) {
      lines.push(`### Stage: ${stage.stage}`);
      const entries = Object.entries(stage.snapshot_data ?? {});
      for (const [k, v] of entries.slice(0, 10)) {
        const val = typeof v === "object" ? JSON.stringify(v) : String(v);
        lines.push(`- ${k}: ${val.length > 200 ? val.slice(0, 200) + "…" : val}`);
      }
    }
  }

  lines.push("", "--- end context ---");
  lines.push(
    "",
    "(Acknowledge in one line that you have the context. I will ask my question in the next chat message. Answer strictly from the context above plus your uploaded FINRLX knowledge, with citations, and no investment advice.)",
  );

  return {
    surface: "replay",
    recommendation_id: r.recommendation_id,
    prompt: SYSTEM_PROMPT,
    text: lines.join("\n"),
  };
}

export function buildNewsContext(args: {
  bundle: NewsBundle | null;
  maxItems?: number;
}): LLMContextBundle {
  const lines: string[] = [];
  lines.push(SYSTEM_PROMPT, "");
  lines.push("--- FINRLX context: news intelligence ---", "");

  const b = args.bundle;
  const cap = args.maxItems ?? 30;
  if (!b || !b.items || b.items.length === 0) {
    lines.push("No news items available right now.");
    return {
      surface: "news",
      recommendation_id: null,
      prompt: SYSTEM_PROMPT,
      text: lines.join("\n"),
    };
  }
  const s = b.summary;
  lines.push(
    `Aggregate sentiment over ${s.total} headlines: positive=${s.positive}, neutral=${s.neutral}, negative=${s.negative}, mean compound=${fmtNum(s.mean_compound, 3)}.`,
  );
  lines.push(
    "Sentiment is computed by VADER (rule-based). It does not understand financial jargon, ticker slang, or sarcasm — treat scores as a rough orientation.",
  );
  lines.push("", `Headlines (${Math.min(cap, b.items.length)}):`);
  for (const item of b.items.slice(0, cap)) {
    const sentiment = `${item.sentiment_label} ${fmtNum(item.sentiment_compound, 3)}`;
    const date = item.published ? ` · ${item.published}` : "";
    lines.push(`- [${sentiment}] (${item.source}${date}) ${item.title}`);
    if (item.summary) lines.push(`  ${item.summary.slice(0, 280)}`);
  }

  lines.push("", "--- end context ---");
  lines.push(
    "",
    "(Acknowledge in one line that you have the context. I will ask my question in the next chat message. Answer strictly from the context above plus your uploaded FINRLX knowledge, with citations, and no investment advice.)",
  );

  return {
    surface: "news",
    recommendation_id: null,
    prompt: SYSTEM_PROMPT,
    text: lines.join("\n"),
  };
}
