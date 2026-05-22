# FINRLX UX/UI Transformation — Phase 0 Audit Report

> Master Phase 0 deliverable for the program defined in
> `DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md`. Cross-references the
> four other Phase 0 outputs:
>
> - `DOCS/handoff/FINRLX_UX_PHASE_0_PAGE_INVENTORY.csv`
> - `DOCS/handoff/FINRLX_UX_PHASE_0_SKILL_INVENTORY.md`
> - `DOCS/handoff/FINRLX_UX_PHASE_0_BENCHMARK_SYNTHESIS.md`
> - `DOCS/handoff/FINRLX_UX_PHASE_0_REDLINE_BACKLOG.md`
>
> Phase 0 follows plan §0 rule "Inspect before editing." No product UI
> changes have been made. Only the five Phase 0 documents listed in plan §5
> were created.

## A. Summary

FINRLX is a Next.js 14 / TypeScript frontend backed by a FastAPI service.
The frontend ships ~25 routes and a mature OKLCH design-token system
inherited from the QuantPipeline prototype. The product already has
correct safety scaffolding (persistent disclaimer banner, fail-closed
feature flags, source-grounded recommendation primitives, six skills
governing recommendation provenance / replay determinism / backtest
hygiene / fintech copy / feature gating), but it suffers from three
foundational UX issues:

1. **Tiny typography.** Default body is 13.5 px (`--dens-text: 13.5px`),
   metadata is 11 px in many components, section labels are 10 px. The
   master plan target is 15 px body / 12.5 px minimum metadata.
2. **Flat IA with 16 sidebar entries split into two ungrouped sections.**
   The six target product areas (Home / Research / Decisions / Portfolio &
   Risk / Insights / Ops & Governance) are not yet expressed in
   navigation. Several pages are nested at the wrong level (`/comparison`
   and `/replay` are sub-flows of Decisions; `/profile` is account, not
   workspace).
3. **Home and Decision pages stack too many panels.** Home already runs
   nine panels; Decision is one long scroll. Both need progressive
   disclosure and tier-1/tier-2 split.

The redesign program is well-positioned: existing tokens, components, and
safety skills can be **extended** rather than replaced. No major
architectural rewrite is required to reach the plan's target state.

## B. Skills Used

Phase 0 is research-only. No skill enforcement was applicable to the
file creations performed (the five Phase 0 documents are non-product
docs). Existing FINRLX safety skills were consulted to confirm boundaries:

- `fintech-disclaimer-and-marketing-guard` — used to verify forbidden-verb
  patterns when reading product copy. No verb violations were observed in
  inspected pages.
- `feature-flag-kill-switch` — referenced to map nav entries to their
  flags (Workspaces and Operations entries in `Sidebar.tsx`).
- `recommendation-object-provenance` and `replay-determinism-harness` —
  referenced as constraints on future Decision/Replay redesigns (Phase 7).
- `backtest-hygiene-gate` — referenced as a constraint on the future
  Research/Backtests redesign (Phases 6/10).
- `finrlx-home-command-center` — read as the structural precedent for how
  the new Phase-1 skills should be authored.

**Skills not found** — five out of five plan-§1.5 redesign skills are
missing. They are explicit Phase 1 deliverables and were *not* created in
Phase 0. See `FINRLX_UX_PHASE_0_SKILL_INVENTORY.md` §2.

## C. External References Reviewed

10 financial-product benchmarks (TradingView, Koyfin, Finviz, Simply Wall
St, AlphaSense, TipRanks, TrendSpider, YCharts, TIKR, plus Bloomberg
Terminal as an out-of-band reference) and 6 user-pain forum threads
(r/TradingView, three r/UXDesign threads, r/investing, r/ValueInvesting,
r/webdev). NN/g, Smashing, UX Pilot, and UXDesign.cc dashboards/AI articles
also reviewed. All takeaways and how they map to FINRLX are in
`FINRLX_UX_PHASE_0_BENCHMARK_SYNTHESIS.md`.

Gate 0 thresholds: ≥ 8 competitors, ≥ 5 user-pain sources. Met (10/6).

**Honest limitation.** Phase 0 did not fetch any of those URLs in this
session — the takeaways are derived from the master plan's curated lists
plus prior FINRLX team reviews. Phase 1 should re-fetch via `WebFetch` and
diff against the synthesis file before locking the playbook.

## D. Files Changed

