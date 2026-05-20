import { describe, expect, it } from "vitest";

import { fmtDate, fmtDateTime, fmtTime } from "./format";

describe("format date helpers", () => {
  it("returns an em-dash for nullish input", () => {
    expect(fmtDate(null)).toBe("—");
    expect(fmtDate(undefined)).toBe("—");
    expect(fmtDate("")).toBe("—");
    expect(fmtDateTime(null)).toBe("—");
    expect(fmtTime(null)).toBe("—");
  });

  it("formats an ISO timestamp identically regardless of host timezone", () => {
    // UTC-only fields (see lib/format.ts comment) — output must be stable.
    expect(fmtDateTime("2026-05-20T14:30:00Z")).toBe("2026-05-20 14:30");
    expect(fmtDate("2026-05-20T14:30:00Z")).toBe("2026-05-20");
    expect(fmtTime("2026-05-20T14:30:00Z")).toBe("14:30");
  });

  it("zero-pads single-digit month / day / hour / minute", () => {
    expect(fmtDateTime("2026-01-03T07:05:00Z")).toBe("2026-01-03 07:05");
  });

  it("returns em-dash on an unparseable input string", () => {
    expect(fmtDate("not-a-date")).toBe("—");
    expect(fmtDateTime("not-a-date")).toBe("—");
    expect(fmtTime("not-a-date")).toBe("—");
  });
});
