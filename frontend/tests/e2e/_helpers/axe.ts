import AxeBuilder from "@axe-core/playwright";
import { type Page, expect } from "@playwright/test";

/**
 * Known-acceptable axe rule IDs the design currently violates. They are real
 * a11y issues, NOT to be treated as fixed — they're tracked for a dedicated
 * design pass (logged in DOCS/handoff/MVP_6_TESTING_FOUNDATION.md). The CI
 * gate flags new violations introduced after this baseline; anything in this
 * list is logged but doesn't fail the build.
 *
 * When a rule is fixed, REMOVE it from this list so a regression re-fails CI.
 */
const KNOWN_PREEXISTING_RULES = new Set<string>([]);

export async function expectNoSeriousAxeViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();

  const critical = results.violations.filter((v) => v.impact === "critical");
  const newSerious = results.violations.filter(
    (v) => v.impact === "serious" && !KNOWN_PREEXISTING_RULES.has(v.id)
  );

  // critical = always fail. newSerious = fail (something fresh slipped in).
  const fatal = [...critical, ...newSerious];
  if (fatal.length > 0) {
    const summary = fatal.map((v) => {
      const lines = [`${v.id} (${v.impact}): ${v.help} — ${v.nodes.length} nodes`];
      // Surface the first 3 nodes per rule so a failing CI run gives an actionable trail.
      for (const node of v.nodes.slice(0, 3)) {
        lines.push(`  - ${node.target.join(" ")} :: ${node.failureSummary?.split("\n")[1]?.trim() ?? ""}`);
      }
      return lines.join("\n");
    });
    throw new Error(`axe found ${fatal.length} disallowed violations:\n${summary.join("\n")}`);
  }
  expect(fatal).toEqual([]);
}
