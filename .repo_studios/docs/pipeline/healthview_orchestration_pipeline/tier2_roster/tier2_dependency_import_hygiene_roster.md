---
title: "Tier-2 Roster — Stage 4.1 Dependency & Import Hygiene"
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
target_stage: "4.1"
version: 0.1.0
updated_at: 2025-12-20
tags:
  - pipeline
  - healthview
  - tier-2
  - stage-4-1
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Roster — Stage 4.1 Dependency & Import Hygiene

> **Purpose:** This Tier-2 vertical deep dive will document Stage 4.1
> (Dependency & Import Hygiene) for
> HealthView pipeline. It will inventory the script chain, capture the current vs target I/O contract
> (with evidence), and define stop-gates required before code migrations can claim compliance with
> locked decisions.
>
> **Tier-1 source:** `tier1_healthview_orchestration_pipeline.md` (Stage 4.1).
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

---

## 1. Goals & Success Criteria

1. Produce a single authoritative Tier-2 deep dive for Stage 4.1 that engineers and agents can use
  to implement the Stage 4.1 migration without re-litigating contracts.
1. Make the “current vs target” output and artifact contract explicit, including the canonical
   HealthView root `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
1. Define stop-gates for Stage 4.1 code work (artifact invariants, pruning mechanisms and targets,
  DB marker discipline, and doc-index evidence).

**Success criteria:**

- Tier-1 links to this doc as the Stage 4.1 Tier-2 roster.
- This doc contains:
  - a Records index + Pruning index,
  - a ScriptInspectionRecordV1 schema,
  - per-script record blocks (full records),
  - stop-gates that must be closed before Tier-1 can claim contract compliance.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** Stage 4.1 — Dependency & Import Hygiene
  (`tier1_healthview_orchestration_pipeline.md` → stage section)
- **Tier-2 scope:** This document will cover Stage 4.1 only.

### 2.2 Chain Inventory (Stage 4.1)

**Orchestrator:**

- `.repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py`

**Delegated scripts (expected chain):**

- Producer: `.repo_studios/scripts/producers/generate_dependency_hygiene_report.py`
- Producer: `.repo_studios/scripts/producers/generate_import_graph_report.py` (optional)
- Producer: `.repo_studios/scripts/producers/scan_code_placeholders.py`
- Producer: `.repo_studios/scripts/producers/generate_typecheck_report.py` (optional)
- Utility: `.repo_studios/scripts/utilities/refresh_mypy_baselines.py` (optional)

Notes:

- Keep the chain list in the same order as the orchestrator executes it.
- If the stage includes optional steps, mark them clearly and capture the flag surface.

### 2.3 Current vs Target Contract Snapshot (Stage 4.1)

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
  `.repo_studios/command_center/reports/healthview/dependency_import_hygiene/<YYYYMMDD-HHMM>/`
- Timestamp/run slug shape observed:
  `YYYYMMDD-HHMM` (UTC)
- Artifact set observed in current runs:
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`

Mismatch is treated as a stop-gate.

---

## 3. Stage Narrative — Stage 4.1 Dependency & Import Hygiene

### 3.1 Records & Inspection (v1)

This section will keep the stage’s script-level inspection evidence in Tier-2 (not Tier-1).

#### 3.1.1 Records Index

A short index that links to each per-script record block in this document.

