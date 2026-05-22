"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { Icon } from "@/components/icons/Icon";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import type { LLMContextBundle } from "@/lib/operator/contextBuilder";

/**
 * Compact button that copies a pre-built LLM context bundle to the
 * clipboard and links to the operator console for paste-back. Renders
 * nothing when the operator_console feature flag is off, so adding it
 * to a page has zero cost for non-operator deployments.
 */
export function CopyLLMContextButton({
  bundle,
  label = "Copy LLM context",
  className = "",
}: {
  bundle: LLMContextBundle;
  label?: string;
  className?: string;
}) {
  const { flags } = useFeatureFlags();
  const [state, setState] = useState<"idle" | "copied" | "error">("idle");

  const onCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(bundle.text);
      setState("copied");
      window.setTimeout(() => setState("idle"), 1800);
    } catch {
      setState("error");
      window.setTimeout(() => setState("idle"), 2200);
    }
  }, [bundle.text]);

  if (!flags.operator_console) return null;

  const operatorHref = bundle.recommendation_id
    ? `/operator?rec=${bundle.recommendation_id}&surface=${bundle.surface}`
    : `/operator?surface=${bundle.surface}`;

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <button
        type="button"
        onClick={onCopy}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-3 hover:bg-line text-ink-2 text-[12px] font-medium transition-colors"
        title="Copy a formatted LLM context (system prompt + structured page data) ready to paste into ChatGPT or Claude"
      >
        <Icon
          name={state === "copied" ? "check" : state === "error" ? "alert-triangle" : "share"}
          size={12}
        />
        {state === "copied" ? "Copied" : state === "error" ? "Copy failed" : label}
      </button>
      <Link
        href={operatorHref}
        className="text-[12px] text-primary hover:underline"
        title="Open the operator console to paste an LLM response back into the audit trail"
      >
        Paste response →
      </Link>
    </div>
  );
}
