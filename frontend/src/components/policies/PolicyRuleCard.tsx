"use client";

import { useState } from "react";

import { PolicyRule, updatePolicyRule } from "@/services/api";
import { Icon } from "@/components/icons/Icon";

const SEVERITY_STYLE: Record<string, string> = {
  high: "bg-breach-soft text-breach-soft-ink",
  mid: "bg-caution-soft text-caution-soft-ink",
  low: "bg-surface-3 text-ink-3",
};

interface Props {
  rule: PolicyRule;
  /** Actor name written to the audit row when this rule is updated. */
  actor: string;
  onUpdated: (updated: PolicyRule) => void;
  onViewHistory: (key: string) => void;
}

export function PolicyRuleCard({ rule, actor, onUpdated, onViewHistory }: Props) {
  const [editing, setEditing] = useState(false);
  const [draftValue, setDraftValue] = useState(String(rule.threshold_value));
  const [draftReason, setDraftReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cancel = () => {
    setEditing(false);
    setDraftValue(String(rule.threshold_value));
    setDraftReason("");
    setError(null);
  };

  const save = async () => {
    const numeric = Number.parseFloat(draftValue);
    if (Number.isNaN(numeric)) {
      setError("Threshold must be a number.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await updatePolicyRule(rule.key, numeric, actor, draftReason || undefined);
      onUpdated(res.data);
      setEditing(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-2 md:gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center flex-wrap gap-2">
            <h3 className="text-[14px] font-semibold text-ink">{rule.name}</h3>
            <span className={`px-2 py-0.5 rounded-md text-[11px] font-medium ${SEVERITY_STYLE[rule.severity] ?? SEVERITY_STYLE.low}`}>
              {rule.severity}
            </span>
            {!rule.is_enforced && (
              <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-surface-3 text-ink-3">
                advisory only
              </span>
            )}
          </div>
          <p className="text-[12.5px] text-ink-3 mt-1">{rule.description ?? rule.applies_to}</p>
          <p className="text-[11px] text-ink-4 mt-1 font-mono">
            {rule.key} · v{rule.version} · {rule.category}
          </p>
        </div>

        <div className="flex flex-col md:items-end gap-2 shrink-0">
          {!editing ? (
            <>
              <div className="text-[20px] font-display font-semibold text-ink font-mono">
                {rule.threshold_value}
                <span className="text-[12px] text-ink-3 font-sans font-normal ml-1">
                  {rule.threshold_unit}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setEditing(true)}
                  className="inline-flex items-center gap-1 min-h-11 md:min-h-0 md:h-9 px-3 rounded-md bg-surface-3 text-ink-2 text-[12.5px] font-medium hover:bg-line transition-colors"
                >
                  <Icon name="check" size={13} /> Edit
                </button>
                <button
                  type="button"
                  onClick={() => onViewHistory(rule.key)}
                  className="inline-flex items-center gap-1 min-h-11 md:min-h-0 md:h-9 px-3 rounded-md text-ink-3 text-[12.5px] hover:bg-surface-3 transition-colors"
                >
                  <Icon name="clock" size={13} /> History
                </button>
              </div>
            </>
          ) : (
            <div className="space-y-2 w-full md:w-72">
              <label className="block text-[11px] text-ink-3" htmlFor={`thr-${rule.key}`}>
                Threshold ({rule.threshold_unit})
              </label>
              <input
                id={`thr-${rule.key}`}
                type="number"
                inputMode="decimal"
                step="0.01"
                value={draftValue}
                onChange={(e) => setDraftValue(e.target.value)}
                className="w-full min-h-11 px-3 rounded-md border border-line bg-surface text-ink text-[14px] font-mono"
              />
              <label className="block text-[11px] text-ink-3" htmlFor={`rsn-${rule.key}`}>
                Reason (optional)
              </label>
              <input
                id={`rsn-${rule.key}`}
                type="text"
                value={draftReason}
                onChange={(e) => setDraftReason(e.target.value)}
                placeholder="Why is this changing?"
                className="w-full min-h-11 px-3 rounded-md border border-line bg-surface text-ink text-[13px]"
              />
              {error && <p role="alert" className="text-[11px] text-breach">{error}</p>}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={save}
                  className="inline-flex items-center gap-1 min-h-11 md:min-h-0 md:h-9 px-3 rounded-md bg-primary text-primary-ink text-[12.5px] font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  Save
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={cancel}
                  className="inline-flex items-center gap-1 min-h-11 md:min-h-0 md:h-9 px-3 rounded-md text-ink-3 text-[12.5px] hover:bg-surface-3 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
