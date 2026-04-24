"use client";

import { useState, useCallback } from "react";
import { Icon } from "@/components/icons/Icon";
import { simulateScenario, ScenarioParamsData, ScenarioResultData } from "@/services/api";

const DELTA_STYLE: Record<string, string> = {
  pos: "text-pos", neg: "text-breach", neutral: "text-ink-3",
};

const DEFAULTS: ScenarioParamsData = {
  horizon_days: 42,
  rate_shock_bps: 0,
  correlation: 0.55,
  earnings_revision_weight: 0.60,
  momentum_engine_on: true,
  flow_engine_on: false,
  policy_constraints_on: true,
};

export function ScenarioCard() {
  const [params, setParams] = useState<ScenarioParamsData>({ ...DEFAULTS });
  const [result, setResult] = useState<ScenarioResultData | null>(null);
  const [loading, setLoading] = useState(false);

  const isModified = JSON.stringify(params) !== JSON.stringify(DEFAULTS);

  const runSimulation = useCallback(async (newParams: ScenarioParamsData) => {
    setLoading(true);
    try {
      const res = await simulateScenario(newParams);
      setResult(res.data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  const updateParam = <K extends keyof ScenarioParamsData>(key: K, value: ScenarioParamsData[K]) => {
    const next = { ...params, [key]: value };
    setParams(next);
    runSimulation(next);
  };

  const reset = () => {
    setParams({ ...DEFAULTS });
    setResult(null);
  };

  return (
    <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Icon name="filter" size={14} className="text-primary" />
        <h3 className="text-[13px] font-semibold text-ink">Scenario controls</h3>
        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${isModified ? "bg-caution-soft text-caution-soft-ink" : "bg-surface-3 text-ink-4"}`}>
          {isModified ? "Modified" : "Baseline"}
        </span>
        {isModified && (
          <button
            onClick={reset}
            className="ml-auto text-[11px] text-ink-3 hover:text-ink transition-colors"
          >
            Reset
          </button>
        )}
      </div>

      {/* Sliders */}
      <div className="space-y-4">
        {/* Horizon */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-[12px] text-ink-2">Horizon</label>
            <span className="text-[12px] font-mono text-ink">{params.horizon_days}d</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-ink-4">1W</span>
            <input
              type="range" min={7} max={180} value={params.horizon_days}
              onChange={(e) => updateParam("horizon_days", Number(e.target.value))}
              className="flex-1 h-1.5 accent-primary"
            />
            <span className="text-[10px] text-ink-4">6M</span>
          </div>
        </div>

        {/* Rate shock */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-[12px] text-ink-2">Rate shock</label>
            <span className="text-[12px] font-mono text-ink">{params.rate_shock_bps > 0 ? "+" : ""}{params.rate_shock_bps} bps</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-ink-4">−200</span>
            <input
              type="range" min={-200} max={200} value={params.rate_shock_bps}
              onChange={(e) => updateParam("rate_shock_bps", Number(e.target.value))}
              className="flex-1 h-1.5 accent-primary"
            />
            <span className="text-[10px] text-ink-4">+200</span>
          </div>
        </div>

        {/* Correlation */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-[12px] text-ink-2">Cross-asset correlation</label>
            <span className="text-[12px] font-mono text-ink">{params.correlation.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-ink-4">0.00</span>
            <input
              type="range" min={0} max={100} value={Math.round(params.correlation * 100)}
              onChange={(e) => updateParam("correlation", Number(e.target.value) / 100)}
              className="flex-1 h-1.5 accent-primary"
            />
            <span className="text-[10px] text-ink-4">1.00</span>
          </div>
        </div>

        {/* Earnings revision weight */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-[12px] text-ink-2">Earnings revision weight</label>
            <span className="text-[12px] font-mono text-ink">{Math.round(params.earnings_revision_weight * 100)}%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-ink-4">0%</span>
            <input
              type="range" min={0} max={100} value={Math.round(params.earnings_revision_weight * 100)}
              onChange={(e) => updateParam("earnings_revision_weight", Number(e.target.value) / 100)}
              className="flex-1 h-1.5 accent-primary"
            />
            <span className="text-[10px] text-ink-4">100%</span>
          </div>
        </div>
      </div>

      {/* Toggles */}
      <div className="mt-4 pt-4 border-t border-line space-y-2.5">
        {[
          { key: "momentum_engine_on" as const, label: "Momentum engine" },
          { key: "flow_engine_on" as const, label: "Options / flow engine" },
          { key: "policy_constraints_on" as const, label: "Policy constraints" },
        ].map(({ key, label }) => (
          <div key={key} className="flex items-center justify-between">
            <span className="text-[12px] text-ink-2">{label}</span>
            <button
              onClick={() => updateParam(key, !params[key])}
              className={`w-9 h-5 rounded-full transition-colors relative ${params[key] ? "bg-primary" : "bg-surface-3"}`}
            >
              <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${params[key] ? "left-[18px]" : "left-0.5"}`} />
            </button>
          </div>
        ))}
      </div>

      {/* Delta preview */}
      {result && result.is_modified && (
        <div className="mt-4 pt-4 border-t border-line">
          <div className="flex items-center gap-4 flex-wrap">
            {result.deltas.map((d) => (
              <div key={d.metric} className="text-[12px]">
                <span className="text-ink-3">{d.metric} </span>
                <span className="text-ink-4 font-mono">{d.baseline}</span>
                <span className="text-ink-4 mx-1">→</span>
                <span className={`font-mono font-medium ${DELTA_STYLE[d.direction] || "text-ink"}`}>{d.modified}</span>
              </div>
            ))}
          </div>
          {result.warnings.length > 0 && (
            <div className="mt-2 space-y-1">
              {result.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-1.5 text-[11px] text-caution">
                  <Icon name="alert-triangle" size={11} className="mt-0.5 shrink-0" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2 mt-3">
            <button className="px-3 py-1.5 rounded-md bg-primary text-primary-ink text-[12px] font-medium hover:opacity-90 transition-opacity">
              Apply to thesis
            </button>
            <button onClick={reset} className="px-3 py-1.5 rounded-md bg-surface-3 text-ink-2 text-[12px] font-medium hover:bg-line transition-colors">
              Discard
            </button>
          </div>
        </div>
      )}

      {loading && (
        <div className="mt-3 text-[11px] text-ink-4 flex items-center gap-1.5">
          <span className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          Simulating...
        </div>
      )}
    </section>
  );
}
