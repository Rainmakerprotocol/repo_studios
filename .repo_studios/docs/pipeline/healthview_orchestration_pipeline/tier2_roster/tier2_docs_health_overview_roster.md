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
- After meaningful checkbox edits, run `make -C .repo_studios studio-generate-doc-index` and record
  the timestamp in the Update Log.

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
  `.repo_studios/command_center/reports/healthview/docs_health/<YYYY-MM-DD>/`
- Timestamp/run slug shape observed:
  `<YYYY-MM-DD>`
- Artifact set observed in current runs:
  - `<ARTIFACT_1>`
  - `<ARTIFACT_2>`
  - `<ARTIFACT_3>`

Mismatch is treated as a stop-gate.

---

## 3. Stage Narrative — Stage 2.1 Docs Health Overview

### 3.1 Records & Inspection (v1)

This section will keep the stage’s script-level inspection evidence in Tier-2 (not Tier-1).

Implementation Workstreams are inactive until Discovery (Workstream A) is completed for the script.

#### 3.1.1 Records Index

A short index that links to each per-script record block in this document.

- `<record_id>` — `generate_doc_index.py` — Producer — `<record_anchor>`
- `<record_id>` — `generate_anchor_inventory.py` — Producer — `<record_anchor>`
- `<record_id>` — `validate_markdown_anchors.py` — Producer — `<record_anchor>`
- `<record_id>` — `verify_docs_integrity.py` — Producer — `<record_anchor>`
- `<record_id>` — `validate_metrics_anchor_stubs.py` — Producer — `<record_anchor>`
- `<record_id>` — `generate_code_doc_churn_report.py` — Producer — `<record_anchor>`
- `<record_id>` — `generate_undocumented_logic_report.py` — Producer — `<record_anchor>`
- `<record_id>` — `aggregate_docs_health_signals.py` — Aggregator — `<record_anchor>`

#### 3.1.2 Pruning Index (mini-block)

A compact, mechanism-oriented summary of pruning surfaces and how pruning is enforced.

- **Pruning surfaces:** `<flags / defaults / callsites>`
- **Pruning mechanism:** `<prune_by_timestamp / prune_by_rank / prune_by_manifest / other>`
- **Pruning targets:** `<bundle roots and intermediate roots>`
- **Pruning guardrails:** `<current_run_protection / exclusions / atomic_write / other>`
- **Evidence source:** `<tests / docstrings / fixtures>`

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

##### <record_id>: generate_doc_index.py

```yaml
record_id: "<record_id>"
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

#### Implementation Workstreams (checkbox-driven) — generate_doc_index.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_doc_index.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — generate_doc_index.py complete; update Tier-1 Stage 2.1 script gate

##### <record_id>: generate_anchor_inventory.py

```yaml
record_id: "<record_id>"
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

#### Implementation Workstreams (checkbox-driven) — generate_anchor_inventory.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_anchor_inventory.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — generate_anchor_inventory.py complete; update Tier-1 Stage 2.1 script gate

##### <record_id>: validate_markdown_anchors.py

```yaml
record_id: "<record_id>"
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
  run_entrypoint: "run(argv)"
  key_flags:
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

#### Implementation Workstreams (checkbox-driven) — validate_markdown_anchors.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_validate_markdown_anchors.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — validate_markdown_anchors.py complete; update Tier-1 Stage 2.1 script gate

##### <record_id>: verify_docs_integrity.py

```yaml
record_id: "<record_id>"
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

#### Implementation Workstreams (checkbox-driven) — verify_docs_integrity.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_verify_docs_integrity.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — verify_docs_integrity.py complete; update Tier-1 Stage 2.1 script gate

##### <record_id>: validate_metrics_anchor_stubs.py

```yaml
record_id: "<record_id>"
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

#### Implementation Workstreams (checkbox-driven) — validate_metrics_anchor_stubs.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_validate_metrics_anchor_stubs.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — validate_metrics_anchor_stubs.py complete; update Tier-1 Stage 2.1 script gate

##### <record_id>: generate_code_doc_churn_report.py

```yaml
record_id: "<record_id>"
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

#### Implementation Workstreams (checkbox-driven) — generate_code_doc_churn_report.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_code_doc_churn_report.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — generate_code_doc_churn_report.py complete; update Tier-1 Stage 2.1 script gate

##### <record_id>: generate_undocumented_logic_report.py

```yaml
record_id: "<record_id>"
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

#### Implementation Workstreams (checkbox-driven) — generate_undocumented_logic_report.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_undocumented_logic_report.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [ ] DONE — generate_undocumented_logic_report.py complete; update Tier-1 Stage 2.1 script gate

##### <record_id>: aggregate_docs_health_signals.py

```yaml
record_id: "<record_id>"
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

#### Implementation Workstreams (checkbox-driven) — aggregate_docs_health_signals.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
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

- `<pytest -q path/to/test_file.py>`

**Telemetry outputs:**

- This stage will emit `telemetry.json` alongside a manifest that captures step outcomes and
  artifact locations.

**Doc evidence workflow:**

- After meaningful edits, run `make -C .repo_studios studio-generate-doc-index` and capture the
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
  - Tier-3 placeholder — `<tier3_cli_orchestration_doc>`
  - Tier-3 placeholder — `<tier3_pruning_retention_doc>`
  - Tier-3 placeholder — `<tier3_artifacts_contract_doc>`
  - Tier-3 placeholder — `<tier3_database_integration_doc>`

- **Feature flags:**
  - `REPO_STUDIOS_DB_ENABLED` (DB dual-write toggle)

---

## 6. Instruction Block (Required by Tier Rules)

1. Editors follow `.github/instructions/markdown.instructions.md` and
   `.github/instructions/pipeline_doc_tiers.instructions.md`.
1. Keep this document’s section order intact.
1. After adding or moving checkboxes, run `make -C .repo_studios studio-generate-doc-index` and
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
    title: Stop-gates include output root + base package + pointers + retention + DB marker rules
    severity: error
```
<!-- agents:end:healthview_stage_roster_template -->

---

## 8. Update Log

| Date | Change | Author | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| 2025-12-19 | Seeded Stage 2.1 Tier-2 roster from template (placeholders only). | repo_studios_ai | <doc-index-ts> | <suites> |
