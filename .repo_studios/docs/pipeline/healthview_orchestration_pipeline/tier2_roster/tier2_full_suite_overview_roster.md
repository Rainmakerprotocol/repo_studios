---
title: "Tier-2 Roster — Stage 7 Running the Complete Suite"
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
version: 0.1.0
updated_at: 2026-01-04
tags:
  - pipeline
  - healthview
  - tier-2
  - stage-7
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Roster — Stage 7 Running the Complete Suite

> **Purpose:** This Tier-2 vertical deep dive will document Stage 7
> (Running the Complete Suite) for the HealthView pipeline. It will
> inventory the orchestrator chain, capture the current vs target I/O
> contract (with evidence), and define stop-gates required before code
> migrations can claim compliance with locked decisions.
>
> **Tier-1 source:** `tier1_healthview_orchestration_pipeline.md` (Stage 7).
> **Locked decisions source:** Tier-1 spine (`tier1_healthview_orchestration_pipeline.md`) + `REPORT_NAMING_STANDARDS.md`.
> **Last synced with Tier-1:** 2025-12-20.
>
> Standards: `.github/instructions/markdown.instructions.md` (reviewed 2025-12-20) and
> `.github/instructions/pipeline_doc_tiers.instructions.md` (reviewed 2025-12-20).

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

1. Produce a single authoritative Tier-2 deep dive for Stage 7 that engineers and agents can use
  to implement the Stage 7 migration without re-litigating contracts.
1. Make the “current vs target” output and artifact contract explicit, including the canonical
   HealthView root `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
1. Define stop-gates for Stage 7 code work (artifact invariants, pruning mechanisms and targets,
  DB marker discipline, and doc-index evidence).

**Success criteria:**

- Tier-1 links to this doc as the Stage 7 Tier-2 roster.
- This doc contains:
  - a Records index + Pruning index,
  - a ScriptInspectionRecordV1 schema,
  - per-script record blocks (full records),
  - stop-gates that must be closed before Tier-1 can claim contract compliance.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** Stage 7 — Running the Complete Suite
  (`tier1_healthview_orchestration_pipeline.md` → stage section)
- **Tier-2 scope:** This document will cover Stage 7 only.

### 2.2 Chain Inventory (Stage 7)

**Orchestrator:**

- `.repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py`

**Delegated scripts (expected chain):**

- Orchestrator: `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py`
- Orchestrator: `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py`
- Orchestrator: `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py`
- Orchestrator: `.repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py`
- Orchestrator: `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py`
- Orchestrator: `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py`

Notes:

- Keep the chain list in the same order as the orchestrator executes it.
- If the stage includes optional steps, mark them clearly and capture the flag surface.

### 2.3 Current vs Target Contract Snapshot (Stage 7)

This section will be the short, scannable contract summary that Tier-1 routes to.

Authoritative entry points for Tier-1 routing and agent discovery are:

- this Contract Snapshot,
- the Stop-Gates section,
- the Records Index.

**Target contract (locked decisions):**

- Canonical HealthView output root:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`
- Base package (locked target):
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`
- No pointer files like `latest_*`.
- Pruning mechanisms and targets are explicit, stable, and evidence-backed.
- DB integration is gated behind `REPO_STUDIOS_DB_ENABLED` and is best-effort (warn-only failures).
  Every DB callsite includes `DB_INTEGRATION_MARKER:`.

**Current evidence (repo-observed):**

- Output root currently observed:
  `.repo_studios/command_center/reports/<viewer>/<topic>/<YYYYMMDD-HHMM>/`
- Timestamp/run slug shape observed:
  `YYYYMMDD-HHMM` (UTC)
- Artifact set observed in current runs:
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`

Mismatch is treated as a stop-gate.

---

## 3. Stage Narrative — Stage 7 Running the Complete Suite

### 3.1 Records & Inspection (v1)

This section will keep the stage’s script-level inspection evidence in Tier-2 (not Tier-1).

#### 3.1.1 Records Index

A short index that links to each per-script record block in this document.

