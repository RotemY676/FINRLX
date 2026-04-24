# INITIAL PROJECT BASELINE

**Created:** 2026-04-24
**Purpose:** Truthful inventory of documents, project interpretation, and implementation plan based on actual file inspection.

---

## A. Package Verification

### Root Project Structure

| Folder / File | Exists | Contents |
|---|---|---|
| `README.md` | Yes | Basic project description |
| `main.py` | Yes | PyCharm placeholder only - no project code |
| `.gitignore` | Yes | Python, Node, IDE, data exclusions |
| `backend/` | Yes | Scaffold only: FastAPI health endpoint, requirements.txt |
| `backend/app/api/` | Yes | Empty directory |
| `backend/app/core/` | Yes | Empty directory |
| `backend/app/jobs/` | Yes | Empty directory |
| `backend/app/models/` | Yes | Empty directory |
| `backend/app/repositories/` | Yes | Empty directory |
| `backend/app/schemas/` | Yes | Empty directory |
| `backend/app/services/` | Yes | Empty directory |
| `backend/app/utils/` | Yes | Empty directory |
| `backend/migrations/` | Yes | Empty directory |
| `backend/tests/` | Yes | Empty directory |
| `frontend/` | Yes | Scaffold only: bare package.json (no Next.js yet) |
| `frontend/src/` | Yes | Empty subdirectories (app, components, features, pages, services, styles, types) |
| `data/` | Yes | .gitkeep placeholders only (raw, processed, exports, reference) |
| `design/` | Yes | .gitkeep placeholders only (assets, exports, wireframes) |
| `infra/` | Yes | Empty subdirectories (ci, docker, railway) |
| `scripts/` | Yes | Contains project_tree.txt |
| `notebooks/` | Yes | .gitkeep only |
| `logs/` | Yes | .gitkeep only |
| `archive/` | Yes | .gitkeep only |
| `DOCS/` | Yes | See below |

### DOCS Structure

| Folder | Exists | Contents |
|---|---|---|
| `DOCS/source_packages/` | Yes | Master ZIP + extracted 01-24 package |
| `DOCS/source_packages/QuantPipeline_Docs_01_24_Package/` | Yes | Full extracted package |
| `DOCS/working_docs/` | Yes | Empty |
| `DOCS/reference_assets/` | Yes | Empty |
| `DOCS/handoff/` | Yes | This file |
| `DOCS/README_DOCS.md` | Yes | Brief instructions |

### 01-24 Package Internal Structure

| Subfolder | Exists | Contents |
|---|---|---|
| `DOCS/` (inside package) | Yes | 24 DOCX files (01-24) + A1 |
| `PDFS_QA/` | Yes | 24 PDF files (01-24) + A1 |
| `ASSETS/` | Yes | 14 PNG diagrams/wireframes |
| `HANDOFF/` | Yes | 7 files (README_FIRST.txt, HANDOFF_FOR_NEW_CHAT.md, CONTINUE_IN_NEW_CHAT_FIRST.md, QuantPipeline_Baseline_Truth_Table.md, README_PACKAGE_ORDER.md, README_PACKAGE_ORDER_01_15.md, Pasted text files) |

### Additional Package: QuantPipeline_Claude_Design_Pack

Located at project root (also extracted). Contains:
- `01_README/` - MANIFEST.txt, README_CLAUDE_DESIGN_PACK.txt
- `02_CORE_DESIGN_DOCS_DOCX/` - Docs 16-20 as DOCX
- `03_CORE_DESIGN_PDFS/` - Docs 16-20 as PDF
- `04_CONTEXT_DOCS_PDF/` - Docs 04, 05, 06, 07, 08, 09, 10, 15 as PDF
- `05_ASSETS/` - 12 PNG files (wireframes, diagrams, maps)
- `06_PAGE_PREVIEWS/` - Page-by-page PNG previews of docs 16-20 and context docs

### Naming / Numbering Observations

- **Consistent:** Documents 01-24 and A1 follow clean sequential numbering.
- **Duplication:** Docs 16-20 exist in three locations: main package DOCS/, main package PDFS_QA/, and the separate Design Pack. This is intentional (the Design Pack was prepared for UX-focused work).
- **Note:** Doc numbering maps `06` to "UX Appendix" in the main package, but doc `16` is also titled "UX_Appendix" -- these are different documents (06 is "Detailed Site Dashboard and Admin Experience", 16 is the design-pack UX Appendix).
- **ZIP files at root:** Three ZIP files remain at project root (QuantPipeline_Claude_Design_Pack.zip, QuantPipeline_Docs_01_15_Package.zip, QuantPipeline_Docs_16_20_Package.zip). These are source archives and are redundant with the extracted contents.

---

## B. Document Inventory Table

