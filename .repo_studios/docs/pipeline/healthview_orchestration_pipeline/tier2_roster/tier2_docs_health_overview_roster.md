---
title: "Tier-2 Roster — Stage 2.1 Docs Health Overview"
tier: tier-2
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - roster
  - stage-vertical
status: seeded
target_stage: "2.1"
version: 0.1.0
updated_at: 2025-12-19
tags:
  - pipeline
  - healthview
  - hop
  - tier-2
  - stage-2-1
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Roster — Stage 2.1 Docs Health Overview

> **Purpose:** This Tier-2 vertical deep dive will document Stage 2.1 (Docs Health Overview) for the
> HealthView HOP. It will inventory the script chain, capture the current vs target I/O contract
> (with evidence), and define stop-gates required before code migrations can claim compliance with
> locked HOP decisions.
>
> **Tier-1 source:** `tier1_healthview_orchestration_pipeline.md` (Stage 2.1).
> **Locked decisions source:** Tier-1 spine (`tier1_healthview_orchestration_pipeline.md`) + `REPORT_NAMING_STANDARDS.md`.
> **Last synced with Tier-1:** 2025-12-19.
>
> Standards: `.github/instructions/markdown.instructions.md` (reviewed 2025-12-19) and
> `.github/instructions/pipeline_doc_tiers.instructions.md` (reviewed 2025-12-19).

---

## 0. Instruction Block for Editors & AI Assistants

- This document inherits terminology and stage ordering from the Tier-1 spine:
  `tier1_healthview_orchestration_pipeline.md`.
- Preserve the canonical Tier section order.
- Do not merge aspirational behavior into “Current evidence”; log it explicitly as a gap or
  stop-gate.
- When code changes begin for this stage, enforce the repo standards:
  - code changes + tests
  - ≥80% coverage on touched modules
  - updated Tier-1/Tier-2 docs
  - clean formatting/lint behavior
- After meaningful checkbox edits, run `make -C .repo_studios doc-index` and record
  the timestamp in the Update Log.
- Workstream semantics:
  - Workstream D (Tier-3 YAML) is the reward workstream and is conditional.
    - If Tier-3 is allowed/required for a record, complete Workstream D and check its checkbox.
    - If Tier-3 is not allowed/required, do not silently skip D: explicitly record
      "Deferred: Tier-3 not appropriate" (or similar) in the record notes/evidence.
  - Tier-2 DONE requires Workstreams A–C + E, plus an explicit Workstream D decision
    (completed if required, otherwise explicitly deferred).

---

## 1. Goals & Success Criteria

1. Produce a single authoritative Tier-2 deep dive for Stage 2.1 that engineers and agents can use
   to implement the HOP migration without re-litigating contracts.