| File | Purpose |
|---|---|
| `DOCS/handoff/FINRLX_UX_PHASE_0_AUDIT_REPORT.md` | This master Phase 0 report. |
| `DOCS/handoff/FINRLX_UX_PHASE_0_PAGE_INVENTORY.csv` | 25-row inventory of routes with disposition, owning phase, mobile/data-freshness notes. |
| `DOCS/handoff/FINRLX_UX_PHASE_0_SKILL_INVENTORY.md` | Inventory of present / missing / external skills. |
| `DOCS/handoff/FINRLX_UX_PHASE_0_BENCHMARK_SYNTHESIS.md` | Synthesis of 10 competitors + 6 user-pain threads + 6 UX sources with FINRLX-specific takeaways. |
| `DOCS/handoff/FINRLX_UX_PHASE_0_REDLINE_BACKLOG.md` | Prioritized backlog (~40 rows) grouped by Phase 1–13, with evidence and gate references. |

No frontend, backend, design, or skill files were modified.

## E. UX Decisions

The four decisions taken at the Phase 0 audit level (each will be
re-validated as the owning phase opens):

1. **Adopt the existing OKLCH token system; do not replace it.** Phase 3
   extends it with semantic `stale / shadow-only / blocked / governance`
   tokens and bumps typography. Source-of-truth ledger stays in
   `frontend/src/app/globals.css` and `frontend/tailwind.config.ts`, with
   `design/handoff-package/handoff-package/styles.css` as the historical
   reference.
2. **Adopt the six-area product architecture from plan §3.** The
   current 16-entry flat sidebar collapses into Home / Research /
   Decisions / Portfolio & Risk / Insights / Ops & Governance + Settings.
   Migration map ships as part of Phase 2 deliverables.
3. **Treat the existing safety skills as load-bearing — extend, do not
   refactor.** The five Phase-1 redesign skills layer *on top* of the six
   existing skills, not in place of them.
4. **Reuse `RecommendationCard`, `ConfidenceBlock`, `WeightsTable`,
   `WarningsBlock`, `DataFreshnessBadge`, `StatusBadge`, `SourceBadge`,
   and the feedback/PageLoading/PageError/PageEmpty primitives.** They
   already encode the right principles (decomposed confidence,
   source-grounded recommendation, freshness chips, structured empty
   states). The redesign refines them; it does not replace them.

## F. Data/API Contract Notes

No API contract was changed. The backend exposes 44 routers (see
`backend/app/api/router.py`) — none were modified. The frontend continues
to read `/api/v1/flags` once at boot via `FeatureFlagsContext` and to
honor the fail-closed default.

API surface the redesign will lean on, by phase:

- Phase 5 Home: `/overview`, `/regime`, `/ops`, `/recommendations/current`,
  `/paper/current`, `/recommendations/opportunities` (or equivalent),
  `/assistant/preview`.
- Phase 6 Research (new): `/universes`, `/engines`, `/pricechart`,
  `/news` (sub-query), `/assistant`.
- Phase 7 Decisions: `/recommendations/current`, `/recommendations/{id}`,
  `/decision/stages`, `/evidence`, `/disagreement`, `/comparison`,
  `/replay`, `/actions/*`.
- Phase 8 Portfolio & Risk: `/paper/current`, `/paper/performance`,
  `/risk/current`, `/scenario`.
- Phase 9 Insights: `/news`, `/regime`, plus filters by ticker / portfolio.
- Phase 10 Ops & Governance: `/ops`, `/ops_jobs`, `/ops_users`,
  `/policies`, `/policies/breaches`, `/policies/history`,
  `/integrations`, `/integrations/health`, `/pipeline`, `/publication`,
  `/ml-ops`, `/model-validation`, `/model-promotion`, `/rl-*`.

## G. Safety/Governance Notes

- The `DisclaimerBanner` lives in `AppShell` and is rendered on every
  authenticated and unauthenticated page (`frontend/src/components/legal/DisclaimerBanner.tsx`,
  `AppShell.tsx:100`). Phase 4 must not remove this when redesigning the
  shell.
- A `DisclaimerModal` runs at the top of `AppShell` for first-load
  consent flow. Phase 4 must preserve it.
- Feature flags fail closed — no surface should be rendered while flags
  load (`FeatureFlagsContext.tsx:44–56`). Phases 2, 4, 10 must preserve
  this.
- Forbidden verbs (`buy`, `sell`, `trade`, `execute`, `broker`,
  `guaranteed`, `risk-free`, `beat the market`) must not appear in
  product copy. None observed in the pages inspected during Phase 0. The
  `fintech-disclaimer-and-marketing-guard` skill encodes this and is the
  authoritative lint rule.
