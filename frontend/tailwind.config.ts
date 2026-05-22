import type { Config } from "tailwindcss";

/**
 * Design tokens from design/handoff-package/styles.css.
 * Colors reference CSS custom properties for light/dark theme support.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        surface: { DEFAULT: "var(--surface)", 2: "var(--surface-2)", 3: "var(--surface-3)" },
        line: { DEFAULT: "var(--line)", strong: "var(--line-strong)" },
        ink: { DEFAULT: "var(--ink)", 2: "var(--ink-2)", 3: "var(--ink-3)", 4: "var(--ink-4)" },
        primary: {
          DEFAULT: "var(--primary)",
          ink: "var(--primary-ink)",
          soft: "var(--primary-soft)",
          "soft-ink": "var(--primary-soft-ink)",
        },
        pos: { DEFAULT: "var(--pos)", soft: "var(--pos-soft)", "soft-ink": "var(--pos-soft-ink)" },
        caution: {
          DEFAULT: "var(--caution)",
          soft: "var(--caution-soft)",
          "soft-ink": "var(--caution-soft-ink)",
        },
        breach: {
          DEFAULT: "var(--breach)",
          soft: "var(--breach-soft)",
          "soft-ink": "var(--breach-soft-ink)",
        },
        accent: { DEFAULT: "var(--accent)", 2: "var(--accent-2)" },
        // Phase 3 semantic aliases — map state semantics onto existing
        // palette via CSS variables defined in globals.css.
        stale: {
          DEFAULT: "var(--stale)",
          soft: "var(--stale-soft)",
          "soft-ink": "var(--stale-soft-ink)",
        },
        blocked: {
          DEFAULT: "var(--blocked)",
          soft: "var(--blocked-soft)",
          "soft-ink": "var(--blocked-soft-ink)",
        },
        governance: {
          DEFAULT: "var(--governance)",
          soft: "var(--governance-soft)",
          "soft-ink": "var(--governance-soft-ink)",
        },
        shadow: {
          DEFAULT: "var(--shadow)",
          soft: "var(--shadow-soft)",
          "soft-ink": "var(--shadow-soft-ink)",
        },
      },
      // Phase 3 typography scale (playbook §3.3). Existing `text-[Npx]`
      // utilities still work; named tokens are how Phases 5–10 opt into
      // the new readable scale. Compact + comfortable density modes
      // adjust via :root[data-density="…"] in globals.css.
      fontSize: {
        "page-title": ["28px", { lineHeight: "1.2", fontWeight: "600" }],
        "section-title": ["20px", { lineHeight: "1.3", fontWeight: "600" }],
        "card-title": ["16px", { lineHeight: "1.4", fontWeight: "600" }],
        body: ["15px", { lineHeight: "1.5" }],
        "body-sm": ["14px", { lineHeight: "1.5" }],
        table: ["14px", { lineHeight: "1.4" }],
        caption: ["12.5px", { lineHeight: "1.4" }],
        meta: ["12.5px", { lineHeight: "1.4" }],
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        display: ["var(--font-display)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: {
        sm: "var(--r-sm)",
        md: "var(--r-md)",
        lg: "var(--r-lg)",
        xl: "var(--r-xl)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
      },
      spacing: {
        pad: "var(--dens-pad)",
        gap: "var(--dens-gap)",
        row: "var(--dens-row)",
      },
      transitionDuration: {
        DEFAULT: "180ms",
      },
    },
  },
  plugins: [],
};

export default config;
