/**
 * iOS viewport lint gate (iPhone / iPad pass).
 *
 * On iOS Safari `vh` resolves against the *largest* viewport — the one with
 * the address bar retracted. A `100vh` / `h-screen` column is therefore taller
 * than the visible area while the bar is showing, so its final row sits under
 * the chrome and cannot be scrolled to. `dvh` tracks the *dynamic* viewport
 * and is the fix. This bites hardest on `overflow-hidden` flex columns (the
 * app shell), where there is no page scroll to rescue the hidden row.
 *
 * Also asserts the shells that opt into `viewport-fit=cover` actually apply
 * safe-area padding: with cover, content paints under the notch and home
 * indicator, so opting in without padding is strictly worse than not opting in.
 *
 * Opt out with `ios-viewport-lint:allow — reason` on the same line.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const SRC_ROOT = join(__dirname, "..");
const BANNED = /\b(h-screen|min-h-screen|max-h-screen)\b|100vh/;
const ALLOW = /ios-viewport-lint:allow/;

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    if (["__tests__", "node_modules", "test-results", "playwright-report"].includes(name)) continue;
    const full = join(dir, name);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else if (/\.(tsx|ts|css)$/.test(full)) out.push(full);
  }
  return out;
}

/** Blank out comments so prose about the rule does not trip the rule. */
function stripComments(src: string): string {
  return src
    .replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, " "))
    .replace(/(^|[^:])\/\/[^\n]*/g, (m) => m.replace(/[^\n]/g, " "));
}

describe("iOS viewport lint", () => {
  it("no h-screen / 100vh in shipped markup — use dvh", () => {
    const offenders: string[] = [];
    for (const file of walk(SRC_ROOT)) {
      const raw = readFileSync(file, "utf8");
      const lines = stripComments(raw).split("\n");
      const rawLines = raw.split("\n");
      lines.forEach((line, i) => {
        if (BANNED.test(line) && !ALLOW.test(rawLines[i] ?? "")) {
          offenders.push(`${file.replace(SRC_ROOT, "src")}:${i + 1} — ${rawLines[i].trim()}`);
        }
      });
    }
    if (offenders.length) {
      throw new Error(
        [
          `iOS viewport lint failed: ${offenders.length} use(s) of vh-based full-height sizing.`,
          ...offenders,
          "",
          "Use dvh (h-dvh / min-h-dvh / calc(100dvh - …)) so the last row stays reachable",
          "while the iOS address bar is visible.",
        ].join("\n"),
      );
    }
    expect(offenders).toEqual([]);
  });

  it("the Simple shell applies safe-area padding under viewport-fit=cover", () => {
    const shell = readFileSync(join(SRC_ROOT, "components", "shell", "SimpleShell.tsx"), "utf8");
    // The layout opts into cover; without these the brand row renders under
    // the status bar in portrait and under the notch in landscape.
    expect(shell).toMatch(/safe-area-pt/);
    expect(shell).toMatch(/safe-area-pl/);
    expect(shell).toMatch(/safe-area-pr/);
  });

  it("viewport-fit=cover is still declared (the padding above assumes it)", () => {
    const layout = readFileSync(join(SRC_ROOT, "app", "layout.tsx"), "utf8");
    expect(layout).toMatch(/viewportFit:\s*"cover"/);
  });
});
