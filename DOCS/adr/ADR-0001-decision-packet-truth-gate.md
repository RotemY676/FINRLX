# ADR-0001 — Canonical DecisionPacket + evidence-derived TruthGate

- **Status**: Accepted (scaffolding; surface dark by default)
- **Date**: 2026-07-21
- **Context IDs**: SPEC-05 EP-1 (US-DPK-01, US-DPK-03); SPEC-05 EP-0 (US-P0-06, US-P0-07)

## Context

FINRLX surfaces decisions from a legacy `Recommendation` object whose confidence,
freshness, and lineage are spread across several services. The specification requires a
single canonical `DecisionPacket` that joins market-data truth, forecast distribution,
validation evidence, risk frame, lineage, and an explicit capability gate — and mandates
that stale/synthetic data and missing evidence **fail closed** rather than silently
default to eligible.

## Decision

1. Introduce `DecisionPacket` (schema, `app/schemas/decision_packet.py`) as a strict
   (`extra="forbid"`) versioned contract, and a `TruthGate` whose capabilities
   (`can_surface_decision` ⊇ `can_show_target` ⊇ `can_enable_alert`) are **derived from
   evidence in `evaluate_truth_gate`**, never asserted by callers. The gate re-validates
   its own capability hierarchy on construction.
2. Map the existing pipeline to the contract via a **pure, read-only adapter**
   (`decision_packet_adapter.py`) that projects a `Recommendation` + real price freshness
   into one packet per weighted ticker, **without fabricating** absent evidence.
3. Expose it behind the `decision_packet_v1` feature flag (default OFF) at a new
   read-only endpoint, with owner-scoped authorization. Legacy reads are untouched.

## Consequences

- **Positive**: one canonical, testable evidence contract; fail-closed by construction;
  zero blast radius while dark; no competing source of truth (reuses `price_freshness`
  and `Recommendation` lineage).
- **Negative / accepted**: portfolio→per-ticker fan-out produces N packets per rec;
  source-provenance classification is a heuristic until US-DPK-02 lands; packets are not
  yet persisted (no immutable packet ID history).
- **Boundary**: this contract never authorizes broker execution, alerts, notifications,
  or promises of future returns. Backtests remain historical evidence.

## Alternatives considered

- *Extend `RecommendationDetail` in place* — rejected: would overload a legacy contract
  and blur the strict evidence gate.
- *Land the three candidate files as-is with no seam* — rejected: the integration
  requirement calls for the smallest real read-only path, and isolated files would be a
  misleading "done" signal.