- AI assistant surfaces (Home preview + future `/assistant` UI) must
  ship guided prompts, source chips, and limitations — encoded in the
  Phase-1 `finrlx-ai-ux-governance` skill (to be created).

## H. Testing Evidence

Phase 0 ran no automated tests because the deliverables are
documentation-only. Commands the plan recommends for higher-phase gates
were **not** executed in this phase:

| Command | Run in Phase 0? | Reason |
|---|---|---|
| `npm run typecheck` | No | No code changed. |
| `npm run test:ci` | No | No code changed. |
| `npm run build` | No | No code changed. |
| `npm run e2e:ci` | No | No code changed; Playwright env not validated. |
| `python -m pytest -q` | No | No backend code changed. |
| `rg "<forbidden verb list>"` | No | No copy changed. Will run at Phase 3 / Phase 12 gates per plan §5. |

The first phase that needs the typecheck/test/build/e2e chain is Phase 3
(Design system foundation). The Phase-1 skill
`finrlx-visual-qa-accessibility-gate` will codify the exact command
sequence and pass/fail criteria.

## I. Screenshot Evidence

None captured in Phase 0 — no UI changes were made. Screenshot matrix
(390 / 768 / 1024 / 1440 px, dark + light) becomes mandatory from Phase 3
onward, per plan §5 Phase 12.

## J. Known Limitations and Honest Gaps

1. **External URLs not fetched live.** The benchmark synthesis used the
   master plan's curated list, not fresh HTTP fetches. Phase 1 should
   re-fetch and diff.
2. **No automated audit.** The route inventory was assembled from
   `frontend/src/app/**/page.tsx` globbing — there is no static-analysis
   check that catches a `page.tsx` I missed. The 25-route count is
   internally consistent but should be verified by a `find frontend/src/app -name 'page.tsx'` rerun at the top of Phase 2.
3. **Backend deep dives skipped.** Phase 0 read the router registry only.
   I did not read each endpoint's request/response schema. Phases that
   touch a specific endpoint (e.g. Phase 6 Research → `/pricechart`)
   should read that endpoint at phase start.
4. **Mock-data risk.** I observed at least one place (`decision/page.tsx:221–238`) where the risk-overlay gauge values are hardcoded inside the page rather than fed from `stages.risk_overlay`. Other pages may have similar pockets — Phase 3 and Phase 7 should grep for hardcoded numeric arrays and flag them.
5. **Stale handoff docs.** There are ~70 prior `DOCS/handoff/PHASE_*.md`
   reports, plus duplicated `_phase8i_review_package/` and
   `_phase8i2_review_package/` review snapshots. Phase 0 did not audit
   their drift against the current code; the redesign program should not
   rely on them as a source of truth for the *current* product.
6. **Design folder double-nesting.** `design/handoff-package/` contains a
   nested `handoff-package/` folder with the original QuantPipeline
   handoff. Both levels carry HTML/JSX files. Phase 3 should consolidate.
7. **No live Railway verification.** The hardcoded Railway URL
   (`https://backend-production-aab8.up.railway.app`) appears as the
   fallback `NEXT_PUBLIC_API_BASE_URL`. Whether that environment is
   currently healthy is unverified in Phase 0; Phase 13 owns production
   verification.

## K. Recommendation for Phase 1

**Proceed to Phase 1 with this scope, in this order:**

1. **Refresh external benchmarks** (≤ 2 hours). Use `WebFetch` to confirm
   the 10 + 6 sources still reflect what the synthesis file claims; diff
   into the synthesis doc if anything material has changed since the
   master plan was authored.
2. **Audit and decide on the Anthropic `frontend-design` skill and the
   Vercel `web-design-guidelines` skill.** Read each `SKILL.md` content
   before any install. Plan §1.4-B explicitly forbids blind remote
   install. Outcome should be one of: (a) install via `npx skills add …`,
   (b) mirror the safe subset locally under
   `.claude/skills/anthropic-frontend-design-mirror/SKILL.md` and
   `.claude/skills/vercel-web-design-guidelines-mirror/SKILL.md`, or (c)
   document why we declined.
3. **Create the five FINRLX redesign skills** at the exact paths the
   master plan §1.5 requires:
   - `.claude/skills/finrlx-ux-redesign-director/SKILL.md`
   - `.claude/skills/finrlx-fintech-dashboard-patterns/SKILL.md`
   - `.claude/skills/finrlx-ai-ux-governance/SKILL.md`
   - `.claude/skills/finrlx-visual-qa-accessibility-gate/SKILL.md`
   - `.claude/skills/finrlx-handoff-evidence-packager/SKILL.md`

   Use `finrlx-home-command-center/SKILL.md` as the structural template
   (clear `name` / `description` / `type: project` frontmatter, scoped
   activation, and concrete rules — not aspirational copy).