1. Make the “current vs target” output and artifact contract explicit, including the canonical
   HealthView root `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
1. Define stop-gates for Stage 2.1 code work (artifact invariants, pruning mechanisms and targets,
  DB marker discipline, and doc-index evidence).

**Success criteria:**

- Tier-1 links to this doc as the Stage 2.1 Tier-2 roster.
- This doc contains:
  - a Records index + Pruning index,
  - a ScriptInspectionRecordV1 schema,
  - per-script record blocks (full records),
  - stop-gates that must be closed before Tier-1 can claim HOP compliance.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** 2.1 — Docs Health Overview
  (`tier1_healthview_orchestration_pipeline.md` → stage section)
- **Tier-2 scope:** This document will cover Stage 2.1 only.

### 2.2 Chain Inventory (Stage 2.1)

**Orchestrator:**

- `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py`

**Delegated scripts (expected chain):**

- Producer: `.repo_studios/scripts/producers/generate_doc_index.py`
- Producer: `.repo_studios/scripts/producers/generate_anchor_inventory.py`
- Producer: `.repo_studios/scripts/producers/validate_markdown_anchors.py`
- Producer: `.repo_studios/scripts/producers/verify_docs_integrity.py`
- Producer: `.repo_studios/scripts/producers/validate_metrics_anchor_stubs.py`
- Producer: `.repo_studios/scripts/producers/generate_code_doc_churn_report.py`
- Producer: `.repo_studios/scripts/producers/generate_undocumented_logic_report.py`
- Aggregator: `.repo_studios/scripts/aggregators/aggregate_docs_health_signals.py`

Notes:

- Keep the chain list in the same order as the orchestrator executes it.
- If the stage includes optional steps, mark them clearly and capture the flag surface.

### 2.3 Current vs Target Contract Snapshot (Stage 2.1)

This section will be the short, scannable contract summary that Tier-1 routes to.

Authoritative entry points for Tier-1 routing and agent discovery are:

- this Contract Snapshot,
- the Stop-Gates section,
- the Records Index.

**Target contract (locked decisions):**

- Canonical HealthView output root:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`
- Base package (HOP target):
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`
- No pointer files like `latest_*`.
- Pruning mechanisms and targets are explicit, stable, and evidence-backed.
- DB integration is gated behind `REPO_STUDIOS_DB_ENABLED` and is best-effort (warn-only failures).
  Every DB callsite includes `DB_INTEGRATION_MARKER:`.

**Current evidence (repo-observed):**

- Output root currently observed:
  `.repo_studios/command_center/reports/healthview/docs_health/<YYYYMMDD-HHMM>/`
- Timestamp/run slug shape observed:
  `YYYYMMDD-HHMM` (UTC)
- Artifact set observed in current runs:
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`

- Intermediate bundle roots currently observed in this stage:
  - Producers: `.repo_studios/reports/producer_reports/healthview/<topic>/<YYYYMMDD-HHMM>/`
  - Aggregator:
    `.repo_studios/reports/aggregator_reports/docs_health_signals/<YYYYMMDD-HHMM>/`

Mismatch is treated as a stop-gate.

---

## 3. Stage Narrative — Stage 2.1 Docs Health Overview

### 3.1 Records & Inspection (v1)

This section will keep the stage’s script-level inspection evidence in Tier-2 (not Tier-1).

Implementation Workstreams are inactive until Discovery (Workstream A) is completed for the script.

#### 3.1.1 Records Index

A short index that links to each per-script record block in this document.