| # | File Name | Exists? | Format | Description | Status |
|---|---|---|---|---|---|
| 01 | FINRLX_Technology_Survey_and_Deep_Research_Report | Yes | DOCX + PDF | FINRL-X framework research, RL/ML landscape for investing | Usable |
| 02 | Market_Survey_QuantPipeline | Yes | DOCX + PDF | Market landscape, competitive positioning | Usable |
| 03 | FINRLX_Solution_Landscape_Implementation_Needs_and_Maximum_Capability_Utilization_Report | Yes | DOCX + PDF | Implementation scope and capability mapping | Usable |
| 04 | Dashboard_Market_Survey_and_Advanced_UX_UI_Research_for_the_Planned_Site_v2 | Yes | DOCX + PDF | Dashboard UX research and patterns | Usable |
| 05 | CDR_Concept_Definition_Report_v2 | Yes | DOCX + PDF | Core concept definition: decision pipeline, layers, recommendation object | Usable - key document |
| 06 | UX_Appendix_Detailed_Site_Dashboard_and_Admin_Experience | Yes | DOCX + PDF | Detailed UX flows for dashboard and admin | Usable |
| 07 | Competitor_Benchmark_Detailed_Comparison_Matrix_and_Differentiation_Strategy | Yes | DOCX + PDF | Competitor analysis and differentiation | Usable |
| 08 | PRD_QuantPipeline | Yes | DOCX + PDF | Product requirements, user stories, MVP scope, release strategy | Usable - key document |
| 09 | Functional_Requirements_Specification | Yes | DOCX + PDF | 30 functional requirements across all modules | Usable - key document |
| 10 | Technical_Architecture_Specification | Yes | DOCX + PDF | System architecture, tech stack, service topology | Usable - key document |
| 11 | Data_Model_and_Schema_Specification | Yes | DOCX + PDF | 7 data domains, entity definitions, relationships | Usable - key document |
| 12 | API_Contract_Specification | Yes | DOCX + PDF | Full API contract with endpoints, schemas, auth | Usable - key document |
| 13 | Validation_Backtesting_and_Paper_Methodology | Yes | DOCX + PDF | Walk-forward backtesting, paper trading, promotion gates | Usable |
| 14 | Governance_Guardrails_and_Ops_Reliability_Specification | Yes | DOCX + PDF | Publication governance, guardrails, SLOs, incidents | Usable |
| 15 | Admin_and_Ops_Specification | Yes | DOCX + PDF | Admin workspace modules, operator workflows | Usable |
| 16 | UX_Appendix | Yes | DOCX + PDF | Information architecture principles, decision-oriented UX | Usable |
| 17 | Information_Architecture_and_User_Flows | Yes | DOCX + PDF | Sitemap, navigation model, 4 primary user flows | Usable |
| 18 | UI_Wireframes_and_Screen_Concepts | Yes | DOCX + PDF | Mid-fidelity wireframes: dashboard, comparison, admin, mobile | Usable |
| 19 | Visual_Design_Direction | Yes | DOCX + PDF | Color palette, typography, chart style, motion, composition | Usable |
| 20 | Component_Specification | Yes | DOCX + PDF | Component system: shell, decision primitives, data display, ops controls | Usable |
| 21 | Claude_Development_Playbook | Yes | DOCX + PDF | Operating principles for Claude-assisted development | Usable |
| 22 | Phase_Prompts_Pack | Yes | DOCX + PDF | 8 reusable prompt patterns (A-H) for different workflows | Usable |
| 23 | Review_Report_Template | Yes | DOCX + PDF | Truth-focused review template (PASS/PARTIAL/FAIL) | Usable |
| 24 | Acceptance_and_QA_Checklist | Yes | DOCX + PDF | Gate-based QA across requirements, arch, data, API, UX, ops | Usable |
| A1 | Technology_Recommendation_for_the_Site_and_Service_with_Mobile_and_iPhone_Path | Yes | DOCX + PDF | Tech stack recommendation: Python + FastAPI backend, Next.js frontend, PWA path | Usable |

**Summary:** All 25 documents (01-24 + A1) are present in both DOCX and PDF formats. The ASSETS folder contains 14 supporting diagrams. The HANDOFF folder contains 7 operational files. The package is complete.

---

## C. Project Interpretation

### Product Goal

QuantPipeline is a **private decision-intelligence platform for medium-term equity investing** (weeks-to-months horizon). It synthesizes multiple evidence sources (news/text analysis, social sentiment, technical indicators, ML models, RL/FINRL-X reasoning) into a unified, weight-centric recommendation object. It is designed for a single sophisticated owner-operator, not a multi-tenant SaaS product.

The key conceptual shift (defined in doc 05 CDR): this is **not** a dashboard of many engines. It is a **modular portfolio decision system** with a canonical pipeline: Data --> Features --> Signals --> Selection --> Allocation --> Timing --> Risk Overlay --> Recommendation Object.