4. **Author `DOCS/FINRLX_UX_UI_REDESIGN_PLAYBOOK.md`** capturing: the six
   product areas, the canonical design vocabulary, forbidden
   language/patterns, and the cross-cutting takeaways §4 of the
   benchmark synthesis. Reference it from every Phase-1+ phase report.
5. **Optional quick wins safe to bundle into Phase 1.**
   (a) Normalize `source: project` → `type: project` in the two existing
   skills that still use the older key (QW-2 in the redline backlog).
   (b) Add a pre-push grep for forbidden verbs if it lands cheaply
   (Q-3 in the redline backlog) — otherwise defer to Phase 12.

**Phase 1 must not start any product UI work.** Phase 1 ends with skills
+ playbook only. The IA work that touches navigation begins in Phase 2.

## L. Phase 0 Gate Compliance (plan §5 Phase 0 Gate 0)

| Gate 0 requirement | Status | Evidence |
|---|---|---|
| All major routes listed | Met | 25 routes in `FINRLX_UX_PHASE_0_PAGE_INVENTORY.csv`. |
| Design folder and handoff package inspected | Met | `design/handoff-package/**` and `design/handoff-package/handoff-package/**` read; HANDOFF.md summarized in synthesis §4. |
| Existing skills inventoried honestly | Met | `FINRLX_UX_PHASE_0_SKILL_INVENTORY.md` lists 6 present + 5 plan-required-missing + 4 external candidates. |
| ≥ 8 competitor/reference products summarized | Met (10) | `FINRLX_UX_PHASE_0_BENCHMARK_SYNTHESIS.md` §1. |
| ≥ 5 user-pain sources summarized | Met (6) | Same file §2. |
| Report identifies keep / merge / remove / redesign / defer | Met | `FINRLX_UX_PHASE_0_REDLINE_BACKLOG.md` disposition column + summary section. |

**Gate 0 clears. Proceed to Phase 1 per recommendation §K.**

---

## M. Review package command

The operator may run this from the project root in PowerShell to package
the Phase 0 deliverables (and the rest of the repo, excluding heavy
artifacts) for external review:

```powershell
$ErrorActionPreference = "Stop"

$root = Get-Location
$stage = Join-Path $root "_review_package_ux_phase0"
$zip = Join-Path $root "FINRLX_ux_phase0_review_package.zip"

if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
if (Test-Path $zip) { Remove-Item $zip -Force }

New-Item -ItemType Directory -Path $stage | Out-Null

$dirs = @(
    "frontend",
    "backend",
    "DOCS",
    "docs",
    "design",
    ".claude",
    "tests",
    "scripts",
    "infra"
)

foreach ($d in $dirs) {
    if (Test-Path $d) {
        robocopy $d (Join-Path $stage $d) /E `
            /XD node_modules .next dist build coverage .git .venv venv __pycache__ .pytest_cache .mypy_cache .idea .vscode tmp temp backups research `
            /XF *.log *.zip *.tar *.gz *.rar *.7z *.pyc *.sqlite *.sqlite3 *.db *.parquet *.pkl *.joblib `
            | Out-Null
    }
}

$files = @(
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "next.config.js",
    "next.config.mjs",
    "tailwind.config.js",
    "tailwind.config.ts",
    "tsconfig.json",
    "README.md",
    "pyproject.toml",
    "pytest.ini",
    "alembic.ini",
    "docker-compose.yml",
    "Dockerfile",
    ".env.example"
)

foreach ($f in $files) {
    if (Test-Path $f) {
        Copy-Item $f (Join-Path $stage $f) -Force
    }
}

$meta = Join-Path $stage "_review_metadata"
New-Item -ItemType Directory -Path $meta | Out-Null

git status --short | Out-File (Join-Path $meta "git_status_short.txt") -Encoding utf8
git diff --name-only | Out-File (Join-Path $meta "git_diff_name_only.txt") -Encoding utf8
git diff --stat | Out-File (Join-Path $meta "git_diff_stat.txt") -Encoding utf8
git rev-parse --short HEAD | Out-File (Join-Path $meta "git_head_short.txt") -Encoding utf8

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip -Force

Write-Host ""
Write-Host "Created Phase 0 review package:"
Write-Host $zip
```

The five Phase 0 deliverables live under `DOCS/handoff/`, so the
robocopy of the `DOCS` directory captures them automatically.
