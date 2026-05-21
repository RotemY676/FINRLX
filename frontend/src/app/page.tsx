"use client";

import { DecisionCommandCenter } from "@/components/home/DecisionCommandCenter";

/**
 * FINRLX Home — Decision Command Center.
 *
 * Replaces the previous greeting + next-actions overview with a decision-
 * oriented command center. See:
 *   - .claude/skills/finrlx-home-command-center/SKILL.md
 *   - DOCS/handoff/PHASE_HOME1_DECISION_COMMAND_CENTER_REPORT.md
 */
export default function HomePage() {
  return <DecisionCommandCenter />;
}
