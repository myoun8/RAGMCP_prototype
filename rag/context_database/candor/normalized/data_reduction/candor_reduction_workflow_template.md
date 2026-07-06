---
doc_id: candor_reduction_workflow_template
source_id: CANDOR-002
title: CANDOR Reduction Workflow Template
instrument: CANDOR
workflow_stage: data_reduction
software: Reductus
access_level: internal
status: needs_review
owner: CANDOR team
last_reviewed: 2026-06-16
source_url_or_path: normalized/data_reduction/candor_reduction_workflow_template.md
citation_required: false
---

# CANDOR Reduction Workflow Template

> NEEDS REVIEW: This is a placeholder template, not a confirmed CANDOR-specific procedure. No source document currently specifies the exact required input files or output naming conventions for CANDOR reduction; those details need confirmation from the CANDOR instrument team before this status changes to `current`.

## What is grounded in existing documentation

The general Reductus workflow (see CANDOR-002 / CANDOR-006) supports the following, which applies to CANDOR raw-data reduction:

- Raw data files are accessed directly by URL from the NCNR online data repository — no local download or login is required to start a reduction.
- Reduction templates (recipes) can be built and modified in Reductus's graphical editor, then downloaded and reused or shared by email.
- Reduced reflectivity data is produced as columnar text files (R vs. Q), which is the standard hand-off format for downstream Refl1D modeling (see CANDOR-003).

## What is not yet documented

The following are open questions, not yet answered by any source material in this pack:

- The exact raw input file naming pattern(s) CANDOR produces and that a Reductus template should expect.
- Any CANDOR-specific output file naming convention beyond Reductus's generic columnar text export.
- Whether CANDOR has a pre-built, shareable Reductus template distinct from the generic reflectometry reduction template.

Until these are confirmed, treat this document as a starting point only — verify file naming and required inputs with the CANDOR instrument scientist before relying on this template for an unattended/batch reduction workflow.
