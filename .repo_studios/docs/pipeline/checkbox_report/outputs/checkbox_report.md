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
updated_at: 2025-12-11
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

* Source of truth: Markdown files beneath `.repo_studios`.
* Checklist scope: unchecked boxes only (`- [ ]`). Completed entries are omitted to keep the focus
  on pending work.
* Generated artifacts live in `.repo_studios/docs/pipeline/checkbox_report/outputs` for easy access.
* CSV artifact: `.repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv`.
* Markdown (this file): `.repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.md`.

## Stage Narratives

Top files with the highest number of unfinished items:
* `.repo_studios/command_center/docs/phase_4/PR_CHECKLIST_TEMPLATE.md` — 33 unchecked
* `.repo_studios/command_center/docs/manual_extraction_checklist.md` — 29 unchecked
* `.repo_studios/docs/templates/integration_alignment_template.md` — 27 unchecked
* `.repo_studios/command_center/docs/db_integration_template.md` — 26 unchecked
* `.repo_studios/docs/automation/function_inventory_integration_plan.md` — 26 unchecked
* `.repo_studios/command_center/docs/db_integration_test_execution_telemetry.md` — 25 unchecked
* `.repo_studios/command_center/docs/naming_conventions.md` — 22 unchecked
* `.repo_studios/command_center/docs/groundwork_and_db_alignment.md` — 21 unchecked
* `.repo_studios/command_center/checklists/2025-10-24.md` — 20 unchecked
* `.repo_studios/command_center/docs/db_integration_guide.md` — 19 unchecked

### Sample Outstanding Tasks

* `.repo_studios/agent_notes/meta/phase1_foundation_review_2025-10-18_0138.md` L30 — Phase 1
  Foundation Review > Follow-up: Migrate remaining legacy standards into `docs/standards/global/` or
  `docs/standards/project/` and assign owners.
* `.repo_studios/agent_notes/meta/phase1_foundation_review_2025-10-18_0138.md` L31 — Phase 1
  Foundation Review > Follow-up: Define CI health checks that consume
  `reports/producer_reports/render_inventory_views/latest_*.json` artifacts.
* `.repo_studios/agent_notes/meta/phase1_foundation_review_2025-10-18_0138.md` L32 — Phase 1
  Foundation Review > Follow-up: Expand secondary views (dependency graphs, trend snapshots) once
  consumers are identified.
* `.repo_studios/command_center/README.md` L169 — Library Integration Protocol > Onboarding
  Checklist: Latest duplicate reports mirrored into
  `.repo_studios/command_center/reports/<slug>_duplicate_scan/`.
* `.repo_studios/command_center/README.md` L170 — Library Integration Protocol > Onboarding
  Checklist: Checklist updated with priority targets and assigned owners.
* `.repo_studios/command_center/README.md` L171 — Library Integration Protocol > Onboarding
  Checklist: Target library paths confirmed against naming conventions.
* `.repo_studios/command_center/README.md` L172 — Library Integration Protocol > Onboarding
  Checklist: Tests identified/apportioned for library and producer impacts.
* `.repo_studios/command_center/README.md` L173 — Library Integration Protocol > Onboarding
  Checklist: Rollback plan documented (backup locations, restore steps).
* `.repo_studios/command_center/checklists/2025-10-24.md` L56 — Library Integration Alignment Plan >
  Phase 3 – Manual Extraction Validation: **Confirm live duplicates** for `_slugify_relative`,
  `build_paths`, and `build_options` using the 2025-10-27 Command Center index *(Developer → provide
  folder-level index snapshots; Agent → verify occurrences).*
* `.repo_studios/command_center/checklists/2025-10-24.md` L57 — Library Integration Alignment Plan >
  Phase 3 – Manual Extraction Validation: **Establish priority order** for first extractions
  (candidate sequence updated to `_slugify_relative`, `_copy_latest`, `write_artifacts`,
  `build_paths`, `configure_logging`) *(Joint → finalize order in Decisions section).*

## Signals & Telemetry

* Total unchecked tasks: 493.
* Files containing unchecked tasks: 59.

### Unchecked Tasks by H1

| H1 | Unchecked |
| --- | --- |
| Monkey Patch Scan Report | 60 |
| Automation Run Pull Request Checklist | 33 |
| Manual Extraction Checklist (Repo Studios Command Center) | 29 |
| Library Integration Alignment Template | 27 |
| Database Integration Documentation Template | 26 |
| Function Inventory Integration Plan | 26 |
| Database Integration Documentation | 25 |
| .repo_studios Library Naming Training Guide | 22 |
| Groundwork and Database Alignment Plan | 21 |
| Library Integration Alignment Plan | 20 |

## Maintenance Playbook

* Run `python .repo_studios/docs/pipeline/checkbox_report/checkbox_report.py --verbose` after
  checklist edits under `.repo_studios`.
* Commit `.repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv` and
  `.repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.md` together so doc-index
  consumers see the refresh.
* Use the CSV artifact as the source of truth for automation; this Markdown is optimized for
  doc-index discovery.

## Update Log

* 2025-12-11 — Report regenerated.