### Target User

A single sophisticated individual investor who:
- Wants institutional-grade decision support for personal portfolio management
- Values transparency, auditability, and explainability over black-box signals
- Needs to understand *why* a recommendation was made and *how confident* the system is
- Operates as both end-user (consuming recommendations) and operator (managing the system)

### Main User Journeys

1. **Daily Review** - Overview --> current recommendation --> confidence/trust assessment --> decision to act or wait
2. **Challenge/Investigation** - Compare engines --> identify disagreements --> explore evidence --> scenario simulation
3. **Replay/Forensics** - Select historical recommendation --> reconstruct stage-by-stage --> understand what drove the outcome
4. **Operator/Publication** - Check system health --> review staged recommendation --> approve/suppress/warn --> publish

### System Layers

| Layer | Purpose |
|---|---|
| Data & Feature Layer | Ingest market data, news, sentiment, technicals; normalize and version features |
| Signals Layer | Run analytical engines (text/NLP, sentiment, technical, ML, RL) to produce scored outputs |
| Selection Layer | Determine which assets to include/exclude from the portfolio |
| Allocation Layer | Assign target weights to selected assets |
| Timing Layer | Determine entry/exit timing and urgency |
| Risk Overlay | Apply portfolio-level risk constraints (position limits, sector caps, cash floors, stress tests) |
| Recommendation Object | Canonical output: target weights + confidence triplet + rationale + warnings |
| Validation Surfaces | Backtest, paper portfolio, replay -- all using the same canonical shapes |
| Admin/Ops | System health, publication governance, audit trail, incident management |

### Major UX/UI Goals

- **Recommendation-first UI**: lead with the decision, not the widgets
- **Trust by exposure**: show confidence decomposition (model, data, operational)
- **Portfolio-aware**: express everything in portfolio-impact terms, not isolated ticker analysis
- **Progressive disclosure**: summary --> evidence --> forensics without clutter
- **Desktop-primary, mobile-credible**: full experience on desktop, focused review on mobile
- **Operationally honest**: show degraded states, stale data, and suppressed outputs explicitly
- **Three-zone shell**: left nav, central canvas, right context pane (collapses on mobile)

### Architecture Implications

- **Backend:** Python (FastAPI) owns analytical core -- NLP, ML, RL, quant pipelines, data engineering, orchestration
- **Frontend:** Next.js/React for dashboard-heavy SPA with responsive design, PWA-ready
- **Data:** PostgreSQL or similar relational DB with append-only history, versioned features, immutable audit trail
- **Jobs:** Scheduled analytical work (ingestion, feature builds, recommendation generation) separate from interactive API
- **API:** RESTful `/api/v1` namespace, role-based access, standardized response envelope, typed errors
- **Deployment:** Containerized (Docker), cloud-first (Railway mentioned in infra scaffold)

### Admin/Ops Implications

- Admin workspace is product-quality, not back-office afterthought
- Publication is a governed state machine (draft --> staged --> approved --> published | suppressed)
- Every mutation produces immutable audit events
- Health monitoring covers: source freshness, feature health, model health, publication health
- Incident severity model (SEV-1 through SEV-4) with automatic suppression rules
- Governance roles (viewer, operator, approver, admin, maintainer) even for single-user first release

---

## D. Build Recommendation

Based on the documents, the correct implementation order is:

### Phase 0: Foundation Setup
- Initialize Next.js project in `frontend/` with TypeScript, Tailwind CSS
- Set up FastAPI project structure in `backend/` with proper config, env handling
- Define design tokens (colors, typography, spacing) from doc 19
- Set up database (PostgreSQL) with Alembic migrations
- Configure Docker compose for local dev (frontend + backend + db)
- Establish CI skeleton in `infra/ci/`

### Phase 1: Data Contracts & Recommendation Schema
- Implement the canonical Recommendation Object schema (Pydantic models + DB tables)
- Define the core data model entities from doc 11: reference data, raw inputs, feature registry, signal outputs, decision pipeline stages, recommendation/publication
- Create API response envelope and error types from doc 12
- Build seed/mock recommendation data for frontend development

### Phase 2: Frontend Shell & Design System
- Implement the three-zone app shell (left nav, canvas, context pane) from doc 17/18
- Build Tier 1 components from doc 20: recommendation card, confidence block, comparison table, alert system
- Implement the Overview screen with mock data
- Establish routing structure matching doc 17 sitemap

### Phase 3: Main Decision Workspace
- Build the primary decision workspace (selection, allocation, timing, risk overlay views)
- Wire to real API endpoints for recommendation retrieval
- Implement engine comparison view
- Build risk workspace