- `S21R-001` — `run_docs_health_overview.py` — Orchestrator — [anchor](#s21r-001-docs-health-overview-orchestrator)
- `S21R-002` — `generate_doc_index.py` — Producer — [anchor](#s21r-002-generate-doc-index)
- `S21R-003` — `generate_anchor_inventory.py` — Producer — [anchor](#s21r-003-generate-anchor-inventory)
- `S21R-004` — `validate_markdown_anchors.py` — Producer — [anchor](#s21r-004-validate-markdown-anchors)
- `S21R-005` — `verify_docs_integrity.py` — Producer — [anchor](#s21r-005-verify-docs-integrity)
- `S21R-006` — `validate_metrics_anchor_stubs.py` — Producer — [anchor](#s21r-006-validate-metrics-anchor-stubs)
- `S21R-007` — `generate_code_doc_churn_report.py` — Producer — [anchor](#s21r-007-generate-code-doc-churn-report)
- `S21R-008` — `generate_undocumented_logic_report.py` — Producer — [anchor](#s21r-008-generate-undocumented-logic-report)
- `S21R-009` — `aggregate_docs_health_signals.py` — Aggregator — [anchor](#s21r-009-aggregate-docs-health-signals)

#### 3.1.2 Pruning Index (mini-block)

A compact, mechanism-oriented summary of pruning surfaces and how pruning is enforced.

- **Pruning surfaces:**
  - `--artifacts-to-keep` (orchestrator + delegated scripts)
  - orchestrator per-step keep flags
- **Pruning mechanism:**
  - `prune_run_directories(... keep=...)`
  - `write_report_artifacts(... keep=...)`
- **Pruning targets:**
  - Orchestrator bundle root: `.repo_studios/command_center/reports/healthview/docs_health/`
  - Producer bundle roots: `.repo_studios/reports/producer_reports/healthview/<topic>/`
  - Aggregator bundle root:
    `.repo_studios/reports/aggregator_reports/docs_health_signals/`
- **Pruning guardrails:** `current_run` protection when pruning (where supported)
- **Evidence source:** `run_docs_health_overview.py` + each producer/aggregator bundle
  writer/pruner callsite

#### 3.1.3 ScriptInspectionRecordV1 Schema

Use this schema as the per-script record structure for this stage.

```yaml
schema: ScriptInspectionRecordV1
fields:
  record_id: "<string>"
  script:
    path: "<repo-relative path>"
    name: "<filename>"
    category: "producer|consumer|aggregator|summarizer|utility|orchestrator"
  tier3:
    metadata_block_version: "v1"
    allowed: false
    exists: false
    name: "<tier3_yaml_filename>"
    meets_template: "NA"
    last_updated: null
  cli_surfaces:
    run_entrypoint: "run(argv)|main(argv)|other"
    key_flags:
      - "<--flag>"
      - "<--flag>"
  io_contract:
    inputs:
      - "<input description>"
    outputs:
      current:
        root: "<current root>"
        artifacts:
          - "<artifact>"
      target:
        root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
        artifacts:
          - "manifest.json"
          - "summary.md"
          - "telemetry.json"
  retention:
    surfaces:
      - "<flags / defaults / callsites>"
    mechanism: "<prune_by_timestamp / prune_by_rank / prune_by_manifest / other>"
    targets:
      - "<bundle roots and intermediate roots>"
    guardrails:
      - "<current_run_protection / exclusions / atomic_write / other>"
    evidence:
      - "<tests / docstrings / fixtures / code_refs>"
  db_integration:
    gated_by: "REPO_STUDIOS_DB_ENABLED"
    marker_required: true
    marker_string: "DB_INTEGRATION_MARKER:"
  evidence:
    code_refs:
      - "<path>#Lx-Ly"
    tests:
      - "<pytest path>"
    fixtures:
      - "<fixture path>"
  notes:
    - "<short note>"
```

#### 3.1.4 Per-Script Full Record Blocks

Populate one block per script in the chain. Keep each record concise and evidence-backed.

##### S21R-001 docs health overview orchestrator

```yaml
record_id: "S21R-001"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py"
  name: "run_docs_health_overview.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_run_docs_health_overview.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--log-level"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--healthview-root"
    - "--*-output-dir (per-step output roots)"
    - "--skip-* (per-step skip flags)"
io_contract:
  inputs:
    - "Delegates to producer/aggregator modules and threads per-step output roots + keep budgets"
    - "Accepts --timestamp (ISO-8601) and derives run_slug as YYYYMMDD-HHMM (UTC)"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/healthview/docs_health/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "write_report_artifacts(... keep=options.artifacts_to_keep)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/command_center/reports/healthview/docs_health"
  guardrails:
    - "Report naming audit via enforce_report_naming(...)"
  evidence:
    - "write_report_artifacts(... keep=...) + run_slug formatting"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L46-L107"
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L331-L463"
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L970-L1005"
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L1198-L1386"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "Current orchestrator outputs are under .repo_studios/command_center/reports (not the target HealthView root)."
  - "DB markers: none observed in this orchestrator (it does not call create_storage)."
  - >-
    Orchestrator manifest includes undocumented_report pointing at
    undocumented_outcome.artifacts['report.json'], but the undocumented producer
    currently emits telemetry.json only (see S21R-008 notes).
```

#### Implementation Workstreams (checkbox-driven) — run_docs_health_overview.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_run_docs_health_overview.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — run_docs_health_overview.py complete; update Tier-1 Stage 2.1 script gate

##### S21R-002 generate doc index

```yaml
record_id: "S21R-002"
script:
  path: ".repo_studios/scripts/producers/generate_doc_index.py"
  name: "generate_doc_index.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_doc_index.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--timestamp"
    - "--log-level"
    - "--artifacts-to-keep"
    - "--refresh-checkbox-report"
    - "--refresh-tier3-index"
io_contract:
  inputs:
    - "Scans repo documentation and emits a Doc Index payload + CSV"
    - "Optional: refreshes checkbox report / Tier-3 index before indexing"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/doc_index/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
        - "doc_index.csv"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "prune_run_directories(... keep=options.artifacts_to_keep)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/doc_index"
  guardrails:
    - "current_run protection when pruning"
  evidence:
    - "create_storage(...) bundle writer + prune_run_directories(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_doc_index.py#L32-L34"
    - ".repo_studios/scripts/producers/generate_doc_index.py#L712-L790"
    - ".repo_studios/scripts/producers/generate_doc_index.py#L804-L936"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "DB markers present for manifest/summary/telemetry writes; doc_index.csv write is explicitly marked as no-DB."
  - "Return payload omits doc_index.csv path even though the file is written into the bundle dir."
```

#### Implementation Workstreams (checkbox-driven) — generate_doc_index.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_doc_index.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — generate_doc_index.py complete; update Tier-1 Stage 2.1 script gate

##### S21R-003 generate anchor inventory

```yaml
record_id: "S21R-003"
script:
  path: ".repo_studios/scripts/producers/generate_anchor_inventory.py"
  name: "generate_anchor_inventory.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_anchor_inventory.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--docs-root"
    - "--additional-docs-root (repeatable)"
    - "--output-dir"
    - "--timestamp"
    - "--log-level"
    - "--artifacts-to-keep"
io_contract:
  inputs:
    - "Scans documentation roots and inventories heading-derived anchors"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/anchor_inventory/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "prune_run_directories(... keep=max(1, options.artifacts_to_keep), current_run=bundle_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/anchor_inventory"
  guardrails:
    - "current_run protection when pruning"
  evidence:
    - "create_storage(...) bundle writer + prune_run_directories(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_anchor_inventory.py#L21-L23"
    - ".repo_studios/scripts/producers/generate_anchor_inventory.py#L239-L309"
    - ".repo_studios/scripts/producers/generate_anchor_inventory.py#L588-L747"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "DB markers present for manifest/summary/telemetry writes."
```

#### Implementation Workstreams (checkbox-driven) — generate_anchor_inventory.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_anchor_inventory.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — generate_anchor_inventory.py complete; update Tier-1 Stage 2.1 script gate

##### S21R-004 validate markdown anchors

```yaml
record_id: "S21R-004"
script:
  path: ".repo_studios/scripts/producers/validate_markdown_anchors.py"
  name: "validate_markdown_anchors.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_validate_markdown_anchors.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv)"
  key_flags:
    - "--repo-root"
    - "--root"
    - "--glob (repeatable)"
    - "--output-dir"
    - "--timestamp"
    - "--log-level"
    - "--artifacts-to-keep"
io_contract:
  inputs:
    - "Scans selected markdown files and validates internal + cross-file anchors"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/markdown_anchor_validation/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "prune_run_directories(... keep=options.artifacts_to_keep, current_run=run_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/markdown_anchor_validation"
  guardrails:
    - "current_run protection when pruning"
  evidence:
    - "create_storage(...) bundle writer + prune_run_directories(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/validate_markdown_anchors.py#L1-L33"
    - ".repo_studios/scripts/producers/validate_markdown_anchors.py#L365-L406"
    - ".repo_studios/scripts/producers/validate_markdown_anchors.py#L426-L466"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "DB markers present for manifest/summary/telemetry writes."
  - "This producer does not expose a run(argv) helper; orchestrators must invoke main(argv) or shell out."
```

#### Implementation Workstreams (checkbox-driven) — validate_markdown_anchors.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_validate_markdown_anchors.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — validate_markdown_anchors.py complete; update Tier-1 Stage 2.1 script gate

##### S21R-005 verify docs integrity

```yaml
record_id: "S21R-005"
script:
  path: ".repo_studios/scripts/producers/verify_docs_integrity.py"
  name: "verify_docs_integrity.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_verify_docs_integrity.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--index"
    - "--output-dir"
    - "--update"
    - "--regen-table"
    - "--artifacts-to-keep"
    - "--log-level"
    - "--exit-codes-hash"
io_contract:
  inputs:
    - "Validates governed JSON blocks and content_hash stability (optionally updates mismatches)"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/docs_integrity_validation/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "prune_run_directories(... keep=max(options.artifacts_to_keep, 1), current_run=run_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/docs_integrity_validation"
  guardrails:
    - "current_run protection when pruning"
  evidence:
    - "Module docstring describes canonical bundle root + artifacts"
    - "create_storage(...) bundle writer + prune_run_directories(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/verify_docs_integrity.py#L1-L23"
    - ".repo_studios/scripts/producers/verify_docs_integrity.py#L155-L236"
    - ".repo_studios/scripts/producers/verify_docs_integrity.py#L579-L688"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "DB markers present for manifest/summary/telemetry writes."
```

#### Implementation Workstreams (checkbox-driven) — verify_docs_integrity.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_verify_docs_integrity.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — verify_docs_integrity.py complete; update Tier-1 Stage 2.1 script gate

##### S21R-006 validate metrics anchor stubs

```yaml
record_id: "S21R-006"
script:
  path: ".repo_studios/scripts/producers/validate_metrics_anchor_stubs.py"
  name: "validate_metrics_anchor_stubs.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_validate_metrics_anchor_stubs.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--legacy-file"
    - "--allowlist-path"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Scans markdown for metrics_orchestrator.md#<anchor> links and validates legacy stub headings"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/metrics_anchor_stub_validation/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "prune_run_directories(... keep=max(keep, 1), current_run=run_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/metrics_anchor_stub_validation"
  guardrails:
    - "current_run protection when pruning"
  evidence:
    - "Module docstring describes canonical bundle root + artifacts"
    - "create_storage(...) bundle writer + prune_run_directories(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/validate_metrics_anchor_stubs.py#L1-L27"
    - ".repo_studios/scripts/producers/validate_metrics_anchor_stubs.py#L109-L159"
    - ".repo_studios/scripts/producers/validate_metrics_anchor_stubs.py#L375-L466"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "DB markers present for manifest/summary/telemetry writes."
  - "Return payload does not include an artifacts mapping; consumers must infer paths from output_dir + run_timestamp."
```

#### Implementation Workstreams (checkbox-driven) — validate_metrics_anchor_stubs.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_validate_metrics_anchor_stubs.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — validate_metrics_anchor_stubs.py complete; update Tier-1 Stage 2.1 script gate

##### S21R-007 generate code doc churn report

```yaml
record_id: "S21R-007"
script:
  path: ".repo_studios/scripts/producers/generate_code_doc_churn_report.py"
  name: "generate_code_doc_churn_report.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_code_doc_churn_report.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--doc-index"
    - "--anchor-inventory"
    - "--allowlist"
    - "--git-window"
    - "--git-until"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Reads git history for code churn and correlates to doc index candidates"
    - "Loads doc index + anchor inventory from canonical topic dirs (expects telemetry.json bundles)"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/code_doc_churn/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "prune_run_directories(... keep=options.artifacts_to_keep, current_run=run_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/code_doc_churn"
  guardrails:
    - "current_run protection when pruning"
  evidence:
    - "create_storage(...) bundle writer + prune_run_directories(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_code_doc_churn_report.py#L1-L29"
    - ".repo_studios/scripts/producers/generate_code_doc_churn_report.py#L165-L216"
    - ".repo_studios/scripts/producers/generate_code_doc_churn_report.py#L538-L671"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "DB markers present for manifest/summary/telemetry writes."
```

#### Implementation Workstreams (checkbox-driven) — generate_code_doc_churn_report.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_code_doc_churn_report.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — generate_code_doc_churn_report.py complete; update Tier-1 Stage 2.1 script gate

##### S21R-008 generate undocumented logic report

```yaml
record_id: "S21R-008"
script:
  path: ".repo_studios/scripts/producers/generate_undocumented_logic_report.py"
  name: "generate_undocumented_logic_report.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_undocumented_logic_report.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--doc-index"
    - "--anchor-inventory"
    - "--allowlist"
    - "--include-command-center"
    - "--code-root (repeatable)"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Scans automation code for functions/classes lacking docstrings"
    - "Loads doc index (JSON payload via telemetry.json) + anchor inventory (via loader)"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/undocumented_logic/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "prune_run_directories(... keep=options.artifacts_to_keep, current_run=run_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/undocumented_logic"
  guardrails:
    - "current_run protection when pruning"
  evidence:
    - "create_storage(...) bundle writer + prune_run_directories(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_undocumented_logic_report.py#L1-L33"
    - ".repo_studios/scripts/producers/generate_undocumented_logic_report.py#L140-L195"
    - ".repo_studios/scripts/producers/generate_undocumented_logic_report.py#L580-L731"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "DB markers present for manifest/summary/telemetry writes."
  - >-
    Mismatch: orchestrator references undocumented_outcome.artifacts['report.json'],
    but this producer returns only manifest/summary/telemetry artifacts.
```

#### Implementation Workstreams (checkbox-driven) — generate_undocumented_logic_report.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_undocumented_logic_report.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — generate_undocumented_logic_report.py complete; update Tier-1 Stage 2.1 script gate

##### S21R-009 aggregate docs health signals

```yaml
record_id: "S21R-009"
script:
  path: ".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py"
  name: "aggregate_docs_health_signals.py"
  category: "aggregator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_aggregate_docs_health_signals.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--churn-report"
    - "--undocumented-report"
    - "--anchor-inventory"
    - "--anchor-validation"
    - "--docs-integrity"
    - "--metrics-stub"
    - "--placeholder-report"
    - "--monkey-patch-report"
    - "--skip-hygiene"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Consumes prior stage bundles (canonical topic dirs or bundle dirs containing telemetry.json; supports legacy report.json)"
    - "Optionally blends hygiene signals unless --skip-hygiene"
  outputs:
    current:
      root: ".repo_studios/reports/aggregator_reports/docs_health_signals/YYYYMMDD-HHMM/"
      artifacts:
        - "report.json"
        - "report.md"
        - "signals.tsv"
        - "signals.csv"
        - "bundle_summary.json"
        - "latest_report.json"  # pointer artifact
        - "latest_report.md"    # pointer artifact
        - "latest_signals.tsv"  # pointer artifact
        - "latest_signals.csv"  # pointer artifact
        - "latest_bundle_summary.json"  # pointer artifact
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "write_report_artifacts(... keep=options.artifacts_to_keep)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/aggregator_reports/docs_health_signals"
  guardrails:
    - "keep-budget pruning inside write_report_artifacts(...)"
  evidence:
    - "ReportArtifact(pointer=latest_*) definitions + write_report_artifacts(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py#L21-L31"
    - ".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py#L170-L238"
    - ".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py#L888-L933"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "Stop-gate: emits pointer artifacts (latest_*) which conflict with the target contract's 'no pointer files' rule."
  - "DB markers: none observed in this aggregator (it does not call create_storage)."
```

#### Implementation Workstreams (checkbox-driven) — aggregate_docs_health_signals.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_aggregate_docs_health_signals.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — aggregate_docs_health_signals.py complete; update Tier-1 Stage 2.1 script gate

### 3.2 Stop-Gates and Implementation Checklists

Stop-gates are the stage-level truth gates that must be closed before Tier-1 can claim contract
compliance.

Tier-3 YAMLs are promotion artifacts: they should only be created after Tier-2 stop-gates for this
stage are satisfied and the Tier-2 record set is stable enough to extract reusable horizontals.

**Tier-2 authoring stop-gates (docs-first):**

- Ensure canonical `<class>/<topic>` tokens for this stage are explicit.
- Ensure `<timestamp>` formatting is explicit and supported by evidence or a locked decision.
- Ensure Records index and Pruning index are populated.
- Ensure each per-script record includes Tier-3 metadata fields.
- Ensure Tier-1 routes to the authoritative entry points (Contract Snapshot, Stop-Gates, Records Index).

**HOP migration stop-gates (code-phase, later):**

- Output root is migrated to `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Base package is enforced: `manifest.json`, `summary.md`, `telemetry.json`.
- No pointer files are introduced.
- Pruning mechanisms and targets align to the target contract and are evidenced.
- If DB writes are present: gate behind `REPO_STUDIOS_DB_ENABLED`, warn-only failures, and include
  `DB_INTEGRATION_MARKER:` at each callsite.
- Tier-1 stage section is updated and contradiction entries are closed as evidence confirms.

---

## 4. Signals & Telemetry

**Regression suites (current evidence):**

- TBD (pytest invocation(s) for this stage)

**Telemetry outputs:**

- This stage will emit `telemetry.json` alongside a manifest that captures step outcomes and
  artifact locations.

**Doc evidence workflow:**

- After meaningful edits, run `make -C .repo_studios doc-index` and capture the
  timestamp in the Update Log.

---

## 5. Dependencies & Stop-Gates

- **Tier-1 stop-gates blocked by this doc:**
  - Tier-1 cannot consider this stage HOP-compliant until the output root and base package
    stop-gates are closed.

- **Tier-3 dependencies (placeholders until created):**
- **Tier-3 promotion bar:** Tier-3 YAML placeholders remain placeholders until Tier-2 stop-gates are
  satisfied; Tier-2 is the promotion bar for creating Tier-3 artifacts.

- **Tier-3 dependencies (placeholders until created):**
  - Tier-3 placeholder — TBD: tier3_cli_orchestration_doc
  - Tier-3 placeholder — TBD: tier3_pruning_retention_doc
  - Tier-3 placeholder — TBD: tier3_artifacts_contract_doc
  - Tier-3 placeholder — TBD: tier3_database_integration_doc

- **Feature flags:**
  - `REPO_STUDIOS_DB_ENABLED` (DB dual-write toggle)

---

## 6. Instruction Block (Required by Tier Rules)

1. Editors follow `.github/instructions/markdown.instructions.md` and
   `.github/instructions/pipeline_doc_tiers.instructions.md`.
1. Keep this document’s section order intact.
1. After adding or moving checkboxes, run `make -C .repo_studios doc-index` and
   record the timestamp in Update Logs.
1. Keep “Target contract (locked decisions)” and “Current evidence (repo-observed)” explicit;
    mismatch is treated as a stop-gate.

---

## 7. Agent Automation Block

<!-- agents:begin:healthview_stage_roster_template -->
```yaml
audience: [Copilot, Repo_Studios]
intent: stage_roster_template
rules:
  - require_front_matter: true
  - require_single_h1: true
  - require_update_log: true
  - require_records_index: true
  - require_pruning_index: true
  - require_script_record_schema: true
  - require_tier3_metadata_fields: true
checks:
  - id: hv-tier2-template-contract
    title: Capture current vs target contract snapshot
    severity: error
  - id: hv-tier2-template-records
    title: Records index + per-script records present
    severity: error
  - id: hv-tier2-template-stopgates
    title: >-
      Stop-gates include output root + base package + pointers + retention +
      DB marker rules
    severity: error
```
<!-- agents:end:healthview_stage_roster_template -->

---

## 8. Update Log

| Date | Change | Author | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| 2025-12-19 | Seeded Stage 2.1 Tier-2 roster template. | repo_studios_ai | TBD | TBD |
