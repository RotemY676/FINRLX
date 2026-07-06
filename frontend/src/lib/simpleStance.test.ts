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