- S7R-001 — orchestrate_full_diagnostic.py — meta-orchestrator — [record](#s7r-001-full-diagnostic-meta-orchestrator)
- S7R-002 — run_test_execution_telemetry.py — topic orchestrator — [record](#s7r-002-test-execution-telemetry)
- S7R-003 — run_docs_health_overview.py — topic orchestrator — [record](#s7r-003-docs-health)
- S7R-004 — run_fault_diagnostics_overview.py — topic orchestrator — [record](#s7r-004-fault-diagnostics)
- S7R-005 — run_dependency_import_hygiene.py — topic orchestrator — [record](#s7r-005-dependency-import-hygiene)
- S7R-006 — run_monkey_patch_oversight.py — topic orchestrator — [record](#s7r-006-monkey-patch-oversight)
- S7R-007 — run_standards_integrity.py — topic orchestrator — [record](#s7r-007-standards-integrity)

#### 3.1.2 Pruning Index (mini-block)

A compact, mechanism-oriented summary of pruning surfaces and how pruning is enforced.

- **Pruning surfaces:** `<flags / defaults / callsites>`
- **Pruning surfaces:** `--artifacts-to-keep` (meta + each topic), plus per-step
  `--*-artifacts-to-keep` flags
- **Pruning mechanism:** `prune_by_keep_budget` (keep most recent N run
  directories via `write_report_artifacts(... keep=...)`)
- **Pruning targets:**
  - `.repo_studios/command_center/reports/<viewer>/<topic>/<YYYYMMDD-HHMM>/` (meta + topic bundles)
  - `.repo_studios/reports/producer_reports/...` (selected topic intermediates)
  - `.repo_studios/reports/consumer_reports/...` (selected topic intermediates)
  - `.repo_studios/reports/aggregator_reports/...` (selected topic intermediates)
  - `.repo_studios/reports/summarizer_reports/...` (selected topic intermediates)
- **Pruning guardrails:** naming enforcement present in some topics (Docs Health + Standards Integrity)
- **Evidence source:** topic orchestrators import and call `write_report_artifacts(...)` with `keep=options.artifacts_to_keep`

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

##### <record_id>: <script_name>

##### S7R-001 full-diagnostic meta-orchestrator

```yaml
record_id: "S7R-001"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py"
  name: "orchestrate_full_diagnostic.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_orchestrate_full_diagnostic.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--reports-root"
    - "--log-level"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--include"
    - "--exclude"
    - "--stop-on-first-failure / --keep-going"
io_contract:
  inputs:
    - "Selects topics from TOPIC_DEFINITIONS; supports include/exclude"
    - "Forwards --timestamp (ISO-8601) and derives run_slug as YYYYMMDD-HHMM (UTC)"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/healthview/full_diagnostic/YYYYMMDD-HHMM/"
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
    - ".repo_studios/command_center/reports/healthview/full_diagnostic"
  guardrails:
    - "Topic record includes artifact_dir when viewer/topic slugs are present"
  evidence:
    - "orchestrate_full_diagnostic.py: meta_run_slug formatting + report writer"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py#L36-L39"
    - ".repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py#L175-L186"
    - ".repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py#L320-L371"
    - ".repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py#L510-L521"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "Current outputs live under .repo_studios/command_center/reports (not the target HealthView root)."
  - "This orchestrator computes per-topic artifact_dir from each module's VIEWER_SLUG + HEALTHVIEW_TOPIC/TOPIC_SLUG."
```

###### Implementation Workstreams (checkbox-driven)

Rule: Workstreams are inactive until Discovery Pass A is completed.

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_orchestrate_full_diagnostic.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — orchestrate_full_diagnostic.py complete; update Tier-1 Stage 7 stage-gate checklist

##### S7R-002 test-execution-telemetry

```yaml
record_id: "S7R-002"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py"
  name: "run_test_execution_telemetry.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_run_test_execution_telemetry.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--logs-dir"
    - "--test-log-reports-dir"
    - "--test-log-health-dir"
    - "--test-coverage-output-dir"
    - "--heatmap-output-dir"
    - "--hardening-output-dir"
    - "--healthview-root"
    - "--artifacts-to-keep"
    - "--collector-artifacts-to-keep"
    - "--health-artifacts-to-keep"
    - "--coverage-artifacts-to-keep"
    - "--heatmap-artifacts-to-keep"
    - "--hardening-artifacts-to-keep"
    - "--timestamp"
io_contract:
  inputs:
    - "Consumes logs under .repo_studios/reports/healthview/rawview/test_execution_runs (default)"
    - "Accepts --timestamp and derives run_slug as YYYYMMDD-HHMM (UTC)"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "telemetry.json"
        - "summary.md (written by summarizer under healthview_root)"
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
    - "per-step retention flags (collector/health/coverage/heatmap/hardening)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry"
    - ".repo_studios/reports/producer_reports/test_coverage_reports"
    - ".repo_studios/reports/consumer_reports/test_log_health_reports"
    - ".repo_studios/reports/aggregator_reports/churn_complexity_heatmap"
  guardrails:
    - "Pipeline stops on first hard failure by default (coverage refresh may be configured to continue-on-error)"
  evidence:
    - "run_test_execution_telemetry.py: run_slug formatting + report writer"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py#L51-L52"
    - ".repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py#L78-L78"
    - ".repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py#L588-L588"
    - ".repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py#L625-L635"
  tests:
    - "<pytest path>"
  fixtures:
    - "coverage.xml defaults to repo root; fixture coverage XML is used in unit tests only"
notes:
  - "write_report_artifacts emits manifest.json + telemetry.json; summary.md is produced by the summarizer step."
```

###### Implementation Workstreams (checkbox-driven)

Rule: Workstreams are inactive until Discovery Pass A is completed.

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_run_test_execution_telemetry.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — run_test_execution_telemetry.py complete; update Tier-1 Stage 7 script gate

##### S7R-003 docs-health

```yaml
record_id: "S7R-003"
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
    - "--doc-index-output-dir"
    - "--anchor-inventory-output-dir"
    - "--anchor-validation-output-dir"
    - "--docs-integrity-output-dir"
    - "--metrics-stub-output-dir"
    - "--churn-output-dir"
    - "--undocumented-output-dir"
    - "--aggregator-output-dir"
    - "--healthview-root"
    - "--artifacts-to-keep (default 5)"
    - "--skip-<step> flags"
    - "--timestamp"
io_contract:
  inputs:
    - "Runs doc-index + anchor inventory/validation + docs integrity + churn + undocumented logic (unless skipped)"
    - "Accepts --timestamp and derives run_slug as YYYYMMDD-HHMM (UTC)"
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
    - "per-step retention flags (doc-index / anchor inventory / anchor validation / docs integrity / metrics stub / churn / undocumented / aggregator)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/command_center/reports/healthview/docs_health"
    - ".repo_studios/reports/producer_reports"
    - ".repo_studios/reports/aggregator_reports/docs_health_signals"
  guardrails:
    - "enforce_report_naming is executed and failures return non-zero"
  evidence:
    - "run_docs_health_overview.py: run_slug formatting + report writer + naming audit"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L53-L54"
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L103-L103"
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L1198-L1200"
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L1338-L1348"
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L1365-L1383"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "Docstring contains a stray ')' line; behavior evidence comes from code paths and report writer callsites."
```

###### Implementation Workstreams (checkbox-driven)

Rule: Workstreams are inactive until Discovery Pass A is completed.

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_run_docs_health_overview.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — run_docs_health_overview.py complete; update Tier-1 Stage 7 script gate

##### S7R-004 fault-diagnostics

```yaml
record_id: "S7R-004"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py"
  name: "run_fault_diagnostics_overview.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_run_fault_diagnostics_overview.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--runs-dir"
    - "--run-dir"
    - "--producer-output-dir"
    - "--producer-command-center-dir"
    - "--consumer-output-dir"
    - "--consumer-command-center-dir"
    - "--summarizer-output-dir"
    - "--healthview-root"
    - "--artifacts-to-keep"
    - "--producer-artifacts-to-keep"
    - "--consumer-artifacts-to-keep"
    - "--summarizer-artifacts-to-keep"
    - "--reuse-report"
    - "--timestamp"
io_contract:
  inputs:
    - "Reads faulthandler runs under .repo_studios/command_center/reports/rawview/fault_diagnostics_runs (default)"
    - "Accepts --timestamp and derives run_slug as YYYYMMDD-HHMM (UTC)"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/commandview/fault_diagnostics/YYYYMMDD-HHMM/"
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
    - "per-step retention flags (producer/consumer/summarizer)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/command_center/reports/commandview/fault_diagnostics"
    - ".repo_studios/reports/producer_reports/faulthandler_reports"
    - ".repo_studios/reports/consumer_reports/fault_artifacts"
    - ".repo_studios/reports/summarizer_reports/fault_diagnostics_overview"
  guardrails:
    - "Summarizer step described as tolerant in docstring"
  evidence:
    - "run_fault_diagnostics_overview.py: VIEWER_SLUG=commandview + report writer"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py#L52-L53"
    - ".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py#L64-L70"
    - ".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py#L533-L534"
    - ".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py#L577-L587"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "VIEWER_SLUG is commandview (docstring claims healthview bundle path); treat as Stage 7 stop-gate discrepancy."
```

###### Implementation Workstreams (checkbox-driven)

Rule: Workstreams are inactive until Discovery Pass A is completed.

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_run_fault_diagnostics_overview.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — run_fault_diagnostics_overview.py complete; update Tier-1 Stage 7 script gate

##### S7R-005 dependency-import-hygiene

```yaml
record_id: "S7R-005"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py"
  name: "run_dependency_import_hygiene.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_run_dependency_import_hygiene.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--dependency-output-dir"
    - "--import-graph-output-dir"
    - "--placeholder-output-dir"
    - "--batch-cleanup-output-base"
    - "--typecheck-output-dir"
    - "--mypy-baselines-output-dir"
    - "--healthview-root"
    - "--artifacts-to-keep"
    - "--dependency-artifacts-to-keep"
    - "--import-graph-artifacts-to-keep"
    - "--placeholder-artifacts-to-keep"
    - "--cleanup-artifacts-to-keep"
    - "--typecheck-artifacts-to-keep"
    - "--baseline-artifacts-to-keep"
    - "--skip-import-graph"
    - "--skip-typecheck"
    - "--trigger-batch-cleanup"
    - "--refresh-mypy-baselines"
    - "--timestamp"
io_contract:
  inputs:
    - "Runs dependency hygiene + import graph + placeholder scan + optional cleanup/typecheck/baseline refresh"
    - "Derives run_slug via _timestamp_to_slug(options.run_timestamp) => YYYYMMDD-HHMM (UTC)"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/healthview/dependency_import_hygiene/YYYYMMDD-HHMM/"
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
    - "per-step retention flags (dependency/import_graph/placeholder/cleanup/typecheck/baseline)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/command_center/reports/healthview/dependency_import_hygiene"
    - ".repo_studios/reports/producer_reports"
    - ".repo_studios/command_center/reports/rawview/dependency_import_hygiene_cleanup"
    - ".repo_studios/command_center/reports/rawview/mypy_baselines"
  guardrails:
    - "Return code is 0 iff telemetry.success"
  evidence:
    - "run_dependency_import_hygiene.py: _timestamp_to_slug + report writer"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py#L52-L53"
    - ".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py#L419-L420"
    - ".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py#L1024-L1025"
    - ".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py#L1095-L1105"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "Current topic bundle root is under .repo_studios/command_center/reports (not target HealthView root)."
```

###### Implementation Workstreams (checkbox-driven)

Rule: Workstreams are inactive until Discovery Pass A is completed.

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_run_dependency_import_hygiene.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — run_dependency_import_hygiene.py complete; update Tier-1 Stage 7 script gate

##### S7R-006 monkey-patch-oversight

```yaml
record_id: "S7R-006"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py"
  name: "run_monkey_patch_oversight.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_run_monkey_patch_oversight.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--scan-root"
    - "--producer-output-dir"
    - "--consumer-output-dir"
    - "--aggregator-output-dir"
    - "--summarizer-output-dir"
    - "--healthview-root"
    - "--artifacts-to-keep"
    - "--producer-artifacts-to-keep"
    - "--consumer-artifacts-to-keep"
    - "--aggregator-artifacts-to-keep"
    - "--summarizer-artifacts-to-keep"
    - "--producer-with-git"
    - "--producer-strict"
    - "--duplicate-matrix"
    - "--timestamp"
io_contract:
  inputs:
    - "Scans for monkey patches, classifies risk, aggregates trends, and summarizes"
    - "Accepts --timestamp and derives run_slug as YYYYMMDD-HHMM (UTC)"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/commandview/monkey_patch_oversight/YYYYMMDD-HHMM/"
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
    - "per-step retention flags (producer/consumer/aggregator/summarizer)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/command_center/reports/commandview/monkey_patch_oversight"
    - ".repo_studios/reports/producer_reports/monkey_patch_scans"
    - ".repo_studios/reports/consumer_reports/monkey_patch_risk"
    - ".repo_studios/reports/aggregator_reports/monkey_patch_trends"
    - ".repo_studios/reports/summarizer_reports/monkey_patch_overview"
  guardrails:
    - "Summarizer raises if status != ok"
  evidence:
    - "run_monkey_patch_oversight.py: VIEWER_SLUG=commandview + report writer"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py#L52-L53"
    - ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py#L72-L72"
    - ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py#L656-L657"
    - ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py#L708-L718"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "VIEWER_SLUG is commandview (docstring claims healthview bundle path); treat as Stage 7 stop-gate discrepancy."
```

###### Implementation Workstreams (checkbox-driven)

Rule: Workstreams are inactive until Discovery Pass A is completed.

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_run_monkey_patch_oversight.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — run_monkey_patch_oversight.py complete; update Tier-1 Stage 7 script gate

##### S7R-007 standards-integrity

```yaml
record_id: "S7R-007"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py"
  name: "run_standards_integrity.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_run_standards_integrity.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--index-output-dir"
    - "--index-path"
    - "--categories-path"
    - "--gap-output-dir"
    - "--diff-output-dir"
    - "--prompt-output-dir"
    - "--pending-path"
    - "--healthview-root"
    - "--diff-old-index"
    - "--diff-fail-on"
    - "--gap-max-show"
    - "--prompt-include-warn"
    - "--prompt-formats"
    - "--artifacts-to-keep"
    - "--index-artifacts-to-keep"
    - "--gap-artifacts-to-keep"
    - "--diff-artifacts-to-keep"
    - "--prompt-artifacts-to-keep"
    - "--timestamp"
io_contract:
  inputs:
    - "Regenerates standards index, runs gap analysis, optional diff, seeds prompts, and runs summarizer"
    - "Uses run_slug formatting YYYYMMDD-HHMM (UTC)"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/healthview/standards_integrity/YYYYMMDD-HHMM/"
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
    - "per-step retention flags (index/gap/diff/prompt)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/command_center/reports/healthview/standards_integrity"
    - ".repo_studios/reports/producer_reports (standards index)"
    - ".repo_studios/reports/producer_reports/standards_index_diff_reports"
    - ".repo_studios/reports/producer_reports/standards_prompt_seeds"
  guardrails:
    - "enforce_report_naming is executed and failures return non-zero"
  evidence:
    - "run_standards_integrity.py: _format_run_slug + report writer + naming audit"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py#L54-L55"
    - ".repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py#L85-L88"
    - ".repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py#L793-L803"
    - ".repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py#L816-L823"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "Standards index generation also writes under rawview/standards_index/<run_slug> (see INDEX_VIEWER_SLUG/INDEX_TOPIC_SLUG)."
```

###### Implementation Workstreams (checkbox-driven)

Rule: Workstreams are inactive until Discovery Pass A is completed.

Workstream A  Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B  Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C  Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D  Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_run_standards_integrity.yaml`
- [ ] Validate Tier-3 YAML

Workstream E  QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE  run_standards_integrity.py complete; update Tier-1 Stage 7 script gate

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

**Migration stop-gates (code-phase, later):**

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

- After meaningful edits, run `make -C .repo_studios doc-index` and capture the
  timestamp in the Update Log.

---

## 5. Dependencies & Stop-Gates

- **Tier-1 stop-gates blocked by this doc:**
  - Tier-1 cannot consider this stage contract-compliant until the output root and base package
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
    title: Stop-gates include output root + base package + pointers + retention + DB marker rules
    severity: error
```
<!-- agents:end:healthview_stage_roster_template -->

---

## 8. Update Log

| Date | Change | Author | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| 2026-01-04 | Updated Stage 7 summary record to reflect current HealthView rawview/orchestrator paths and repo-root coverage defaults (fixture used for tests only). | GitHub Copilot | 20260104-1710 | doc-index |
| 2025-12-20 | Seeded Stage 7 Tier-2 roster skeleton (placeholders only). | repo_studios_ai | `<doc-index-ts>` | `<suites>` |
