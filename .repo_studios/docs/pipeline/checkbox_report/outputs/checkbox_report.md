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
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md`
  — 86 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_healthview_roster_template.md`
  — 11 unchecked
* `.repo_studios/docs/pipeline/pipeline_templates/tier2_pipeline_howto.md` — 10 unchecked
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier1_healthview_orchestration_pipeline.md`
  — 4 unchecked
* `.repo_studios/docs/pipeline/pipeline_templates/tier2_pipeline_template.md` — 4 unchecked
* `.repo_studios/docs/pipeline/pipeline_templates/tier3_pipeline_template.md` — 3 unchecked

### Sample Outstanding Tasks

* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier1_healthview_orchestration_pipeline.md`
  L439 — HealthView Orchestration Pipeline > 4. Stage 1 – Testing Perspectives > 4.1 Stage 1.1: Test
  Execution Telemetry: Base package complete (`manifest.json`, `summary.md`, `telemetry.json`). See:
  [Stop-gates](tier2_roster/tier2_test_execution_telemetry_roster.md#32-stop-gates)
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier1_healthview_orchestration_pipeline.md`
  L440 — HealthView Orchestration Pipeline > 4. Stage 1 – Testing Perspectives > 4.1 Stage 1.1: Test
  Execution Telemetry: No pointer artifacts (`latest_*` / `current_*`). See:
  [Stop-gates](tier2_roster/tier2_test_execution_telemetry_roster.md#32-stop-gates)
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier1_healthview_orchestration_pipeline.md`
  L441 — HealthView Orchestration Pipeline > 4. Stage 1 – Testing Perspectives > 4.1 Stage 1.1: Test
  Execution Telemetry: Output root aligned to HOP contract
  (`.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`). See: [Contract
  snapshot](tier2_roster/tier2_test_execution_telemetry_roster.md#23-current-vs-target-contract-snapshot-stage-11)
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier1_healthview_orchestration_pipeline.md`
  L442 — HealthView Orchestration Pipeline > 4. Stage 1 – Testing Perspectives > 4.1 Stage 1.1: Test
  Execution Telemetry: Tier-3 eligible (Stage 1.1 Tier-2 depth captured; ready for Tier-3
  extraction). See: [Records
  index](tier2_roster/tier2_test_execution_telemetry_roster.md#31-per-script-inspection-table-v1)
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_healthview_roster_template.md`
  L299 — Tier-2 Roster Template — <STAGE_ID> <STAGE_NAME> > 3. Stage Narrative — <STAGE_ID>
  <STAGE_NAME> > 3.1 Records & Inspection (v1) > Implementation Workstreams (checkbox-driven) —
  <script_name>: Inspect outputs + pruning/retention surfaces; record findings
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_healthview_roster_template.md`
  L303 — Tier-2 Roster Template — <STAGE_ID> <STAGE_NAME> > 3. Stage Narrative — <STAGE_ID>
  <STAGE_NAME> > 3.1 Records & Inspection (v1) > Implementation Workstreams (checkbox-driven) —
  <script_name>: Draft plan to close output-root/base-package stop-gates
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_healthview_roster_template.md`
  L307 — Tier-2 Roster Template — <STAGE_ID> <STAGE_NAME> > 3. Stage Narrative — <STAGE_ID>
  <STAGE_NAME> > 3.1 Records & Inspection (v1) > Implementation Workstreams (checkbox-driven) —
  <script_name>: Implement accepted plan and update this record + stop-gate status with new evidence
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_healthview_roster_template.md`
  L311 — Tier-2 Roster Template — <STAGE_ID> <STAGE_NAME> > 3. Stage Narrative — <STAGE_ID>
  <STAGE_NAME> > 3.1 Records & Inspection (v1) > Implementation Workstreams (checkbox-driven) —
  <script_name>: Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_healthview_roster_template.md`
  L312 — Tier-2 Roster Template — <STAGE_ID> <STAGE_NAME> > 3. Stage Narrative — <STAGE_ID>
  <STAGE_NAME> > 3.1 Records & Inspection (v1) > Implementation Workstreams (checkbox-driven) —
  <script_name>: Inspect Tier-3 template requirements
* `.repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier2_roster/tier2_healthview_roster_template.md`
  L313 — Tier-2 Roster Template — <STAGE_ID> <STAGE_NAME> > 3. Stage Narrative — <STAGE_ID>
  <STAGE_NAME> > 3.1 Records & Inspection (v1) > Implementation Workstreams (checkbox-driven) —
  <script_name>: Draft `tier3_<script_stem>.yaml`

## Signals & Telemetry

* Total unchecked tasks: 118.
* Files containing unchecked tasks: 6.

### Unchecked Tasks by H1

| H1 | Unchecked |
| --- | --- |
| Stage 1.1 Roster — Test Execution Telemetry | 86 |
| Tier-2 Roster Template — <STAGE_ID> <STAGE_NAME> | 11 |
| How-To — Authoring Tier-2 Pipeline Documents | 10 |
| HealthView Orchestration Pipeline | 4 |
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
