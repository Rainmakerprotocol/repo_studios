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
updated_at: 2025-12-19
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
* `.repo_studios/docs/pipeline/pipeline_templates/tier2_pipeline_howto.md` — 10 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md`
  — 8 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/hop_implementation.md` — 5
  unchecked
* `.repo_studios/docs/pipeline/pipeline_templates/tier2_pipeline_template.md` — 4 unchecked
* `.repo_studios/docs/pipeline/pipeline_templates/tier3_pipeline_template.md` — 3 unchecked

### Sample Outstanding Tasks

* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/hop_implementation.md` L180 —
  HealthView HOP Implementation Plan > 3. Stage Narratives (Workstreams) > 3.C Workstream C —
  Extract Stage 1.1 Definition Into Tier-2 Vertical: Create the Stage 1.1 Tier-2 doc using the
  Tier-2 template, including:
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/hop_implementation.md` L195 —
  HealthView HOP Implementation Plan > 3. Stage Narratives (Workstreams) > 3.D Workstream D — Seed
  Remaining Tier-2 Verticals (Tier-1 Order): Create one Tier-2 stub per stage with consistent
  headings, stop-gates, and update log.
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/hop_implementation.md` L196 —
  HealthView HOP Implementation Plan > 3. Stage Narratives (Workstreams) > 3.D Workstream D — Seed
  Remaining Tier-2 Verticals (Tier-1 Order): Add explicit TODO checklists for “inventory chain”,
  “confirm output root”, and “validate gates”.
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/hop_implementation.md` L206 —
  HealthView HOP Implementation Plan > 3. Stage Narratives (Workstreams) > 3.E Workstream E —
  Convert Tier-2 Docs → Execution Checklists (Later Code Phase): Define the per-script “definition
  of done” checklist used by every migration.
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/hop_implementation.md` L207 —
  HealthView HOP Implementation Plan > 3. Stage Narratives (Workstreams) > 3.E Workstream E —
  Convert Tier-2 Docs → Execution Checklists (Later Code Phase): Add “doc-index + regression suite”
  evidence requirements per completed script.
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md`
  L215 — Stage 1.1 Roster — Test Execution Telemetry > 3. Stage Narrative — Stage 1.1 Test Execution
  Telemetry > 3.2 Stop-Gates and Implementation Checklists: Confirm the canonical `<class>/<topic>`
  tokens for Stage 1.1 under
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md`
  L217 — Stage 1.1 Roster — Test Execution Telemetry > 3. Stage Narrative — Stage 1.1 Test Execution
  Telemetry > 3.2 Stop-Gates and Implementation Checklists: Confirm the canonical `<timestamp>`
  formatting expectation and record it here (do not assume
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md`
  L222 — Stage 1.1 Roster — Test Execution Telemetry > 3. Stage Narrative — Stage 1.1 Test Execution
  Telemetry > 3.2 Stop-Gates and Implementation Checklists: Output root migrated to
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md`
  L223 — Stage 1.1 Roster — Test Execution Telemetry > 3. Stage Narrative — Stage 1.1 Test Execution
  Telemetry > 3.2 Stop-Gates and Implementation Checklists: Artifact invariant enforced: exactly
  `manifest.json`, `summary.md`, `telemetry.json`.
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md`
  L224 — Stage 1.1 Roster — Test Execution Telemetry > 3. Stage Narrative — Stage 1.1 Test Execution
  Telemetry > 3.2 Stop-Gates and Implementation Checklists: No pointer files introduced.

## Signals & Telemetry

* Total unchecked tasks: 30.
* Files containing unchecked tasks: 5.

### Unchecked Tasks by H1

| H1 | Unchecked |
| --- | --- |
| How-To — Authoring Tier-2 Pipeline Documents | 10 |
| Stage 1.1 Roster — Test Execution Telemetry | 8 |
| HealthView HOP Implementation Plan | 5 |
| Tier-2 Pipeline Document Template | 4 |
| Tier-3 Horizontal Document Template | 3 |

## Maintenance Playbook

* Run `python .repo_studios/docs/pipeline/checkbox_report/checkbox_report.py --verbose` after
  checklist edits under `.repo_studios/docs/pipeline`.
* Commit `.repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.csv` and
  `.repo_studios/docs/pipeline/checkbox_report/outputs/checkbox_report.md` together so doc-index
  consumers see the refresh.
* Use the CSV artifact as the source of truth for automation; this Markdown is optimized for
  doc-index discovery.

## Update Log

* 2025-12-19 — Report regenerated.
