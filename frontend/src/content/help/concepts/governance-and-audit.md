---
title: Governance and audit
summary: Provenance, replay, breach trails — how every recommendation stays reproducible.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 7
---

Every recommendation in FINRLX carries the full chain of evidence used to produce it. This is the governance layer: a discipline of recording *what was true at decision time* so any past output can be examined, explained, and reproduced. The discipline is not aesthetic — it is the only credible answer to the question "why did the system do that?"

## What gets recorded

For every published recommendation, the audit trail captures:

- **Data snapshot identifier.** The exact bytes the engine saw at decision time.
- **Feature spec.** The list of features, their parameters, their normalization policy.
- **Engine version + seed.** Which algorithm, which hyperparameters, which random seed.
- **Policy controls in force.** Every named control (cash floor, confidence floors, exposure caps, turbulence threshold) at the precise values applied.
- **Overlay decisions.** For each active overlay, the raw engine output and the projected output. If a breach was raised, the constraint that fired.
- **User actions.** Every promote, defer, save-as-thesis, or policy edit, with the actor, timestamp, and reason if supplied.
- **Recommendation outputs.** The published weights, the supporting evidence narrative, the alignment with other engines if a comparison was run.

This is a flat record, not a hierarchical one. Every event has a timestamp, an actor (system or user), and the prior state hash it modified. The audit trail is immutable — entries can be marked acknowledged or resolved, but not deleted.

## What replay does

The [Replay page](/help/reference/pages/replay) lets you pick any past recommendation and *reconstruct* it. Reconstruction means:

- Loading the data snapshot.
- Loading the feature spec and recomputing features against that snapshot.
- Loading the engine version + seed.
- Running the engine on the reconstructed state.
- Applying the overlay with the policy controls that were in force.

The output should be byte-identical to the original published weights. If it is not, something in the chain has changed — usually because a feature implementation was updated after the recommendation was published. Replay surfaces the discrepancy and links to the change that introduced it.

This is the property that makes the system auditable. You cannot ask "why did the engine choose AAPL over MSFT on 2025-08-12" without being able to answer "what data did it see, what policy was in force, what model was running, what was the breach state?" Replay answers all of those.

## The guarantees

FINRLX makes three explicit guarantees about replay:

1. **Determinism within version.** A recommendation produced on engine version *v* with seed *s* on data snapshot *d* replays identically on the same *v*, *s*, *d*.
2. **Cross-version drift surfaced.** If you replay a recommendation against a newer engine version, the system flags the version delta and runs both — old and new — so you can see what changed.
3. **Snapshot integrity.** Data snapshots are content-addressed. A replay that requests a snapshot validates its hash; a corrupted snapshot fails loudly rather than producing the wrong answer.

## What governance does *not* do

Three things it is important not to expect:

- **Causal explanation.** The audit trail tells you *what* the engine did and *what it saw*, not *why* the policy is correct. The "why" is your job, informed by the trail.
- **Free-form reasoning logs.** RL agents do not narrate. The "evidence narrative" you see on the [Decision page](/help/reference/pages/decision) is *computed* from inputs and outputs — it is not a transcript of the engine's thoughts. Treat it as a structured summary, not a confession.
- **Real-time fraud detection.** Governance records what happened so you can find anomalies after the fact. It does not block anomalies in real time — that's the overlay's job.

## Practical implications

- When you promote a recommendation to paper, the audit trail captures the engine state at promotion. If paper later diverges from the engine's intent, replay tells you whether the engine is consistent and execution is drifting, or vice versa.
- When you edit a policy, the edit is versioned. The next recommendation cycle picks up the new values, but the *prior* recommendation is replayable under the *prior* policy. Both states are recoverable.
- When you investigate a breach, replay is the first tool. The state at the moment of the breach is reconstructible; the conditions that triggered it are visible; the policy edit (if any) that resolved it is recorded.

## See also

- [The weight-centric pipeline](/help/concepts/weight-centric-pipeline) — what governance records.
- [Replay a decision](/help/guides/replay-a-decision) — the recipe.
- [Investigate a breach](/help/guides/investigate-a-breach) — where governance pays off.
