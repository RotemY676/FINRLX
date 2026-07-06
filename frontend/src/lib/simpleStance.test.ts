/**
 * LEAP S5 — stance-mapping unit tests + the binding wording test
 * (SIMPLE_MODE_SPEC J2: the payload's raw engine stance vocabulary and the
 * copy-deck ban list must never appear in Simple Mode component sources).
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { SIMPLE_MODE_BANNED_WORDS, stanceTone, toSimpleStance } from "./simpleStance";

describe("toSimpleStance (binding UI boundary)", () => {
  it("maps the engine vocabulary to research language", () => {
    expect(toSimpleStance("buy")).toBe("constructive");
    expect(toSimpleStance("hold")).toBe("neutral");
    expect(toSimpleStance("sell")).toBe("cautious");
    expect(toSimpleStance("trim")).toBe("cautious");
  });
  it("is case-insensitive and safe on unknown/missing values", () => {
    expect(toSimpleStance("BUY")).toBe("constructive");
    expect(toSimpleStance("unknown")).toBe("neutral");
    expect(toSimpleStance(null)).toBe("neutral");
    expect(toSimpleStance(undefined)).toBe("neutral");
  });
  it("tones map to existing token families only", () => {
    expect(stanceTone("constructive")).toBe("pos");
    expect(stanceTone("neutral")).toBe("neutral");
    expect(stanceTone("cautious")).toBe("caution");
  });
});

describe("Simple Mode wording test (safe-language enforcement)", () => {
  const roots = [
    join(__dirname, "..", "app", "simple"),
    join(__dirname, "..", "app", "compare"),
    join(__dirname, "..", "components", "simple"),
  ];

  function sourceFiles(dir: string): string[] {
    return readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
      e.isDirectory() ? sourceFiles(join(dir, e.name)) : [join(dir, e.name)],
    );
  }

  it("banned words never appear as rendered words in Simple Mode sources", () => {
    const offenders: string[] = [];
    for (const root of roots) {
      for (const file of sourceFiles(root)) {
        if (!/\.(tsx|ts)$/.test(file) || file.endsWith(".test.ts")) continue;
        // Strip comments: bans apply to code/JSX that can reach the DOM.
        const src = readFileSync(file, "utf-8")
          .replace(/\/\*[\s\S]*?\*\//g, "")
          .replace(/^\s*\/\/.*$/gm, "");
        for (const word of SIMPLE_MODE_BANNED_WORDS) {
          const re = new RegExp(`(?<![A-Za-z])${word.replace(" ", "\\s+")}(?![A-Za-z])`, "i");
          if (re.test(src)) offenders.push(`${file}: "${word}"`);
        }
      }
    }
    expect(offenders).toEqual([]);
  });
});

describe("exported dossier HTML (spec §5b bindings)", () => {
  it("embeds disclaimers, freshness stamp, penalty column, and mapped stance", async () => {
    const { dossierToHtml } = await import("./exportDossier");
    const html = dossierToHtml({
      ticker: "EXP",
      generated_at: "2026-07-06T00:00:00Z",
      config_version: "v",
      freshness: { latest_bar: "2026-07-03", bars: 10, news_source_available: true },
      summary: {
        latest_close: 1,
        stance: "sell",
        composite_score: 0,
        avg_confidence: 0,
        regime: "downtrend",
        stance_kind: "",
      },
      sections: {
        technical: {
          available: true,
          features: { rsi_14: 40 },
          regime: { label: "downtrend", detail: "", kind: "" },
          composite: { stance: "sell", composite_score: 0, avg_confidence: 0 },
        },
        news_sentiment: { available: true, note: null, counts: {}, items_7d: [] },
        fundamentals: { available: false, note: "n/a" },
        model_insight: {
          candidates: [
            { key: "k", name: "Cand", kind: "ml", train_sharpe: 1, val_sharpe: 0.5, divergence: 0.5, penalty: 0.4, score: 0.1 },
          ],
          winner: { key: "k", name: "Cand", kind: "ml", train_sharpe: 1, val_sharpe: 0.5, divergence: 0.5, penalty: 0.4, score: 0.1, rationale: "r" },
          rl: { status: "queued_for_research_run" },
        },
      },
      price_series: [],
      disclaimers: ["Research analysis, not investment advice."],
    });
    expect(html).toContain("not investment advice");
    expect(html).toContain("Data through <strong>2026-07-03</strong>");
    expect(html).toContain("<th>Penalty</th>");
    expect(html).toContain("cautious"); // sell -> cautious via the boundary
    expect(html).not.toMatch(/>\s*sell\s*</); // raw word never rendered
    expect(html).toContain("queued_for_research_run");
  });
});
