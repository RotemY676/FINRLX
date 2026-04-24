import type { Config } from "tailwindcss";

/**
 * Design tokens derived from doc 19 Visual Design Direction.
 * Cool neutral backgrounds, clear blue primary, measured green/amber/red.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Primary
        "qp-blue": {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
        // Status
        "qp-green": {
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
        },
        "qp-amber": {
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
        },
        "qp-red": {
          400: "#f87171",
          500: "#ef4444",
          600: "#dc2626",
        },
        // Surfaces (cool neutral)
        "qp-bg": {
          DEFAULT: "#f8fafc",
          card: "#ffffff",
          sidebar: "#f1f5f9",
          hover: "#e2e8f0",
        },
        // Text
        "qp-text": {
          primary: "#0f172a",
          secondary: "#475569",
          muted: "#94a3b8",
        },
        // Borders
        "qp-border": {
          DEFAULT: "#e2e8f0",
          strong: "#cbd5e1",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      fontSize: {
        "qp-hero": ["2rem", { lineHeight: "2.5rem", fontWeight: "700" }],
        "qp-h1": ["1.5rem", { lineHeight: "2rem", fontWeight: "600" }],
        "qp-h2": ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
        "qp-h3": ["1.125rem", { lineHeight: "1.5rem", fontWeight: "500" }],
        "qp-body": ["0.875rem", { lineHeight: "1.25rem" }],
        "qp-small": ["0.75rem", { lineHeight: "1rem" }],
      },
      spacing: {
        "qp-1": "4px",
        "qp-2": "8px",
        "qp-3": "12px",
        "qp-4": "16px",
        "qp-6": "24px",
        "qp-8": "32px",
        "qp-12": "48px",
      },
      borderRadius: {
        "qp": "8px",
        "qp-sm": "4px",
        "qp-lg": "12px",
      },
      transitionDuration: {
        "qp": "180ms",
      },
    },
  },
  plugins: [],
};

export default config;
