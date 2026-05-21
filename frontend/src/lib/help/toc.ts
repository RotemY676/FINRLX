import type { HelpArea } from "./types";

export const AREA_META: Record<HelpArea, { title: string; description: string; order: number }> = {
  "getting-started": {
    title: "Getting started",
    description: "Take the product tour, run your first decision, and learn the workspace.",
    order: 1,
  },
  concepts: {
    title: "Concepts",
    description: "The mental model behind weights, agents, regimes, and governance.",
    order: 2,
  },
  guides: {
    title: "How-to guides",
    description: "Task-oriented recipes for the work you do every week.",
    order: 3,
  },
  reference: {
    title: "Reference",
    description: "Per-page anatomy, status chips, policy controls, metrics, and the REST API.",
    order: 4,
  },
  glossary: {
    title: "Glossary",
    description: "Plain-English definitions for every term used across the product.",
    order: 5,
  },
  faq: {
    title: "FAQ",
    description: "Common questions, grouped by intent.",
    order: 6,
  },
  troubleshooting: {
    title: "Troubleshooting",
    description: "Symptoms, likely causes, and what to do next.",
    order: 7,
  },
  changelog: {
    title: "Changelog",
    description: "What changed and when, newest first.",
    order: 8,
  },
  disclaimers: {
    title: "Disclaimers & legal",
    description: "How to read recommendations, and the boundaries of what FINRLX is.",
    order: 9,
  },
  root: {
    title: "Help center",
    description: "Search, top tasks, and what's new.",
    order: 0,
  },
};

export const AREAS_IN_ORDER: HelpArea[] = (
  Object.entries(AREA_META) as [HelpArea, (typeof AREA_META)[HelpArea]][]
)
  .filter(([area]) => area !== "root")
  .sort((a, b) => a[1].order - b[1].order)
  .map(([area]) => area);
