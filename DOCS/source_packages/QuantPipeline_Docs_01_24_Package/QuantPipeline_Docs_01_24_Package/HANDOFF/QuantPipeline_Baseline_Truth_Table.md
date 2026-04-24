# QuantPipeline Baseline Truth Table

Built from direct inspection of the uploaded ZIP contents, DOCX files, and rendered PDFs.

| Slot | File found | Intended role | Status | Pages | Notes |
|---|---|---|---|---:|---|
| 01 | 01_FINRLX_Technology_Survey_and_Deep_Research_Report.docx | Research foundation | Verified | 27 | Real doc; rendered; structurally rich; noticeable repeated prose in later sections |
| 02 | 02_Market_Survey_QuantPipeline.docx | Market survey | Verified | 29 | Real doc; rendered; stronger lexical variety than several others; still some repeated blocks |
| 03 | 03_FINRLX_Solution_Landscape_Implementation_Needs_and_Maximum_Capability_Utilization_Report.docx | Solution landscape | Verified | 27 | Real doc; rendered; good architecture coverage; high repetition risk |
| 04 | 04_Dashboard_Market_Survey_and_Advanced_UX_UI_Research_for_the_Planned_Site_v2.docx | Dashboard UX/UI research | Verified | 30 | Real doc; rendered; strong coverage; very high repeated wording risk |
| 05 | 05_CDR_Concept_Definition_Report_v2.docx | Concept Definition Report | Verified | 54 | Real doc; rendered; deep and broad; strongest scope but heaviest repetition/filler risk |
| 06 | 06_UX_Appendix_Detailed_Site_Dashboard_and_Admin_Experience.docx | UX appendix | Verified | 29 | Real doc; rendered; useful screen/system coverage; repetition risk present |
| 07 | 07_Competitor_Benchmark_Detailed_Comparison_Matrix_and_Differentiation_Strategy.docx | Competitor benchmark | Verified | 31 | Real doc; rendered; solid competitor structure; repetition risk present |
| SUP | 08_Technology_Recommendation_for_the_Site_and_Service_with_Mobile_and_iPhone_Path.docx | Supporting research / technology recommendation | Verified but misnumbered | 28 | Real doc; rendered; should not keep duplicate 08 if 08 is reserved for PRD |
| 08 | 08_PRD_QuantPipeline.docx | PRD | Verified but needs cleanup | 26 | Real doc; rendered; substantial; repeated/filler-style prose especially late |
| 09 | 09_Functional_Requirements_Specification.docx | Functional Requirements Specification | Verified but needs cleanup | 32 | Real doc; rendered; richer than handoff claimed; repeated prose especially late |
| 10 | — | Technical Architecture Specification | Missing | — | Create after 08/09 cleanup and numbering lock |
| 11 | — | Data Model and Schema Specification | Missing | — | Not found in ZIP |
| 12 | — | API Contract Specification | Missing | — | Not found in ZIP |
| 13 | — | Validation / Backtesting / Paper Methodology | Missing | — | Not found in ZIP |
| 14 | — | Governance / Guardrails / Ops Reliability Specification | Missing | — | Not found in ZIP |
| 15 | — | Admin and Ops Specification | Missing | — | Not found in ZIP |

## Canonical numbering recommendation

To avoid numbering drift, keep the user-requested engineering package as the canonical sequence:

- 08 = PRD
- 09 = Functional Requirements Specification
- 10 = Technical Architecture Specification
- 11 = Data Model and Schema Specification
- 12 = API Contract Specification
- 13 = Validation / Backtesting / Paper Methodology
- 14 = Governance / Guardrails / Ops Reliability Specification
- 15 = Admin and Ops Specification

Move the current technology recommendation document out of the numbered master sequence and relabel it as a supporting research appendix (for example `A1_Technology_Recommendation...` or `R8_Technology_Recommendation...`).

## Decision gate

Recommended order before writing 10–15:

1. Lock canonical numbering.
2. Clean repetition/filler from 08 and 09.
3. Only then write 10–15 against the cleaned 08/09 baseline.
