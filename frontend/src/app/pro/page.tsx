"use client";

import { DecisionCommandCenter } from "@/components/home/DecisionCommandCenter";

/**
 * LEAP S7a — Pro landing (Decision Command Center).
 * The command center moved here from `/` when Simple Mode became the front
 * door (SIMPLE_MODE_SPEC J0, decision D29/D33). Feature-intact relocation:
 * the component is unchanged; only the route moved. Remaining D33 migration
 * (moving the other manual surfaces under /pro/*) is tracked in RESUME.md.
 */
export default function ProLandingPage() {
  return <DecisionCommandCenter />;
}
