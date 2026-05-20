/**
 * Phase UX-1.5 — Touch target lint gate.
 *
 * Apple HIG and WCAG 2.5.5 both mandate a 44pt floor on interactive controls.
 * On mobile, this is enforced via class:
 *   - `min-h-11` (44px on Tailwind's default 4px scale) or
 *   - `h-11 w-11` for icon-only buttons, or
 *   - `min-h-11 md:min-h-0` if desktop wants tighter spacing.
 *
 * This test scans every .tsx in src/ for `<button` JSX that ships with a
 * fixed `h-6` / `h-7` / `h-8` / `h-9` class AND no `min-h-11` override on the
 * same element. Any hit fails the test with file:line.
 *
 * To add an intentional exception, leave a comment on the same line:
 *   // touch-target-lint:allow — reason
 *
 * Why a unit test instead of an eslint rule? It runs in the same vitest CI
 * job that already gates the frontend, no new toolchain, no plugin churn.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const SRC_ROOT = join(__dirname, "..");
// 44pt floor = h-11 on Tailwind's default 4px scale. h-6..h-10 all fail.
const TOO_SHORT = /\bh-(6|7|8|9|10)\b/;
const HAS_OVERRIDE = /\bmin-h-(11|12|14|16)\b/;
const HAS_FIXED_TALL = /\bh-(11|12|14|16)\b/;
const ALLOW_TAG = /touch-target-lint:allow/;
// "hidden ... md:|lg:|xl: reveal" means the element only shows at >=md, where
// pointer (not touch) is the assumed input. Treated as exempt from the 44pt rule.
const POINTER_ONLY = /\bhidden\b/;
const REVEALED_ON_POINTER = /\b(md|lg|xl|2xl):(inline-flex|inline-block|inline|flex|block|grid|table|inline-grid)\b/;

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      // Skip generated / test directories
      if (["__tests__", "test-results", "playwright-report", "node_modules"].includes(name)) continue;
      out.push(...walk(full));
    } else if (name.endsWith(".tsx")) {
      out.push(full);
    }
  }
  return out;
}

function classNamesOnLine(line: string): string[] {
  // Capture both className="..." and className={`...`} contents.
  const out: string[] = [];
  const dq = /className=\"([^\"]*)\"/g;
  const tpl = /className=\{`([^`]*)`\}/g;
  let m: RegExpExecArray | null;
  while ((m = dq.exec(line))) out.push(m[1]);
  while ((m = tpl.exec(line))) out.push(m[1]);
  return out;
}

describe("touch target lint (UX-1.5 gate)", () => {
  it("no <button> ships with h-6/h-7/h-8/h-9 and no min-h-11 override", () => {
    const offenders: string[] = [];

    for (const file of walk(SRC_ROOT)) {
      const lines = readFileSync(file, "utf8").split("\n");
      let openButton = false;
      let buttonStart = -1;
      let bufferedClasses = "";

      lines.forEach((line, i) => {
        // Open <button or className-bearing line of a <button …> tag.
        if (/<button\b/.test(line) && !ALLOW_TAG.test(line)) {
          openButton = true;
          buttonStart = i;
          bufferedClasses = "";
        }
        if (openButton) {
          bufferedClasses += " " + classNamesOnLine(line).join(" ");
          if (line.includes(">")) {
            // End of opening tag — evaluate.
            const isPointerOnly =
              POINTER_ONLY.test(bufferedClasses) && REVEALED_ON_POINTER.test(bufferedClasses);
            if (
              TOO_SHORT.test(bufferedClasses) &&
              !HAS_OVERRIDE.test(bufferedClasses) &&
              !HAS_FIXED_TALL.test(bufferedClasses) &&
              !isPointerOnly
            ) {
              offenders.push(
                `${file.replace(SRC_ROOT, "src")}:${buttonStart + 1} — fixed short height ` +
                  `without min-h-11 override; classes: "${bufferedClasses.trim()}"`,
              );
            }
            openButton = false;
            buttonStart = -1;
            bufferedClasses = "";
          }
        }
      });
    }

    if (offenders.length) {
      // Print all so a fix sweep doesn't need multiple runs.
      const msg = [
        `Touch-target lint failed: ${offenders.length} <button> elements below 44pt without override.`,
        ...offenders,
        "",
        "To fix: add min-h-11 (mobile) and optionally md:min-h-0 (desktop tighter).",
        "To opt out: append // touch-target-lint:allow — reason on the <button line.",
      ].join("\n");
      throw new Error(msg);
    }
    expect(offenders).toEqual([]);
  });
});
