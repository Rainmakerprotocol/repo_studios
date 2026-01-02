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
updated_at: 2026-01-02
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
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md`
  — 72 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_standards_integrity_roster.md`
  — 66 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`
  — 44 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  — 25 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_5_1_implementation_plan.md`
  — 14 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_4_1_implementation_plan.md`
  — 13 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_healthview_roster_template.md`
  — 11 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_monkey_patch_oversight_roster.md`
  — 11 unchecked
* `.repo_studios/docs/pipeline/pipeline_templates/tier2_pipeline_howto.md` — 10 unchecked

### Sample Outstanding Tasks

* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  L96 — Stage 3.1 Fault Diagnostics Overview — Implementation Plan > Phase 1: Path & Constants
  Update > 1.2 Update Remaining Hardcoded Paths: `collect_faulthandler_reports.py` line 49:
  `DEFAULT_RUNS_RELATIVE` still uses `command_center`
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  L97 — Stage 3.1 Fault Diagnostics Overview — Implementation Plan > Phase 1: Path & Constants
  Update > 1.2 Update Remaining Hardcoded Paths: `generate_fault_artifacts.py`: Verify
  `RAWVIEW_ROOT` and discovery paths
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  L98 — Stage 3.1 Fault Diagnostics Overview — Implementation Plan > Phase 1: Path & Constants
  Update > 1.2 Update Remaining Hardcoded Paths: `summarize_fault_diagnostics_overview.py`: Verify
  input discovery paths
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  L99 — Stage 3.1 Fault Diagnostics Overview — Implementation Plan > Phase 1: Path & Constants
  Update > 1.2 Update Remaining Hardcoded Paths: `run_fault_diagnostics_overview.py`: Verify all CLI
  argument defaults
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  L126 — Stage 3.1 Fault Diagnostics Overview — Implementation Plan > Phase 2: Discovery Logic
  Update > 2.1 Timestamp-Based Discovery (No Pointer Files): `collect_faulthandler_reports.py`:
  `_find_latest_run()` — verify uses directory sorting
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  L127 — Stage 3.1 Fault Diagnostics Overview — Implementation Plan > Phase 2: Discovery Logic
  Update > 2.1 Timestamp-Based Discovery (No Pointer Files): `generate_fault_artifacts.py`:
  `_find_latest_outdir()` — verify uses directory sorting
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  L128 — Stage 3.1 Fault Diagnostics Overview — Implementation Plan > Phase 2: Discovery Logic
  Update > 2.1 Timestamp-Based Discovery (No Pointer Files):
  `summarize_fault_diagnostics_overview.py`: Discovery of consumer bundles
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  L129 — Stage 3.1 Fault Diagnostics Overview — Implementation Plan > Phase 2: Discovery Logic
  Update > 2.1 Timestamp-Based Discovery (No Pointer Files): `run_fault_diagnostics_overview.py`:
  Discovery of upstream artifacts
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  L227 — Stage 3.1 Fault Diagnostics Overview — Implementation Plan > Phase 4: Docstring Updates
  (PEP 287 reStructuredText) > 4.1 Module Docstrings: Cross-references using ``:doc:`` and ``:ref:``
  roles
* `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage_3_1_implementation_plan.md`
  L380 — Stage 3.1 Fault Diagnostics Overview — Implementation Plan > Phase 5: Test Updates > 5.2
  Test Cases to Add/Update: Verify output paths match HOP contract

## Signals & Telemetry

* Total unchecked tasks: 361.
* Files containing unchecked tasks: 17.

### Unchecked Tasks by H1

| H1 | Unchecked |
| --- | --- |
| Tier-2 Roster — Stage 7 Running the Complete Suite | 77 |
| Tier-2 Roster — Stage 11.1 Available Scripts (Holding Area) | 72 |
| Tier-2 Roster — Stage 6.1 Standards Integrity | 66 |
| HealthView Orchestration Pipeline | 44 |
| Stage 3.1 Fault Diagnostics Overview — Implementation Plan | 25 |
| Stage 5.1 Implementation Plan: Monkey Patch Oversight | 14 |
| Stage 4.1 Implementation Plan: Dependency & Import Hygiene | 13 |
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

* 2026-01-02 — Report regenerated.
