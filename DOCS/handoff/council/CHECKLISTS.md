# PROGRAM LEAP — Council checklists (objective, yes/no)
Each council role reviews the phase diff + a live local run and commits a
verdict file `L<phase>_<ROLE>_VERDICT.md` with PASS or FAIL per item.
Merge gate U8 = four PASS verdicts committed. Max 3 review cycles, then
D26 scope-trim. Verdicts never contain questions to the operator (QZ).

## F.1 Quant Skeptic
- [ ] No feature or signal uses data from after its evaluation time t
- [ ] Any train/validation split is on trading-day windows and non-overlapping
- [ ] Scoring math matches the plan spec (D36) exactly
- [ ] A deliberately-overfit fixture candidate is penalized/rejected by tests
- [ ] Replay/determinism suites are green
- [ ] Every displayed score is reproducible from persisted inputs

## F.2 UX Critic
- [ ] Novice path completes with zero interactions beyond the ticker input
- [ ] Every declared UI state (loading/partial/error/insufficient/stale) is reachable and rendered
- [ ] No text below the readable floor; typography per Master Plan rule 6
- [ ] Mobile layout stacks correctly; no horizontal scroll
- [ ] Drill-ins open and close without losing page state
- [ ] Loading states name their pipeline stage in plain language

## F.3 Truthfulness Auditor
- [ ] Advice-verb scan clean (buy/sell/should/guaranteed/will outperform)
- [ ] Every displayed number has evidence drill-in or provenance stamp
- [ ] Research-analysis disclaimer present on dossier/compare/export surfaces
- [ ] RL outputs labeled research-only; no promotion-implying copy
- [ ] Isolation regression test (tournament never touches recommendations) present and green
- [ ] Data staleness/degradation is visibly labeled, never silently hidden

## F.4 Security/Ops
- [ ] All user input (tickers, params) validated server-side; parameterized queries only
- [ ] No secrets in diff, fixtures, or logs
- [ ] Migrations additive with tested downgrade
- [ ] Failed jobs cannot remain in `running` state (timeout/finalize path tested)
- [ ] New endpoints covered by existing rate-limit/auth conventions
- [ ] Post-merge smoke plan stated (or SKIPPED-with-reason recorded)
