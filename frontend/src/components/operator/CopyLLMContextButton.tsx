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
 *
 * The disclosure-style "+ embed question" affordance lets the operator
 * pre-load a question into the bundle so a single paste both delivers
 * the context and asks the question — no follow-up message needed.
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
  const [expanded, setExpanded] = useState(false);
  const [question, setQuestion] = useState("");

  const onCopy = useCallback(async () => {
    const q = question.trim();
    const payload = q
      ? `${bundle.text}\n\nMy question: ${q}`
      : bundle.text;
    try {
      await navigator.clipboard.writeText(payload);
      setState("copied");
      window.setTimeout(() => setState("idle"), 1800);
    } catch {
      setState("error");
      window.setTimeout(() => setState("idle"), 2200);
    }
  }, [bundle.text, question]);

  if (!flags.operator_console) return null;

  const operatorHref = bundle.recommendation_id
    ? `/operator?rec=${bundle.recommendation_id}&surface=${bundle.surface}`
    : `/operator?surface=${bundle.surface}`;

  return (
    <div className={`inline-flex flex-col gap-1.5 ${className}`}>
      <div className="inline-flex items-center gap-2 flex-wrap">
        <button
          type="button"
          onClick={onCopy}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-3 hover:bg-line text-ink-2 text-[12px] font-medium transition-colors"
          title="Copy a formatted LLM context (system prompt + structured page data) ready to paste into ChatGPT or Claude. The bundle ends with an instruction asking the LLM to wait for your question — type it as a follow-up message after pasting."
        >
          <Icon
            name={state === "copied" ? "check" : state === "error" ? "alert-triangle" : "share"}
            size={12}
          />
          {state === "copied"
            ? question.trim()
              ? "Copied (with question)"
              : "Copied"
            : state === "error"
              ? "Copy failed"
              : label}
        </button>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="text-[11px] text-ink-3 hover:text-ink"
          aria-expanded={expanded}
          aria-controls={`embed-q-${bundle.surface}`}
          title="Optionally embed a question in the same paste so the LLM answers without a follow-up message"
        >
          {expanded ? "− hide question" : "+ embed question"}
        </button>
        <Link
          href={operatorHref}
          className="text-[12px] text-primary hover:underline"
          title="Open the operator console to paste an LLM response back into the audit trail"
        >
          Paste response →
        </Link>
      </div>
      {expanded && (
        <textarea
          id={`embed-q-${bundle.surface}`}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={2}
          placeholder="Type your question here to embed it in the copy. Leave empty to ask in the chat after pasting."
          className="w-full max-w-xl px-2 py-1.5 rounded-md bg-surface-2 border border-line text-[12.5px] text-ink resize-y"
        />
      )}
    </div>
  );
}