- S41R-001 — dependency import hygiene orchestrator — Orchestrator — (#s41r-001-dependency-import-hygiene-orchestrator)
- S41R-002 — `generate_dependency_hygiene_report.py` — Producer — (#s41r-002-generate_dependency_hygiene_reportpy)
- S41R-003 — `generate_import_graph_report.py` — Producer (optional) — (#s41r-003-generate_import_graph_reportpy)
- S41R-004 — `scan_code_placeholders.py` — Producer — (#s41r-004-scan_code_placeholderspy)
- S41R-005 — `generate_typecheck_report.py` — Producer (optional) — (#s41r-005-generate_typecheck_reportpy)
- S41R-006 — `refresh_mypy_baselines.py` — Utility (optional) — (#s41r-006-refresh_mypy_baselinespy)

#### 3.1.2 Pruning Index (mini-block)

A compact, mechanism-oriented summary of pruning surfaces and how pruning is enforced.

- **Pruning surfaces:**
  - `--artifacts-to-keep` (orchestrator HealthView bundle)
  - `--dependency-artifacts-to-keep`, `--import-graph-artifacts-to-keep`, `--placeholder-artifacts-to-keep`
  - `--cleanup-artifacts-to-keep`, `--typecheck-artifacts-to-keep`, `--baseline-artifacts-to-keep`
  - Producer `--artifacts-to-keep` flags
  - `write_report_artifacts(... keep=...)`
  - `prune_run_directories(... keep=... current_run=...)`
  - `_prune_cleanup_history(... keep=...)`
- **Pruning mechanism:** `prune_by_keep_budget` (directory pruning by keep-budget)
- **Pruning targets:**
  - `.repo_studios/command_center/reports/healthview/dependency_import_hygiene/<YYYYMMDD-HHMM>/`
  - `.repo_studios/reports/producer_reports/healthview/dependency_hygiene/<YYYYMMDD-HHMM>/`
  - `.repo_studios/reports/producer_reports/healthview/import_graph/<YYYYMMDD-HHMM>/`
  - `.repo_studios/reports/producer_reports/code_placeholder_scans/healthview/code_placeholders/<YYYYMMDD-HHMM>/`
  - `.repo_studios/command_center/reports/rawview/dependency_import_hygiene_cleanup/run_batch_cleanup-<YYYY-MM-DD_HHMMSS>/`
  - `.repo_studios/reports/producer_reports/typecheck_reports/healthview/typecheck_report/<YYYYMMDD-HHMM>/`
  - `.repo_studios/command_center/reports/rawview/mypy_baselines/mypy_baselines-<YYYYMMDD_HHMMSS>/`
- **Pruning guardrails:**
  - `write_report_artifacts` and `prune_run_directories` honor `.keep` sentinel files
  - `prune_run_directories` retains `current_run`
  - `_prune_cleanup_history` skips the current cleanup bundle
- **Evidence source:**
  - `.repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py`
  - `.repo_studios/command_center/scripts/libraries/artifacts.py`
  - `.repo_studios/command_center/scripts/libraries/prune_logs.py`

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

##### S41R-001 dependency import hygiene orchestrator

```yaml
record_id: "S41R-001"
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
    - "--healthview-root"
    - "--dependency-output-dir"
    - "--import-graph-output-dir"
    - "--placeholder-output-dir"
    - "--batch-cleanup-output-base"
    - "--typecheck-output-dir"
    - "--mypy-baselines-output-dir"
    - "--dependency-artifacts-to-keep"
    - "--import-graph-artifacts-to-keep"
    - "--placeholder-artifacts-to-keep"
    - "--cleanup-artifacts-to-keep"
    - "--typecheck-artifacts-to-keep"
    - "--baseline-artifacts-to-keep"
    - "--artifacts-to-keep"
    - "--dependency-requirements-pattern"
    - "--dependency-skip-pyproject"
    - "--import-owned"
    - "--placeholder-include-ext"
    - "--placeholder-pattern"
    - "--placeholder-exclude-prefix"
    - "--skip-import-graph"
    - "--skip-typecheck"
    - "--trigger-batch-cleanup"
    - "--refresh-mypy-baselines"
    - "--timestamp"
    - "--log-level"
io_contract:
  inputs:
    - "repo_root + output roots + feature flags + timestamp"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/healthview/dependency_import_hygiene/<YYYYMMDD-HHMM>/"
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
    - "write_report_artifacts(... keep=options.artifacts_to_keep, viewer=healthview, topic=dependency_import_hygiene)"
    - "--cleanup-artifacts-to-keep"
    - "_prune_cleanup_history(... keep=options.cleanup_keep)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/command_center/reports/healthview/dependency_import_hygiene"
    - ".repo_studios/command_center/reports/rawview/dependency_import_hygiene_cleanup"
  guardrails:
    - "write_report_artifacts respects .keep sentinel"
    - "cleanup pruning skips current bundle"
  evidence:
    - "write_report_artifacts viewer/topic layout (slug=YYYYMMDD-HHMM)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py#L1-L38"
    - ".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py#L240-L380"
    - ".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py#L380-L560"
    - ".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py#L540-L760"
    - ".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py#L887-L1127"
    - ".repo_studios/command_center/scripts/libraries/artifacts.py#L88-L202"
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py#L1-L120"
  tests:
    - ".repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py"
  fixtures:
    - "<fixture path>"
notes:
  - >-
    Current HealthView bundle root is under .repo_studios/command_center/reports
    (not the canonical .repo_studios/reports/healthview target).
  - >-
    Stop-gate: placeholder step assumes non-hierarchical output_dir/run_id layout and expects
    report.json/matches.json/log.txt, but scan_code_placeholders emits manifest.json/summary.md/telemetry.json
    under <output_dir>/healthview/code_placeholders/<YYYYMMDD-HHMM>/.
  - >-
    Stop-gate: typecheck step assumes latest_report.json and report.json/report.md/log.txt/raw.txt,
    but generate_typecheck_report emits manifest.json/summary.md/telemetry.json under
    <output_dir>/healthview/typecheck_report/<YYYYMMDD-HHMM>/.
  - >-
    Stop-gate: cleanup planning step writes latest_* pointer artifacts in
    .repo_studios/command_center/reports/rawview/dependency_import_hygiene_cleanup.
  - >-
    Stop-gate: refresh_mypy_baselines writes latest_* pointer artifacts in
    .repo_studios/command_center/reports/rawview/mypy_baselines.
  - "DB markers: none observed in this orchestrator (no create_storage callsites)."
```

##### S41R-002 generate_dependency_hygiene_report.py

```yaml
record_id: "S41R-002"
script:
  path: ".repo_studios/scripts/producers/generate_dependency_hygiene_report.py"
  name: "generate_dependency_hygiene_report.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_dependency_hygiene_report.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--requirements-pattern"
    - "--skip-pyproject"
    - "--artifacts-to-keep"
    - "--timestamp"
    - "--log-level"
io_contract:
  inputs:
    - "repo_root + requirements patterns (optional) + timestamp"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/dependency_hygiene/<YYYYMMDD-HHMM>/"
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
    - "prune_run_directories(... keep=args.artifacts_to_keep, current_run=run_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/dependency_hygiene"
  guardrails:
    - "prune_run_directories retains current_run"
    - "prune_run_directories honors .keep sentinel"
  evidence:
    - "module docstring describes 3-artifact bundle"
    - "prune_run_directories helper"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_dependency_hygiene_report.py#L1-L20"
    - ".repo_studios/scripts/producers/generate_dependency_hygiene_report.py#L30-L70"
    - ".repo_studios/scripts/producers/generate_dependency_hygiene_report.py#L260-L420"
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py#L1-L120"
  tests:
    - ".repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py"
  fixtures:
    - "<fixture path>"
notes:
  - "Orchestrator calls this producer with --output-dir=.repo_studios/reports/producer_reports by default."
  - "Stop-gate: orchestrator tests assume latest_report.json + report.json artifacts, but this producer emits manifest/summary/telemetry."
```

#### Implementation Workstreams (checkbox-driven) — generate_dependency_hygiene_report.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_dependency_hygiene_report.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — generate_dependency_hygiene_report.py complete; update Tier-1 Stage 4.1 script gate

##### S41R-003 generate_import_graph_report.py

```yaml
record_id: "S41R-003"
script:
  path: ".repo_studios/scripts/producers/generate_import_graph_report.py"
  name: "generate_import_graph_report.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_import_graph_report.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--owned"
    - "--artifacts-to-keep"
    - "--timestamp"
    - "--log-level"
io_contract:
  inputs:
    - "repo_root + owned packages (optional) + timestamp"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/import_graph/<YYYYMMDD-HHMM>/"
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
    - "prune_run_directories(... keep=args.artifacts_to_keep, current_run=run_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/import_graph"
  guardrails:
    - "prune_run_directories retains current_run"
    - "prune_run_directories honors .keep sentinel"
  evidence:
    - "module docstring describes 3-artifact bundle"
    - "prune_run_directories helper"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_import_graph_report.py#L1-L18"
    - ".repo_studios/scripts/producers/generate_import_graph_report.py#L20-L55"
    - ".repo_studios/scripts/producers/generate_import_graph_report.py#L260-L415"
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py#L1-L120"
  tests:
    - ".repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py"
  fixtures:
    - "<fixture path>"
notes:
  - "Orchestrator calls this producer with --output-dir=.repo_studios/reports/producer_reports by default."
  - "Stop-gate: orchestrator tests assume latest_report.json + report.json artifacts, but this producer emits manifest/summary/telemetry."
```

#### Implementation Workstreams (checkbox-driven) — generate_import_graph_report.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_import_graph_report.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — generate_import_graph_report.py complete; update Tier-1 Stage 4.1 script gate

##### S41R-004 scan_code_placeholders.py

```yaml
record_id: "S41R-004"
script:
  path: ".repo_studios/scripts/producers/scan_code_placeholders.py"
  name: "scan_code_placeholders.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_scan_code_placeholders.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--root"
    - "--output-dir"
    - "--allowlist-file"
    - "--timestamp"
    - "--include-ext"
    - "--patterns"
    - "--artifacts-to-keep"
    - "--exclude-prefix"
    - "--log-level"
io_contract:
  inputs:
    - "repo_root + scan root + allowlist + timestamp"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/code_placeholder_scans/healthview/code_placeholders/<YYYYMMDD-HHMM>/"
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
    - "prune_run_directories(... keep=options.artifacts_to_keep, current_run=bundle_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/<output_dir>/healthview/code_placeholders"
  guardrails:
    - "prune_run_directories retains current_run"
    - "prune_run_directories honors .keep sentinel"
  evidence:
    - "module docstring describes canonical 3-artifact bundle"
    - "run() prunes topic_dir"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/scan_code_placeholders.py#L1-L30"
    - ".repo_studios/scripts/producers/scan_code_placeholders.py#L120-L190"
    - ".repo_studios/scripts/producers/scan_code_placeholders.py#L430-L569"
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py#L1-L120"
  tests:
    - ".repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py"
  fixtures:
    - "<fixture path>"
notes:
  - "This producer writes under <output_dir>/healthview/code_placeholders/<YYYYMMDD-HHMM>/ (hierarchical layout)."
  - "Orchestrator default output_dir for this script is .repo_studios/reports/producer_reports/code_placeholder_scans."
  - "Stop-gate: orchestrator placeholder step currently expects report.json/matches.json/log.txt in a different layout."
```

#### Implementation Workstreams (checkbox-driven) — scan_code_placeholders.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_scan_code_placeholders.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — scan_code_placeholders.py complete; update Tier-1 Stage 4.1 script gate

##### S41R-005 generate_typecheck_report.py

```yaml
record_id: "S41R-005"
script:
  path: ".repo_studios/scripts/producers/generate_typecheck_report.py"
  name: "generate_typecheck_report.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_typecheck_report.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--log-level"
    - "--all"
    - "--targets"
io_contract:
  inputs:
    - "repo_root + targets (--targets / env / pyproject) + timestamp"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/typecheck_reports/healthview/typecheck_report/<YYYYMMDD-HHMM>/"
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
    - "prune_run_directories(... keep=options.artifacts_to_keep, current_run=bundle_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/<output_dir>/healthview/typecheck_report"
  guardrails:
    - "prune_run_directories retains current_run"
    - "prune_run_directories honors .keep sentinel"
  evidence:
    - "module docstring describes 3-artifact bundle"
    - "main() prunes topic_dir"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_typecheck_report.py#L1-L20"
    - ".repo_studios/scripts/producers/generate_typecheck_report.py#L520-L620"
    - ".repo_studios/scripts/producers/generate_typecheck_report.py#L700-L807"
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py#L1-L120"
  tests:
    - ".repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py"
  fixtures:
    - "<fixture path>"
notes:
  - "Orchestrator default output_dir for this script is .repo_studios/reports/producer_reports/typecheck_reports."
  - >-
    Stop-gate: orchestrator expects latest_report.json + report.json/report.md/log.txt/raw.txt
    artifacts, but this producer emits manifest/summary/telemetry.
```

#### Implementation Workstreams (checkbox-driven) — generate_typecheck_report.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_typecheck_report.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — generate_typecheck_report.py complete; update Tier-1 Stage 4.1 script gate

##### S41R-006 refresh_mypy_baselines.py

```yaml
record_id: "S41R-006"
script:
  path: ".repo_studios/scripts/utilities/refresh_mypy_baselines.py"
  name: "refresh_mypy_baselines.py"
  category: "utility"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_refresh_mypy_baselines.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--target"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--append-timestamp"
    - "--no-append-timestamp"
    - "--log-level"
io_contract:
  inputs:
    - "repo_root + target specs (--target overrides) + timestamp"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/rawview/mypy_baselines/mypy_baselines-<YYYYMMDD_HHMMSS>/"
      artifacts:
        - "bundle_summary.json"
        - "status.json"
        - "SUMMARY.md"
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
    - "ReportArtifact(pointer=latest_*) + copy_latest_artifact"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/command_center/reports/rawview/mypy_baselines"
  guardrails:
    - "write_report_artifacts respects .keep sentinel"
  evidence:
    - "write_report_artifacts non-hierarchical slug format (YYYYMMDD_HHMMSS)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/utilities/refresh_mypy_baselines.py#L1-L40"
    - ".repo_studios/scripts/utilities/refresh_mypy_baselines.py#L120-L220"
    - ".repo_studios/scripts/utilities/refresh_mypy_baselines.py#L340-L459"
    - ".repo_studios/command_center/scripts/libraries/artifacts.py#L88-L202"
  tests:
    - ".repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py"
  fixtures:
    - "<fixture path>"
notes:
  - "Stop-gate: this utility writes latest_* pointer files via write_report_artifacts + copy_latest_artifact."
  - "DB markers: none observed in this utility (no create_storage callsites)."
```

#### Implementation Workstreams (checkbox-driven) — refresh_mypy_baselines.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_refresh_mypy_baselines.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — refresh_mypy_baselines.py complete; update Tier-1 Stage 4.1 script gate

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

- `pytest -q .repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py`

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
| 2025-12-20 | Seeded Stage 4.1 roster skeleton. | repo_studios_ai | 20251220-1533 | Not run |
| 2025-12-20 | Discovery Pass A: populated evidence. | repo_studios_ai | 20251220-1533 | Not run |
