---
title: "Stage Tier-2 Compliance Alignment — Template Processing Guide"
tier: reference-document
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - alignment-document
  - processing-guide
  - stage-compliance
status: active
version: 1.0.0
updated_at: 2026-01-28
tags:
  - stage-compliance
  - template-processing
  - tier-2-alignment
  - phase-4
related_files:
  - ./templates/README.md
  - ./templates/tier2_producer_template.md
  - ./templates/tier2_consumer_template.md
  - ./templates/tier2_aggregator_template.md
  - ./templates/tier2_summarizer_template.md
  - ./templates/tier2_orchestrator_template.md
  - ./templates/tier2_utility_template.md
  - ../tier2_test_execution_telemetry_roster.md
  - ../tier2_available_scripts_roster.md
  - ../../tier1_healthview_orchestration_pipeline.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Stage Tier-2 Compliance Alignment — Template Processing Guide

> **Purpose:** This document establishes the alignment contract for processing existing pipeline
> stages through the Stage 12 template system. It ensures consistency across Stage 1.1, 2.1, 3.1,
> 4.1, 5.1, 6.1, and 10.1 as each stage undergoes template-driven compliance review.
>
> **Origin:** Created 2026-01-28 after finalizing Stage 11.1 and Stage 12, when reviewing
> Stage 1.1 revealed the need for systematic template processing of legacy stage documentation.

---

## 1. Problem Statement

### 1.1 Current State

| Stage | Tier-2 Status | Record Format | Build.md Trail | Last Updated |
|-------|---------------|---------------|----------------|--------------|
| 1.1 | `draft` v0.1.1 | Legacy prose | ❌ None | 2026-01-04 |
| 2.1 | TBD | TBD | TBD | TBD |
| 3.1 | TBD | TBD | TBD | TBD |
| 4.1 | TBD | TBD | TBD | TBD |
| 5.1 | TBD | TBD | TBD | TBD |
| 6.1 | TBD | TBD | TBD | TBD |
| 10.1 | TBD | TBD | TBD | TBD |
| **11.1** | **`active` v1.0.0** | **Structured YAML** | **✅ 6 build.md** | **2026-01-28** |

### 1.2 Gap Summary

Stage 11.1 was processed through Phase 4 templates with:

- Structured YAML record blocks per script
- Build.md provenance trail for each processed script
- Tier-3 YAML verification
- Consistent workstream checkbox format
- `active` v1.0.0 promotion

Stages 1.1–6.1 and 10.1 use legacy formats:

- Verbose inline prose records
- Mixed implementation history with current state
- No build.md provenance trail
- Inconsistent workstream naming
- `draft` status

---

## 2. Solution: Template-Driven Stage Processing

### 2.1 Processing Workflow

For each stage (1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 10.1):

```
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 1: Scaffold                                                    │
│ ├── Create stage subfolder: working_docs/stage_X_X/                 │
│ ├── Create build.md for each script using appropriate template      │
│ └── Assign record IDs using stage-specific prefix                   │
├─────────────────────────────────────────────────────────────────────┤
│ Phase 2: Process (per script)                                        │
│ ├── Discovery — verify current state matches Tier-2 claims          │
│ ├── Gap Analysis — identify drift since last review                 │
│ ├── Compliance Check — HOP base package, output root, DB markers    │
│ ├── Evidence Capture — run tests, capture code refs                 │
│ └── Tier-3 Verification — confirm YAML meets template               │
├─────────────────────────────────────────────────────────────────────┤
│ Phase 3: Finalize                                                    │
│ ├── Convert Tier-2 records to structured YAML format                │
│ ├── Normalize workstream checkboxes                                 │
│ ├── Add build.md references to each record                          │
│ ├── Update frontmatter: draft → active, version 1.0.0               │
│ └── Sync Tier-1 stage section                                       │
└─────────────────────────────────────────────────────────────────────┘

### 2.2 Execution Rules (Stage & Script Discipline)

- Process **one stage at a time**, in order, and do not advance to the next stage until the current stage is fully compliant.
- Process **one script at a time**, bringing it to **full compliance** for its script category and HealthView requirements **before** moving to the next script.
- Before leaving a stage, **polish the Tier-2 stage documents** so the stage itself is in full compliance (doc hygiene, standardized sections, and evidence captured).
- After Tier-2 stage polish, **return to Tier-1** and update the stage section to reflect the completed compliance status.
- Doc hygiene and proper methodology are part of compliance and must be treated as hard gates, not optional improvements.
- Repeat this workflow for **Stages 1.1 through 6.1**. Stage 10.1 is **deferred for consideration** after 1.1–6.1 are compliant.
```

### 2.2 Naming Convention

Each stage uses a unique record ID prefix:

| Stage | Prefix | Meaning | Example |
|-------|--------|---------|---------|
| 1.1 | TER | Test Execution Record | TER-001, TER-002, ... |
| 2.1 | S21R | Stage 2.1 Record | S21R-001, S21R-002, ... |
| 3.1 | FDR | Fault Diagnostics Record | FDR-001, FDR-002, ... |
| 4.1 | DIR | Dependency/Import Record | DIR-001, DIR-002, ... |
| 5.1 | CHR | Churn/Heatmap Record | CHR-001, CHR-002, ... |
| 6.1 | SIR | Standards/Inventory Record | SIR-001, SIR-002, ... |
| 10.1 | PIR | Pipeline Integration Record | PIR-001, PIR-002, ... |
| 11.1 | ASR | Available Scripts Record | ASR-001, ASR-002, ... |

> **Note:** Stage 2.1 prefix was changed from AHR to S21R on 2026-02-01 to align with
> deployed usage in tier2_docs_health_overview_roster.md and stage12_metaprompts.md.

### 2.3 Folder Structure

```
tier2_roster/
  working_docs/
    stage_1_1/                           # Stage 1.1 build documents
      TER-001_run_test_execution_telemetry_build.md
      TER-002_collect_test_log_reports_build.md
      TER-003_generate_test_coverage_inventory_build.md
      TER-004_analyze_test_hardening_build.md
      TER-005_generate_test_log_health_report_build.md
      TER-006_generate_churn_complexity_heatmap_build.md
      TER-007_summarize_test_execution_telemetry_build.md
    stage_2_1/                           # Future: Stage 2.1
    stage_3_1/                           # Future: Stage 3.1
    ...
    stage_11_1/                          # Migrate existing ASR-* files here
      ASR-001_generate_anchor_health_report_build.md
      ASR-005_validate_import_boundaries_build.md
      ...
    stage_tier2_compliance_alignment.md  # This document
```

### 2.4 Processing Order

Within each stage, process scripts in **chain order** (top-down):

1. **Orchestrator** — establishes the contract
2. **Producers** — feed the chain
3. **Consumers** — transform producer output
4. **Aggregators** — combine signals
5. **Summarizers** — final bundle

This ensures downstream scripts align with the orchestrator contract.

---

## 3. Stage 1.1 Processing Plan

### 3.1 Script Inventory

| ID | Script | Category | Template |
|----|--------|----------|----------|
| TER-001 | `run_test_execution_telemetry.py` | orchestrator | tier2_orchestrator_template.md |
| TER-002 | `collect_test_log_reports.py` | producer | tier2_producer_template.md |
| TER-003 | `generate_test_coverage_inventory.py` | producer | tier2_producer_template.md |
| TER-004 | `analyze_test_hardening.py` | producer | tier2_producer_template.md |
| TER-005 | `generate_test_log_health_report.py` | consumer | tier2_consumer_template.md |
| TER-006 | `generate_churn_complexity_heatmap.py` | aggregator | tier2_aggregator_template.md |
| TER-007 | `summarize_test_execution_telemetry.py` | summarizer | tier2_summarizer_template.md |

### 3.2 Existing Tier-3 YAMLs

Stage 1.1 already has Tier-3 YAMLs from December 2025:

| Script | Tier-3 YAML | Status |
|--------|-------------|--------|
| TER-001 | `tier3_run_test_execution_telemetry.yaml` | Exists (verify) |
| TER-002 | `tier3_collect_test_log_reports.yaml` | Exists (verify) |
| TER-003 | `tier3_generate_test_coverage_inventory.yaml` | Exists (verify) |
| TER-004 | `tier3_analyze_test_hardening.yaml` | Exists (verify) |
| TER-005 | `tier3_generate_test_log_health_report.yaml` | Exists (verify) |
| TER-006 | `tier3_generate_churn_complexity_heatmap.yaml` | Exists (verify) |
| TER-007 | `tier3_summarize_test_execution_telemetry.yaml` | Exists (verify) |

### 3.3 Processing Checklist

- [x] Create `working_docs/stage_1_1/` folder (2026-01-28)
- [x] Create TER-001 build.md (orchestrator) (2026-01-28)
- [x] Process TER-001 through template compliance — **COMPLIANT** (2026-01-28)
- [x] Create TER-003 build.md (producer) (2026-01-28)
- [x] Process TER-003 through template compliance — **COMPLIANT** (2026-01-28)
- [x] Create TER-004 build.md (producer) (2026-01-28)
- [x] Process TER-004 through template compliance — **COMPLIANT** (2026-01-28)
- [x] Create TER-005 build.md (consumer) (2026-01-28)
- [x] Process TER-005 through template compliance — **COMPLIANT** (2026-01-28)
- [x] Create TER-006 build.md (aggregator) (2026-01-28)
- [x] Process TER-006 through template compliance — **COMPLIANT** (2026-01-28)
- [x] Create TER-007 build.md (summarizer) (2026-01-28)
- [x] Process TER-007 through template compliance — **COMPLIANT** (2026-01-28)
- [ ] Convert Tier-2 roster records to structured YAML
- [ ] Update Tier-2 frontmatter to `active` v1.0.0
- [ ] Sync Tier-1 Stage 1.1 section

---

## 4. Build.md as Provenance

### 4.1 Purpose

Each `*_build.md` file serves as:

