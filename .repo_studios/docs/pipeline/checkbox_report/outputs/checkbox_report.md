---
title: Checkbox Report Summary
tier: tooling
audience:
    - Copilot
    - Repo_Studios
owners:
    - DocumentationOps
status: active
version: 1.0
updated_at: 2025-12-29
tags:
    - checkbox-report
    - repo-todo
related_files:
    - .repo_studios/docs/pipeline/checkbox_report/checkbox_report.py
    - .repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv
    - .repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.md
---

# Checkbox Report

## Goals

* Provide a single discoverable index of unchecked Markdown tasks across the repository.
* Help Copilot and contributors jump directly to unfinished work with heading context.
* Offer a CSV artifact for automation plus a Markdown digest the doc index can surface.

## System Context

* Source of truth: Markdown files beneath `.repo_studios/docs/pipeline`.
* Checklist scope: unchecked boxes only (`- [ ]`). Completed entries are omitted to keep the focus
  on pending work.
* Generated artifacts live in `.repo_studios/docs/pipeline/checkbox_report/outputs` for easy access.
* CSV artifact: `.repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv`.
* Markdown (this file): `.repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.md`.

## Stage Narratives

Top files with the highest number of unfinished items:
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md`
  — 77 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  — 74 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md`
  — 72 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_standards_integrity_roster.md`
  — 66 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_docs_health_overview_roster.md`
  — 65 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_dependency_import_hygiene_roster.md`
  — 55 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_fault_diagnostics_overview_roster.md`
  — 44 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_healthview_roster_template.md`
  — 11 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_monkey_patch_oversight_roster.md`
  — 11 unchecked
* `.repo_studios/docs/pipeline/pipeline_templates/tier2_pipeline_howto.md` — 10 unchecked

### Sample Outstanding Tasks

* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  L620 — HealthView Orchestration Pipeline > 5. Stage 2 – Documentation Quality > 5.1 Stage 2.1:
  Docs Health Overview: verify_docs_integrity.py — pending until Tier-2 DONE is checked. See: Tier-2
  record
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  L621 — HealthView Orchestration Pipeline > 5. Stage 2 – Documentation Quality > 5.1 Stage 2.1:
  Docs Health Overview: validate_metrics_anchor_stubs.py — pending until Tier-2 DONE is checked.
  See: Tier-2 record
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  L622 — HealthView Orchestration Pipeline > 5. Stage 2 – Documentation Quality > 5.1 Stage 2.1:
  Docs Health Overview: generate_code_doc_churn_report.py — pending until Tier-2 DONE is checked.
  See: Tier-2 record
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  L623 — HealthView Orchestration Pipeline > 5. Stage 2 – Documentation Quality > 5.1 Stage 2.1:
  Docs Health Overview: generate_undocumented_logic_report.py — pending until Tier-2 DONE is
  checked. See: Tier-2 record
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  L624 — HealthView Orchestration Pipeline > 5. Stage 2 – Documentation Quality > 5.1 Stage 2.1:
  Docs Health Overview: aggregate_docs_health_signals.py — pending until Tier-2 DONE is checked.
  See: Tier-2 record
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  L625 — HealthView Orchestration Pipeline > 5. Stage 2 – Documentation Quality > 5.1 Stage 2.1:
  Docs Health Overview: run_docs_health_overview.py — pending until Tier-2 DONE is checked. See:
  Tier-2 record
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  L631 — HealthView Orchestration Pipeline > 5. Stage 2 – Documentation Quality > 5.1 Stage 2.1:
  Docs Health Overview: Base package complete (`manifest.json`, `summary.md`, `telemetry.json`).
  See: Stop-gates
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  L632 — HealthView Orchestration Pipeline > 5. Stage 2 – Documentation Quality > 5.1 Stage 2.1:
  Docs Health Overview: No pointer artifacts (`latest_*` / `current_*`). See: Stop-gates
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  L633 — HealthView Orchestration Pipeline > 5. Stage 2 – Documentation Quality > 5.1 Stage 2.1:
  Docs Health Overview: Output root aligned to HOP contract
  (`.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`).
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  L635 — HealthView Orchestration Pipeline > 5. Stage 2 – Documentation Quality > 5.1 Stage 2.1:
  Docs Health Overview: Tier-3 eligible (Stage 2.1 Tier-2 depth captured; ready for Tier-3
  extraction). See:

## Signals & Telemetry

* Total unchecked tasks: 497.
* Files containing unchecked tasks: 14.

### Unchecked Tasks by H1

| H1 | Unchecked |
| --- | --- |
| Tier-2 Roster — Stage 7 Running the Complete Suite | 77 |
| HealthView Orchestration Pipeline | 74 |
| Tier-2 Roster — Stage 11.1 Available Scripts (Holding Area) | 72 |
| Tier-2 Roster — Stage 6.1 Standards Integrity | 66 |
| Tier-2 Roster — Stage 2.1 Docs Health Overview | 65 |
| Tier-2 Roster — Stage 4.1 Dependency & Import Hygiene | 55 |
| Tier-2 Roster — Stage 3.1 Fault Diagnostics Overview | 44 |
| Tier-2 Roster Template — <STAGE_ID> <STAGE_NAME> | 11 |
| Tier-2 Roster — Stage 5.1 Monkey Patch Oversight | 11 |
| How-To — Authoring Tier-2 Pipeline Documents | 10 |

## Maintenance Playbook

* Run `python .repo_studios/docs/pipeline/checkbox_report/checkbox_report.py --verbose` after
  checklist edits under `.repo_studios/docs/pipeline`.
* Commit `.repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv` and
  `.repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.md` together so doc-index
  consumers see the refresh.
* Use the CSV artifact as the source of truth for automation; this Markdown is optimized for
  doc-index discovery.

## Update Log

* 2025-12-29 — Report regenerated.
