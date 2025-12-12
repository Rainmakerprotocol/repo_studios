---
title: "Pipeline Documentation Map"
tier: tier-1
audience:
  - Copilot
  - Repo_Studios
  - Contributors
owners:
  - Docs Guild
role:
  - Reference Map
status: draft
version: v0.1.0
updated_at: 2025-12-11
tags:
  - pipeline
  - navigation
  - tier-docs
related_files:
  - ../../.github/instructions/pipeline_doc_tiers.instructions.md
  - ../../.github/instructions/tier_doc_operating_model.instructions.md
  - ./README.md
  - ./pipeline_templates/tier_doc_system_instructions.md
---
<!-- markdownlint-disable-next-line MD025 -->
# Pipeline Documentation Map

> This Tier-1 supporting doc expands on `docs/pipeline/README.md`. Keep the policy files under
> `.github/instructions/` open while using it so automation guardrails stay in view.

## Goals

* Provide a Copilot-friendly index for every Tier-1/Tier-2/Tier-3 artifact under `docs/pipeline/`.
* Highlight which horizontals gate each pipeline so reciprocity updates are never skipped.
* Capture the evidence workflow (doc-index + checkbox report) required before merging doc edits.

## System Context

### Lifecycle Overview

1. Land here to confirm which pipeline folder contains the Tier-1 spine you need.
2. Jump to the Tier-2/Tier-3 docs listed below and verify they reciprocally link back.
3. Refresh the doc-index (via the `doc-index` make target or platform-equivalent command) to update
   `checkbox_report/outputs/` before logging the Update Log entries in each doc.

### Pipeline Coverage Matrix

* **Command Center Pipeline**
  * Tier-1: `<pending_progress>`
  * Tier-2 (Rosters): `tier2_producers_roster.md`, `tier2_consumers_roster.md`, `tier2_aggregators_roster.md`, `tier2_orchestrators_roster.md`, `tier2_summarizers_roster.md`, `tier2_utilities_roster.md` (all pending)
  * Tier-3: Script-level docs (77 scripts) + library docs (prune_logs, database_integration, cli, artifacts) — see `.repo_studios/scripts/` structure
* **Doc Validation Pipeline**
  * Tier-1: `<pending_progress>`
  * Tier-2: Checkbox report vertical, doc-index generation vertical (pending)
  * Tier-3: `tier3_prune_logs.md` (pending), `tier3_cli.md` (pending)
* **Future Pipelines**
  * Report generation pipeline: `<pending_progress>`
  * Analysis aggregation pipeline: `<pending_progress>`

## Status Board

  Use these tables to log the current state of each pipeline stage. Update them whenever a Tier doc
  changes so the folder README and instructions reflect reality.

  ### Command Center Pipeline Status

  | Stage doc | Status | Last evidence | Notes |
  | --- | --- | --- | --- |
  | `tier1_command_center_pipeline.md` | Pending | — | Needs creation from template |
  | `tier2_producers_roster.md` | Pending | — | 24 producer scripts to document |
  | `tier2_consumers_roster.md` | Pending | — | 4 consumer scripts to document |
  | `tier2_aggregators_roster.md` | Pending | — | 13 aggregator scripts to document |
  | `tier2_orchestrators_roster.md` | Pending | — | 9 orchestrator scripts to document |
  | `tier2_summarizers_roster.md` | Pending | — | 27 summarizer scripts to document |

  ### Doc Validation Pipeline Status

  | Stage doc | Status | Last evidence | Notes |
  | --- | --- | --- | --- |
  | `tier1_doc_validation_pipeline.md` | Pending | — | Needs creation from template |
  | Checkbox report vertical | Pending | — | Tool exists, needs Tier-2 doc |
  | Doc-index generation vertical | Pending | — | Tool exists, needs Tier-2 doc |

### Horizontal Reference

Tier-3 uses **YAML format** optimized for agent tool calling. Each script gets a `tier3_<script_name>.yaml` file.

* `tier3_prune_logs.yaml` (pending) — artifact retention and cleanup semantics; used by producers and orchestrators.
* `tier3_database_integration.yaml` (pending) — PostgreSQL schema and dual-write patterns; used by agents and analysis scripts.
* `tier3_cli.yaml` (pending) — shared CLI argument patterns and config builders; used by all Command Center scripts.
* `tier3_artifacts.yaml` (pending) — timestamped artifact naming and discovery conventions; used by all tiers.
* `tier3_scripts_index.yaml` (auto-generated) — aggregated index of all 77+ scripts for fast agent discovery.
* Update the pipeline templates when additional Tier-3 horizontals are created so reciprocity links stay current.

### Evidence Workflow Checklist

1. Draft or edit the Tier doc by duplicating the appropriate template from
   `pipeline_templates/`.
2. Refresh the doc-index (via the `doc-index` make target or platform-equivalent command) to update `checkbox_report/outputs/`.
3. Record the doc-index timestamp and regression suites inside every touched doc's Update Log.
4. Update reciprocity links: Tier-1 ↔ Tier-2 ↔ Tier-3, ensuring all horizontals are cross-referenced.

## Agent Instructions

1. Use the coverage matrix above to pick the correct Tier-1 spine before drafting guidance or code.
2. Follow each Tier-1 doc’s "Tier-2 Dependencies" and "Tier-3 Horizontals" subsections, then confirm
   those dependents are represented in this map.
3. When you add a doc, update this map and the folder README in the same PR so discoverability stays
   intact.
4. Treat `.repo_studios/scripts/` structure as the source of truth for script organization; cite specific
   Tier-3 library docs (prune_logs, database_integration, cli, artifacts) when editing pipeline docs.
5. Never merge until doc-index refresh + checkbox evidence is captured and logged in the Update Log.

### Agent Automation Block

<!-- agents:begin:pipeline-doc-map -->
```yaml
audience: [Copilot, Repo_Studios]
tasks:
  - id: pipeline-map-coverage
    title: Confirm every Tier-1 spine listed in README appears here
    severity: error
  - id: pipeline-map-reciprocity
    title: Ensure Tier-2/Tier-3 references note reciprocity requirements
    severity: error
  - id: pipeline-map-docindex
    title: Require evidence workflow checklist mentions doc-index run
    severity: warn
```
<!-- agents:end:pipeline-doc-map -->

## Human Notes

* Keep link text descriptive so the doc-index CSV can trace relationships without manual grep.
* If a pipeline gains new stages or verticals, update this map first so downstream docs can
  reference a stable anchor even before their own edits merge.

## Reference Prompts

* "Copilot, verify that every Tier-2 roster doc (producers, consumers, aggregators, orchestrators,
  summarizers, utilities) cites the Command Center Tier-1 spine."
* "List all Tier-3 library docs (prune_logs, database_integration, cli, artifacts) and show which
  Tier-2 rosters reference them according to the map."
* "Confirm the Command Center Tier-2 roster docs recorded doc-index timestamps in their Update Logs."

## Update Log

| Date | Change | Author | Doc-index timestamp | Regression suites | Notes |
| --- | --- | --- | --- | --- | --- |
| 2025-12-11 | Seeded map | Copilot | 2025-12-11T16:33:14Z | doc-index | Init |
| 2025-12-11 | Added status tables | Copilot | 2025-12-11T16:51:01Z | doc-index | Status sync |
