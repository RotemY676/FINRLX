# QuantPipeline cleaned package

This package reorganizes the current document set into a canonical sequence for documents 01–09 and moves the technology recommendation out of the main numbering into Appendix A1.

## Canonical order

| Slot | File | PDF pages after cleanup/render |
|---|---|---:|
| 01 | 01_FINRLX_Technology_Survey_and_Deep_Research_Report.docx | 24 |
| 02 | 02_Market_Survey_QuantPipeline.docx | 29 |
| 03 | 03_FINRLX_Solution_Landscape_Implementation_Needs_and_Maximum_Capability_Utilization_Report.docx | 27 |
| 04 | 04_Dashboard_Market_Survey_and_Advanced_UX_UI_Research_for_the_Planned_Site_v2.docx | 9 |
| 05 | 05_CDR_Concept_Definition_Report_v2.docx | 12 |
| 06 | 06_UX_Appendix_Detailed_Site_Dashboard_and_Admin_Experience.docx | 9 |
| 07 | 07_Competitor_Benchmark_Detailed_Comparison_Matrix_and_Differentiation_Strategy.docx | 8 |
| 08 | 08_PRD_QuantPipeline.docx | 12 |
| 09 | 09_Functional_Requirements_Specification.docx | 11 |
| A1 | A1_Technology_Recommendation_for_the_Site_and_Service_with_Mobile_and_iPhone_Path.docx | 9 |

## Cleanup actions applied

- Removed repeated boilerplate paragraphs that appeared verbatim many times inside the same document.
- Removed embedded internal citation tokens such as `cite...` and `filecite...` that should not remain in deliverable DOCX files.
- Renamed the technology recommendation from `08_...` to `A1_...` and updated its title page to avoid collision with the PRD.
- Re-rendered the cleaned documents to PDF for QA.

## Important note

Several documents became substantially shorter after duplicate-paragraph cleanup. That is expected: the source files contained many repeated blocks that inflated page counts without adding new content.

## Contents

- `DOCS/` cleaned DOCX deliverables
- `PDFS_QA/` rendered PDFs for internal verification
- `ASSETS/` image assets preserved from the original package
- `HANDOFF/` handoff notes preserved from the original package