### Phase 4: Backend Pipeline Core
- Implement data ingestion services (market data, news, sentiment sources)
- Build feature engineering pipeline
- Create signal/engine runner framework
- Implement selection --> allocation --> timing --> risk overlay pipeline
- Build recommendation publication service with state machine

### Phase 5: Replay & Validation
- Implement replay/forensics (stage-by-stage historical reconstruction)
- Build backtest job runner and result storage
- Implement paper portfolio tracking
- Create validation promotion gates

### Phase 6: Admin & Ops
- Build admin workspace (command center, publication queue, data source control, engine health)
- Implement governance workflows (approve, suppress, warn)
- Build incident and audit trail system
- Add health monitoring and alerting

### Phase 7: Hardening & Mobile
- Responsive/mobile optimization
- PWA configuration
- Performance optimization
- Security hardening
- Deployment pipeline finalization

---

## E. Immediate Next-Step Plan

### Next Phase: Phase 0 + Phase 1 (Foundation + Data Contracts)

This is the critical first implementation phase. Everything downstream depends on getting the data contracts and shell right.

#### Step 0.1: Frontend Initialization
- Initialize Next.js 14+ with App Router in `frontend/`
- Add TypeScript, Tailwind CSS, ESLint
- Install key dependencies: chart library (Recharts or Lightweight Charts), date-fns, zustand or jotai for state
- Create `frontend/src/styles/tokens.ts` with design tokens from doc 19 (colors, typography, spacing)

#### Step 0.2: Backend Initialization
- Structure `backend/app/` with proper module layout matching doc 10
- Add `backend/app/core/config.py` with environment-based settings
- Add `backend/app/core/database.py` with SQLAlchemy async engine
- Set up Alembic with initial migration config
- Create health, version, and readiness endpoints

#### Step 0.3: Infrastructure
- Create `docker-compose.yml` with: frontend (Node), backend (Python/uvicorn), postgres, (optional) redis
- Add `Makefile` or scripts for common dev commands (start, test, migrate, seed)

#### Step 1.1: Core Schema - Recommendation Object
- Define Pydantic schemas in `backend/app/schemas/`:
  - `recommendation.py` - RecommendationSummary, RecommendationDetail, ConfidenceTriplet, WeightEntry
  - `decision.py` - SelectionRun, AllocationResult, TimingResult, RiskOverlayResult
  - `common.py` - ResponseEnvelope, TypedError, FreshnessState, PaginationCursor
- Define SQLAlchemy models in `backend/app/models/`:
  - `recommendation.py` - recommendations, recommendation_weights, recommendation_confidence
  - `decision_pipeline.py` - selection_runs, allocation_results, timing_results, risk_overlays
  - `reference.py` - assets, universes, benchmarks

#### Step 1.2: Core API Endpoints (Read-Only First)
- `GET /api/v1/overview` - current recommendation summary + health
- `GET /api/v1/recommendations/current` - full current recommendation
- `GET /api/v1/recommendations/{id}` - historical recommendation detail
- `GET /api/v1/health` - system health summary

#### Step 1.3: Seed Data
- Create a seed script that generates realistic mock recommendations
- Include multiple historical recommendations for replay testing
- Populate reference data (sample assets, universe)

#### Step 1.4: Frontend Shell (Parallel with Backend)
- Build app shell layout: sidebar nav + main canvas + collapsible context pane
- Implement routing: Overview, Decision, Comparison, Replay, Backtests, Paper, Admin
- Build empty page shells for each route
- Implement RecommendationCard component with mock data
- Implement ConfidenceBlock component
- Wire Overview page to backend `/api/v1/overview`

#### Acceptance Criteria for This Phase
- [ ] `docker compose up` starts frontend + backend + database
- [ ] Backend serves `/api/v1/overview` with seed recommendation data
- [ ] Frontend renders app shell with working navigation
- [ ] Overview page displays current recommendation from API
- [ ] RecommendationCard shows: asset weights, confidence triplet, freshness
- [ ] All schemas match doc 11 entity names and doc 12 API contract names
- [ ] Design tokens match doc 19 color palette and typography
- [ ] No placeholder or fake "implemented" claims -- only what actually works

---

## Appendix: Current Codebase State

The existing repository is a **bare scaffold** with no functional code:
- `main.py` at root is a PyCharm template placeholder
- `backend/app/main.py` has only a `/health` endpoint returning `{'status': 'ok'}`
- `backend/requirements.txt` lists dependencies but nothing is installed or used
- `frontend/package.json` is a bare stub (no Next.js, no dependencies)
- All `backend/app/` subdirectories are empty
- All `frontend/src/` subdirectories are empty
- No database, no migrations, no tests, no Docker config
- No application code exists anywhere in the repository

**Bottom line:** Implementation starts from zero. The documentation package is complete and high-quality. The scaffold structure is reasonable and can be used as-is.
