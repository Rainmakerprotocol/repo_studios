---
title: "Pipeline Documentation Entry Guide"
tier: tier-1
audience:
  - Copilot
  - Repo_Studios
  - Contributors
owners:
  - Docs Guild
role:
  - Navigation Guide
status: draft
version: v0.1.0
updated_at: 2025-12-11
tags:
  - pipeline
  - documentation
  - onboarding
related_files:
  - ../../.github/instructions/pipeline_doc_tiers.instructions.md
  - ../../.github/instructions/tier_doc_operating_model.instructions.md
  - ./pipeline_templates/tier_doc_system_instructions.md
  - ./pipeline_doc_map.md
---

# Pipeline Documentation Entry Guide

> Repo-wide Markdown rules live in `.github/instructions/markdown.instructions.md`.
> Tier-specific policy is defined in `.github/instructions/pipeline_doc_tiers.instructions.md`
> and `.github/instructions/tier_doc_operating_model.instructions.md`. Keep those open while
> using this guide.

## Goals

* Give GitHub Copilot and peer agents a single starting point for everything inside
  `docs/pipeline/`.
* Explain how Tier-1, Tier-2, and Tier-3 docs are laid out so contributors can land in the right
  template immediately.
* Capture the automation contract (doc-index + checkbox report) so evidence is logged before
  pipeline docs change.

## System Context

### Folder Inventory

| Path | Scope | Notes |
| --- | --- | --- |
| [`pipeline_templates/`](./pipeline_templates) | Tier-1, Tier-2, and Tier-3 templates plus how-to guides | Start here when creating new tier docs. Six template files provide complete scaffolding. |
| [`checkbox_report/`](./checkbox_report) | Checkbox detection tool and outputs | Run `checkbox_report.py` or use the `doc-index` make target to refresh `outputs/` before editing pipeline docs. |
| [`pipeline_doc_map.md`](./pipeline_doc_map.md) | Tier-1 supporting doc enumerating all pipelines | Use this for full matrix and dependency lookups across Command Center, Doc Validation, and future pipelines. |
| `<pending_progress>` | Future: Tier-1 pipeline docs | Command Center pipeline, Doc Validation pipeline will live here. |
| `<pending_progress>` | Future: Tier-2 roster docs | Six roster docs (producers, consumers, aggregators, orchestrators, summarizers, utilities) will document script categories. |

### Template & Instruction Pointers

* Templates live in `pipeline_templates/` (`tier1_pipeline_template.md`,
  `tier2_pipeline_template.md`, `tier3_pipeline_template.md`, plus the how-to guides). Duplicate
  before drafting so instruction blocks and update logs stay intact.
* The full 5W1H onboarding walkthrough is in
  `pipeline_templates/tier_doc_system_instructions.md`. It explains when to spawn a
  Tier-2/Tier-3 doc, how to log doc-index runs, and how to keep reciprocity checklists accurate.
* Use this README for orientation, then pivot to `pipeline_doc_map.md` for matrices,
  coverage status, and dependency lookups.

## Status Board

### Status Taxonomy

* `Pending` — doc or stage exists but lacks active work.
* `In Progress` — team or agent is actively editing the stage doc.
* `Blocked` — upstream dependency or Tier-3 horizontal prevents progress.
* `Complete` — evidence logged in the stage doc shows the stop-gates closed.

Update the table below whenever a Tier doc changes so the status board stays aligned with the stage
matrices. When a stage finishes, mark it `Complete` and cite the Update Log row from that doc.

| Pipeline | Scope | Status | Last evidence | Notes |
| --- | --- | --- | --- | --- |
| Command Center | Tier-1 pipeline doc | Pending | — | Template ready for creation |
| Command Center | Tier-2 roster docs (6 total) | Pending | — | Producers/consumers/aggregators/orchestrators/summarizers/utilities |
| Doc Validation | Tier-1 pipeline doc | Pending | — | Template ready for creation |
| Doc Validation | Checkbox report vertical | Pending | — | Tool exists, needs Tier-2 doc |
| Tier-3 Libraries | prune_logs, database_integration, cli, artifacts (YAML format) | Pending | — | Core horizontals for Command Center scripts; agent-optimized YAML |

> Pro tip: Copy additional rows from this table when you open new Tier-2/Tier-3 docs so Copilot can
> reason about live work without scraping every file.

## Agent Instructions

1. **Choose the right entry.** Start with the Tier-1 spine in the relevant folder (when created), then follow its
   "Tier-2 Dependencies" and "Tier-3 Horizontals" subsections before touching code or docs.
2. **Duplicate templates, not live docs.** New verticals must originate from the Tier-2 template;
   horizontals must come from the Tier-3 template.
3. **Regenerate automation artifacts.** Refresh the doc-index (via the `doc-index` make target or platform-equivalent command) after editing any pipeline doc. This
   updates `checkbox_report/outputs/`, so capture the timestamp and regression suites
   in every Update Log you touched.
4. **Cross-link everything.** Whenever you add a Tier-2 or Tier-3 doc, link it from the parent
   Tier-1 section and ensure the new doc cites its dependents. Reference `pipeline_doc_map.md` to
   verify coverage.
5. **Script-specific edits.** If you change Command Center scripts, update the relevant Tier-2 roster doc
   and cite Tier-3 library docs (prune_logs, database_integration, cli, artifacts) where appropriate.

### Agent Automation Block
<!-- agents:begin:pipeline-guide-entry -->
```yaml
audience: [Copilot, Repo_Studios]
tasks:
  - id: pipeline-entry-structure
    title: Verify Tier folder overview + links exist
    severity: error
  - id: pipeline-entry-docindex
    title: Require doc-index timestamp references in Update Logs
    severity: warn
  - id: pipeline-entry-reciprocity
    title: Ensure Tier-1 ↔ Tier-2 ↔ Tier-3 cross-links are described
    severity: error
  - id: pipeline-entry-telemetry
    title: Flag telemetry edits lacking telemetry_hybrid citations
    severity: warn
```
<!-- agents:end:pipeline-guide-entry -->

## Human Notes

* This file intentionally stays high level so it rarely changes; use `pipeline_doc_map.md` for
  detailed matrices and keep that doc updated as new tiers are added.
* If a new pipeline folder is introduced, add it to the table above and ensure its Tier-1 doc links
  back here and to the instructions noted in the banner.

## Reference Prompts

* "Copilot, list the Tier-2 roster docs that will document Command Center scripts and confirm
  each references the Tier-3 library docs (prune_logs, cli, artifacts, database_integration)."
* "Summarize which Tier-3 horizontal gates the checkbox report tool and point me to the
  supporting template."
* "Draft a new Tier-2 roster doc for producers by duplicating the template and logging
  the doc-index evidence per the README instructions."

## Update Log

| Date | Change | Author | Doc-index timestamp | Regression suites | Notes |
| --- | --- | --- | --- | --- | --- |
| 2025-12-11 | Seeded guide | Copilot | 2025-12-11T16:33:14Z | doc-index | Init |
| 2025-12-11 | Added status board | Copilot | 2025-12-11T16:51:01Z | doc-index | Status sync |
