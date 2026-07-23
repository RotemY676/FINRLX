"use client";

/**
 * /pro/models — the Model lab tab.
 *
 * Fail-closed behind `model_lab` (DEC-7 pattern, matching the desk): the flag
 * is OFF by default and during the loading window, so the tab is invisible
 * until deliberately enabled per environment.
 */

import Link from "next/link";

import { ModelLab } from "@/components/models/ModelLab";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";

export default function ModelLabPage() {
  const { flags, isLoading } = useFeatureFlags();

  if (isLoading) {
    return <p className="px-4 py-10 text-sm text-ink-2">Loading…</p>;
  }
  if (!flags.model_lab) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <p className="text-sm text-ink-2">
          The model lab is not enabled in this environment.
        </p>
        <Link href="/pro" className="mt-4 inline-block text-sm text-primary underline">
          Back to Pro
        </Link>
      </div>
    );
  }
  return <ModelLab />;
}
