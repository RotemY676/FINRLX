/**
 * Phase UX-5.1 — tokens.json contract.
 *
 * tokens.json is the source of truth for iOS bridging (Swift codegen).
 * It must stay in lockstep with globals.css :root and :root[data-theme=dark]
 * so the iOS app renders the same colors as the web. This test parses the
 * raw CSS, extracts the --var declarations from each theme block, and
 * verifies every key in tokens.color.{light,dark} matches.
 *
 * To fix a failure: edit globals.css OR tokens.json so the values match,
 * then re-run. Failing this test means we'd ship an iOS build with off-by-
 * a-shade colors compared to the web.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import tokens from "../design/tokens.json";

const GLOBALS = readFileSync(
  join(__dirname, "..", "app", "globals.css"),
  "utf8",
);

function extractBlock(css: string, selector: string): Record<string, string> {
  // Capture everything between the first occurrence of `selector {` and the
  // matching `}` — simple bracket count is enough for these flat blocks.
  const start = css.indexOf(`${selector} {`);
  if (start < 0) throw new Error(`Selector not found in globals.css: ${selector}`);
  let depth = 0;
  let i = css.indexOf("{", start);
  const bodyStart = i + 1;
  for (; i < css.length; i++) {
    if (css[i] === "{") depth++;
    else if (css[i] === "}") {
      depth--;
      if (depth === 0) break;
    }
  }
  const body = css.slice(bodyStart, i);
  // Strip comments to avoid picking declarations inside /* … */.
  const stripped = body.replace(/\/\*[\s\S]*?\*\//g, "");
  const out: Record<string, string> = {};
  for (const line of stripped.split("\n")) {
    const m = line.match(/^\s*--([a-zA-Z0-9-]+):\s*([^;]+);/);
    if (m) out[m[1]] = m[2].trim();
  }
  return out;
}

describe("tokens.json contract with globals.css (UX-5.1)", () => {
  const lightCss = extractBlock(GLOBALS, ":root");
  const darkCss = extractBlock(GLOBALS, ':root[data-theme="dark"]');

  it("every color key in tokens.color.light matches globals.css :root", () => {
    for (const [key, value] of Object.entries(tokens.color.light)) {
      expect(lightCss[key], `--${key} value mismatch`).toBe(value);
    }
  });

  it("every color key in tokens.color.dark matches globals.css :root[data-theme=dark]", () => {
    for (const [key, value] of Object.entries(tokens.color.dark)) {
      expect(darkCss[key], `--${key} value mismatch (dark)`).toBe(value);
    }
  });

  it("globals.css doesn't declare a color custom property the JSON forgot", () => {
    // The JSON intentionally excludes some non-color tokens (radii, shadows,
    // typography). It must cover every color-shaped variable, though —
    // anything starting with canvas/surface/ink/primary/pos/caution/breach/accent.
    const colorPrefix = /^(canvas|surface|line|ink|primary|pos|caution|breach|accent)/;
    const missing = Object.keys(lightCss).filter(
      (k) => colorPrefix.test(k) && !(k in tokens.color.light),
    );
    expect(missing, `globals.css has color tokens not in tokens.json: ${missing.join(", ")}`).toEqual([]);
  });
});
