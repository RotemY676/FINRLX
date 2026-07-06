# PROGRAM LEAP — RESUME marker (§2.2)
DONE: F0, F1(backend), F2(core), S1, S2, S3, S4, S6(backend), S8, S9, C1-prep,
and now S5 vertical slice at /simple (spec-conformant One Screen: hero,
indicative progress, dossier with stance-mapping boundary, staleness tiers,
scoreboard, disclaimers; wording test enforcing the ban list; tsc + 45 vitest
+ next build green; backend 1281 green).
CORRECTION to earlier claims: the node toolchain DOES work in this
environment (npm ci + tsc + vitest + next build verified). Still genuinely
blocked here: Playwright browser downloads (domain not allowlisted),
production-network sweeps, and the Actions workflow install (E1 token scope).
Next tasks, in order:
1. S6 UI: /compare page over GET /autopilot/compare (buildable here).
2. S5 polish: autocomplete via asset-search; price chart with regime shading;
   export button reusing /analyze offline-HTML pattern (§5b disclaimers).
3. S7: /pro migration + route flip of /simple -> / (CSV-driven 308s) —
   buildable here; e2e verification needs Playwright (Claude Code).
4. F1.6 staleness badges on Pro surfaces; F3 sweeps (needs browsers/prod);
   C1 close + tag.