1. **Processing Evidence** — Documents what was discovered, analyzed, and verified
2. **Decision Record** — Captures why specific choices were made
3. **Future Reference** — Provides context for later modifications
4. **Discoverability** — Linked from Tier-2 record via `phase4_build_doc` field

### 4.2 Retention Policy

Build.md files are **permanent artifacts**:

- Never delete after processing
- Update `status: complete` when done
- Add to `related_files` in Tier-2 record
- Reference in Tier-2 workstream checkboxes

### 4.3 Template Selection

| Script Category | Build Template |
|-----------------|----------------|
| Producer | `tier2_producer_template.md` |
| Consumer | `tier2_consumer_template.md` |
| Aggregator | `tier2_aggregator_template.md` |
| Summarizer | `tier2_summarizer_template.md` |
| Orchestrator | `tier2_orchestrator_template.md` |
| Utility | `tier2_utility_template.md` |

---

## 5. Tier-2 Roster Overhaul

### 5.1 Record Format Migration

**Legacy format (prose):**

```markdown
#### Record — script_name.py

- **Script:** `.repo_studios/scripts/producers/script_name.py`
  - **Role:** Producer
  - **Entry surface:** `run(argv)` and `main(argv)`
  - **Key CLI inputs (selected):**
    - `--flag1`
    - `--flag2`
  ...
```

**Target format (structured YAML):**

```yaml
##### TER-002: collect_test_log_reports.py

```yaml
record_id: "TER-002"
script:
  path: ".repo_studios/scripts/producers/collect_test_log_reports.py"
  name: "collect_test_log_reports.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_collect_test_log_reports.yaml"
  meets_template: "yes"
  last_updated: "2026-01-28"
tier3_yaml: ".repo_studios/docs/pipeline/.../tier3_collect_test_log_reports.yaml"
phase4_build_doc: ".repo_studios/docs/pipeline/.../working_docs/stage_1_1/TER-002_collect_test_log_reports_build.md"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--logs-dir"
    - "--output-dir"
    - "--artifacts-to-keep"
...
```

### 5.2 Workstream Checkbox Normalization

**Legacy format:**

```markdown
Workstream A — Discovery
- [x] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan
- [x] Draft plan to migrate outputs into Tier-1 canonical root
```

**Target format:**

```markdown
#### Implementation Workstreams (checkbox-driven) — collect_test_log_reports.py

- [x] A. Discovery — confirm CLI surfaces, outputs, retention, and consumers
- [x] B. Plan — artifact renaming to HOP base package
- [x] C. Implement — docstring update, artifact names changed, return keys updated
- [x] D. Evidence — tests passing (N/N)
- [x] E. Tier-3 YAML — verified tier3_collect_test_log_reports.yaml meets template
- [x] F. Orchestrator integration — verified wiring in run_test_execution_telemetry.py
- [x] DONE — Phase 4 compliance complete (2026-01-28)
```

---

## 6. Success Criteria

### 6.1 Per-Stage Completion

A stage is considered complete when:

- [ ] All scripts have build.md in `working_docs/stage_X_X/`
- [ ] All build.md files have `status: complete`
- [ ] All Tier-2 records use structured YAML format
- [ ] All workstream checkboxes use normalized format
- [ ] All records include `phase4_build_doc` field
- [ ] Tier-2 frontmatter updated to `active` v1.0.0
- [ ] Tier-1 stage section synced
- [ ] Doc hygiene verified (markdownlint or explicit exception logged)
- [ ] All scripts in the stage meet full compliance for their category and HealthView demands

### 6.2 Cross-Stage Tracking

| Stage | Scaffold | Process | Finalize | Status |
|-------|----------|---------|----------|--------|
| 1.1 | ✅ | ✅ | ⏳ | Script processing complete |
| 2.1 | ⬜ | ⬜ | ⬜ | Not Started |
| 3.1 | ⬜ | ⬜ | ⬜ | Not Started |
| 4.1 | ⬜ | ⬜ | ⬜ | Not Started |
| 5.1 | ⬜ | ⬜ | ⬜ | Not Started |
| 6.1 | ⬜ | ⬜ | ⬜ | Not Started |
| 10.1 | ⬜ | ⬜ | ⬜ | Not Started |
| **11.1** | ✅ | ✅ | ✅ | **Complete** |

---

## 7. Agent Automation Block

<!-- agents:begin:stage_compliance_alignment -->
```yaml
audience: [Copilot, Repo_Studios]
intent: stage_compliance_alignment
rules:
  - process_in_chain_order: true
  - create_build_md_before_processing: true
  - use_stage_specific_record_prefix: true
  - convert_to_structured_yaml_format: true
  - preserve_build_md_as_provenance: true
checks:
  - id: alignment-scaffold
    title: Verify stage folder created with all build.md files
    severity: error
  - id: alignment-process
    title: Verify all scripts processed through template compliance
    severity: error
  - id: alignment-finalize
    title: Verify Tier-2 roster updated and Tier-1 synced
    severity: error
```
<!-- agents:end:stage_compliance_alignment -->

---

## 8. Update Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-28 | Initial alignment document created for Stage 1.1 processing | GitHub Copilot |
