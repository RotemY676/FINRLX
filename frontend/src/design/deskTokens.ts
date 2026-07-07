/**
 * Desk W1 — design tokens (SPEC-03 \u00A71). Single source for the Desk v2 tree.
 * Semantic colors are for stance/flag semantics ONLY (decorative use is a
 * review defect). Dashed borders mean operator-gated, everywhere.
 */
export const tokens = {
  color: {
    accent: "#0E7C7B",
    accentHover: "#0B6362",
    accentSubtle: "rgba(14,124,123,0.08)",
    semantic: {
      constructive: "#1E7F4F",
      cautious: "#B8860B",
      risk: "#B3261E",
    },
    neutral: {
      n950: "#0F1520", n900: "#1A2332", n800: "#2A3648", n600: "#5A6472",
      n400: "#8A93A0", n300: "#C9D1DA", n200: "#E6EBF0", n100: "#F2F5F8",
      n050: "#FAFBFC",
    },
  },
  space: (n: number) => `${n * 8}px`,
  radius: { panel: "12px", card: "8px", chip: "15px" },
  border: {
    hairline: "1px solid #C9D1DA",
    gated: "1.5px dashed #B8860B",
    error: "1px solid #B3261E",
  },
  motion: { crossfadeMs: 150, drawerMs: 200 },
  type: {
    // tabular numerals are a token, not a per-component choice (R2-U1)
    numeric: { fontVariantNumeric: "tabular-nums" as const },
    scale: { xl: "28px", lg: "20px", md: "16px", sm: "14px", xs: "12px" },
    lineHeight: 1.45,
  },
} as const;

export type DialState = "live" | "degraded" | "unavailable";
export type DetailCode =
  | "E7_GATED" | "E8_GATED" | "THIN_COVERAGE" | "SOURCE_DOWN"
  | "STALE_BEYOND_POLICY" | "PARTIAL_DATA";
