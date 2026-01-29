---
title: Stage 1.1 Roster — Test Execution Telemetry
tier: tier-2
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - roster
  - stage-vertical
status: complete
version: 1.0.0
updated_at: 2026-01-29
tags:
  - pipeline
  - healthview
  - stage-1
  - test-execution-telemetry
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py
  - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py
  - .repo_studios/scripts/producers/collect_test_log_reports.py
  - .repo_studios/scripts/producers/generate_test_coverage_inventory.py
  - .repo_studios/scripts/producers/analyze_test_hardening.py
  - .repo_studios/scripts/consumers/generate_test_log_health_report.py
  - .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py
  - .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Stage 1.1 Roster — Test Execution Telemetry

> **Purpose:** This Tier-2 vertical deep dive documents Stage 1.1 (Test Execution Telemetry) against
> the Tier-1 HealthView contract. It inventories the script chain, captures the current vs target
> I/O contract, and defines stop-gates required before code migrations can claim contract
> compliance.
>
> Tier-1 source: `tier1_healthview_orchestration_pipeline.md` (Stage 1.1).
>
> Standards: `.github/instructions/markdown.instructions.md` (reviewed 2025-12-18) and
> `.github/instructions/pipeline_doc_tiers.instructions.md` (reviewed 2025-12-18).

---

## 0. Instruction Block for Editors & AI Assistants

- This document inherits terminology and stage ordering from the Tier-1 spine:
  `tier1_healthview_orchestration_pipeline.md`.
- Preserve the canonical Tier section order.
- Do not merge aspirational behavior into “Current state”; log it explicitly as a gap or stop-gate.
- Treat Section 3.1 as the authoritative Stage 1.1 script inventory for automation/agents.
  - Do not guess: every assertion needs evidence (code location and/or test).
  - If a script adds outputs that violate locked decisions, record the exception in the Decision Log
    and keep the contradiction explicit in Tier-1 contract docs.
- When Stage 1.1 code changes occur, enforce repo standards:
  - code changes + tests
  - ≥80% coverage on touched modules
  - updated Tier-1/Tier-2 docs
  - clean formatting/lint behavior
- After meaningful edits, run `make -C .repo_studios doc-index` and record the timestamp in
  the Update Log.

---

## 1. Goals & Success Criteria

1. Produce a single authoritative Tier-2 deep dive for Stage 1.1 that engineers and agents can use
  to implement Tier-1 contract migrations without re-litigating contracts.
1. Make the “current vs target” output and artifact contract explicit, including the canonical
   HealthView root `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
1. Define stop-gates for Stage 1.1 code work (artifact invariants, retention behavior, DB marker
   discipline, and doc-index evidence).

**Success criteria:**

- Tier-1 Section 13 links to this doc as the Stage 1.1 Tier-2 roster.
- This doc contains a per-script inspection table (v1) for the full chain.
- This doc lists Stage 1.1 stop-gates that must be closed before Tier-1 can claim Stage 1.1 is
  contract compliant.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** Stage 1.1 — Test Execution Telemetry
  (`tier1_healthview_orchestration_pipeline.md` → Stage 1.1 section)
- **Tier-2 scope:** This doc covers Stage 1.1 only.
- **Tier-3 dependencies:**
  - [tier3_cli.yaml](../../tier3_cli.yaml) (shared CLI builders)
  - [tier3_prune_logs.yaml](../../tier3_prune_logs.yaml) (retention + current_run protection)
  - [tier3_artifacts.yaml](../../tier3_artifacts.yaml) (base package contract + discovery semantics)
  - [tier3_database_integration.yaml](../../tier3_database_integration.yaml)
    (DB dual-write semantics + schema)

### 2.2 Chain Inventory (Stage 1.1)

**Orchestrator:**

- `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py`

**Delegated scripts (6 total):**

- Producer: `.repo_studios/scripts/producers/collect_test_log_reports.py`
- Producer: `.repo_studios/scripts/producers/generate_test_coverage_inventory.py`
- Producer: `.repo_studios/scripts/producers/analyze_test_hardening.py`
- Consumer: `.repo_studios/scripts/consumers/generate_test_log_health_report.py`
- Aggregator: `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py`
- Summarizer: `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py`

### 2.3 Current vs Target Contract Snapshot (Stage 1.1)

**Target contract (locked decisions):**

- Canonical HealthView output root:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`
- Base package (required):
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`
- Additional artifacts are allowed but must be listed with a short, factual reason.
- No pointer files like `latest_*`.
- Retention behavior verified via pruning mechanism + evidence.
- DB integration is gated behind `REPO_STUDIOS_DB_ENABLED` and is best-effort (warn-only failures).
  Every DB callsite requires `DB_INTEGRATION_MARKER:`.

**Current contract (code evidence):**

- Output root defaults under:
  `.repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry/<run_slug>/`
  via the `--healthview-root` default.
- Timestamp/run slug shape observed in tests: `YYYYmmdd-HHmm` (example: `20251201-0101`).
- Base package (current evidence):
  - `manifest.json` is emitted.
  - `summary.md` is emitted.
  - `telemetry.json` is emitted.
- Additional artifacts currently emitted:
  - `test_execution_telemetry_summary.md` (summary markdown)
  - `test_execution_telemetry_summary.json` (summary JSON)

---

## 3. Stage Narrative — Stage 1.1 Test Execution Telemetry

### 3.1 Per-Script Inspection Table (v1)

This section uses a bullet layout (not a wide markdown table) to keep line length ≤100 and improve
scanability.

Agents must treat this section as the authoritative script inventory for Stage 1.1.

**Records index:**

- [TER-001: `run_test_execution_telemetry.py`](#ter-001-run_test_execution_telemetrypy)
- [TER-002: `collect_test_log_reports.py`](#ter-002-collect_test_log_reportspy)
- [TER-003: `generate_test_coverage_inventory.py`](#ter-003-generate_test_coverage_inventorypy)
- [TER-004: `analyze_test_hardening.py`](#ter-004-analyze_test_hardeningpy)
- [TER-005: `generate_test_log_health_report.py`](#ter-005-generate_test_log_health_reportpy)
- [TER-006: `generate_churn_complexity_heatmap.py`](#ter-006-generate_churn_complexity_heatmappy)
- [TER-007: `summarize_test_execution_telemetry.py`](#ter-007-summarize_test_execution_telemetrypy)

**Pruning index:** All scripts use the `shared-helper` mechanism via `prune_run_directories()`.

- [TER-001](#ter-001-run_test_execution_telemetrypy)
- [TER-002](#ter-002-collect_test_log_reportspy)
- [TER-003](#ter-003-generate_test_coverage_inventorypy)
- [TER-004](#ter-004-analyze_test_hardeningpy)
- [TER-005](#ter-005-generate_test_log_health_reportpy)
- [TER-006](#ter-006-generate_churn_complexity_heatmappy)
- [TER-007](#ter-007-summarize_test_execution_telemetrypy)

<!-- agents:begin:stage_1_1_script_inspection_schema_v1 -->
```yaml
schema: ScriptInspectionRecordV1
scope:
  tier1_stage: "Stage 1.1"
  tier2_doc: "tier2_test_execution_telemetry_roster.md"
record_structure:
  required:
    - record_id
    - script (path, category, entry_surface)
    - phase4_build_doc
    - key_cli_inputs
    - current_output_roots
    - current_artifacts
    - retention_surface
    - pruning (mechanism, surface, target, evidence)
    - compliance (output_root_compliant, base_package_compliant, db_integration)
    - tier3 (appropriate, yaml_exists, yaml_name)
    - tests
    - evidence
    - qa_evidence (pytest, mypy, output_truth)
update_rules:
  - "If script CLI or outputs change, update the record."
  - "If additional artifacts are introduced, list them under current_artifacts."
  - "If an exception to locked decisions is introduced, add a Decision Log entry."
```
<!-- agents:end:stage_1_1_script_inspection_schema_v1 -->

#### TER-001: run_test_execution_telemetry.py

```yaml
record_id: "TER-001"

script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py"
  category: "orchestrator"
  entry_surface: "run(argv) and main()"

phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_1_1/TER-001_run_test_execution_telemetry_build.md"

key_cli_inputs:
  - "--repo-root (override repository root resolution)"
  - "--logs-dir (default: .repo_studios/reports/healthview/rawview/test_execution_runs)"
  - "--test-coverage-xml (default: coverage.xml at repo root)"
  - "--heatmap-metrics-source (optional)"
  - "--healthview-root (default: .repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry)"
  - "--timestamp (ISO 8601; run slug becomes YYYYmmdd-HHMM in UTC)"
  - "--artifacts-to-keep"
  - "Delegated retention flags: --collector-artifacts-to-keep, --health-artifacts-to-keep, --coverage-artifacts-to-keep, --heatmap-artifacts-to-keep, --hardening-artifacts-to-keep"

current_output_roots:
  - ".repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/"

current_artifacts:
  base_package:
    - name: "manifest.json"
      reason: "HealthView contract base package"
    - name: "summary.md"
      reason: "HealthView contract base package"
    - name: "telemetry.json"
      reason: "HealthView contract base package"
  additional:
    - name: "child_outcomes.json"
      reason: "per-step outcome details for orchestrator"

retention_surface: "--artifacts-to-keep forwarded to write_report_artifacts()"

pruning:
  mechanism: "shared-helper"
  surface: "callsite write_report_artifacts(..., keep=options.artifacts_to_keep, current_run=<run_dir>)"
  target: "--healthview-root/orchestrator_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/"
  evidence:
    - ".repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py (write_report_artifacts)"

compliance:
  output_root_compliant: true
  base_package_compliant: true
  db_integration: false
  db_integration_note: "No direct DB callsites; delegated scripts include DB integration markers"

tier3:
  appropriate: true
  decision: "create"
  yaml_exists: true
  yaml_name: "tier3_run_test_execution_telemetry.yaml"
  meets_template: true
  last_updated: "2025-12-27"

tests:
  - ".repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py"

evidence:
  - "Run slug derived from options.run_timestamp.strftime('%Y%m%d-%H%M')."
  - "Manifest + summary + telemetry written via write_report_artifacts(stem=HEALTHVIEW_TOPIC, ...)."
  - "Summarizer invoked with --manifest, --telemetry, --output-dir, and --artifacts-to-keep."
  - "Producer timestamp alignment: orchestrator forwards --run-timestamp <YYYYmmdd-HHMM> to collect_test_log_reports.py."

notes:
  - "Delegated scripts continue to own Tier-3 execution recipes."

qa_evidence:
  pytest: "✅ 14/14 passed (2026-01-29)"
  mypy: "✅ (2025-12-25)"
  coverage: "✅ ≥80% (2025-12-25)"
  output_truth: "✅ Base package verified (manifest.json, summary.md, telemetry.json); 3 steps (collect, analyse, summarize) all success; viewer=orchestrator_reports from bundle 20260129-1756"
```

#### TER-002: collect_test_log_reports.py

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
  last_updated: "2025-12-27"
tier3_yaml: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_collect_test_log_reports.yaml"
phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_1_1/TER-002_collect_test_log_reports_build.md"
db_integration_doc: ".repo_studios/command_center/docs/db_integrations/db_integration_test_log_reports.md"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--logs-dir"
    - "--logs-run"
    - "--output-dir"
    - "--run-timestamp"
    - "--summarize-existing"
    - "--run-pytest/--no-run-pytest"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Pytest log run directories under --logs-dir (default: rawview/test_execution_runs)"
    - "JUnit XML files (junit_*.xml) within log run directories"
    - "Pytest text output files (pytest_*.txt) within log run directories"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/rawview/test_log_reports/<YYYYMMDD-HHMM>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/rawview/test_log_reports/<YYYYMMDD-HHMM>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    status: "✅ Base package aligned (2026-01-29)"
retention:
  surfaces:
    - "--artifacts-to-keep (default: 5 via retention_policy.yaml)"
    - "Run directory format: YYYYMMDD-HHMM"
  mechanism: "prune_run_directories(base_dir, keep=N, current_run=bundle_dir)"
  targets:
    - ".repo_studios/reports/healthview/rawview/test_log_reports/"
  guardrails:
    - "Keeps current run; prunes older run directories beyond keep"
    - "No latest_* pointers (HOP-compliant)"
  evidence:
    - "prune_run_directories() called with keep=artifacts_to_keep"
    - "Test: test_collect_test_log_reports_prunes_history (PASSED)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
  notes:
    - "DB schema documented in db_integration_test_log_reports.md (134 lines)"
    - "Tables: report_runs, report_artifacts, test_metrics"
    - "Telemetry extraction mapping defined for time-series queries"
orchestrator_integration:
  orchestrator_ready: true
  promoted_to_orchestrator: true
  target_orchestrator: "run_test_execution_telemetry.py"
  supports_output_dir: true
  supports_artifacts_to_keep: true
  uses_argv_kwarg: false
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/collect_test_log_reports.py#L1-L13 (module docstring)"
    - ".repo_studios/scripts/producers/collect_test_log_reports.py#L617 (run(argv) entry)"
    - ".repo_studios/scripts/producers/collect_test_log_reports.py#L598-L613 (artifact writing)"
  tests:
    - "test_collect_test_log_reports_emits_artifacts (PASSED)"
    - "test_collect_test_log_reports_prunes_history (PASSED)"
    - "test_collect_test_log_reports_handles_missing_runs (PASSED)"
    - "test_collect_test_log_reports_can_run_pytest (PASSED)"
    - "test_collect_test_log_reports_summarize_existing_skips_pytest (PASSED)"
  fixtures: []
  qa_evidence:
    mypy_strict: "✅ Success (2026-01-29)"
    pytest: "✅ 5/5 passed (2026-01-29)"
    output_truth: "✅ 6/6 claims verified TRUE against JUnit XML ground truth"
notes:
  - "Classification: HOP-compliant producer, orchestrator integration complete."
  - "Contract status: ✅ aligned with HOP base package (manifest.json, summary.md, telemetry.json)"
  - "Entry surface: run(argv) — standard positional argv signature."
  - "DB integration: Schema documented; markers not yet in code (doc exists separately)."
  - "Phase 4 processing: Complete 2026-01-29; see phase4_build_doc for verification details."
```

##### TER-003: generate_test_coverage_inventory.py

```yaml
record_id: "TER-003"
script:
  path: ".repo_studios/scripts/producers/generate_test_coverage_inventory.py"
  name: "generate_test_coverage_inventory.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_generate_test_coverage_inventory.yaml"
  meets_template: "yes"
  last_updated: "2026-01-29"
tier3_yaml: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_test_coverage_inventory.yaml"
phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_1_1/TER-003_generate_test_coverage_inventory_build.md"
db_integration_doc: ".repo_studios/command_center/docs/db_integrations/db_integration_generate_test_coverage_inventory.md"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--coverage-xml"
    - "--output-dir"
    - "--timestamp"
    - "--min-coverage"
    - "--include-empty"
    - "--artifacts-to-keep"
    - "--refresh-coverage-xml"
    - "--refresh-tests"
    - "--refresh-cov-target"
    - "--refresh-continue-on-error"
    - "--refresh-omit-tests"
    - "--refresh-pytest-args"
    - "--log-level"
io_contract:
  inputs:
    - "Coverage.py XML report (--coverage-xml, default: coverage.xml)"
    - "Python source files for AST function boundary extraction"
    - "Optional: pytest suites for coverage refresh mode"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/producer_reports/test_coverage_inventory/<YYYYMMDD-HHMM>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/producer_reports/test_coverage_inventory/<YYYYMMDD-HHMM>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    status: "✅ Base package aligned (2026-01-29)"
retention:
  surfaces:
    - "--artifacts-to-keep (default: 5 via retention_policy.yaml)"
    - "Run directory format: YYYYMMDD-HHMM"
  mechanism: "prune_run_directories(base_dir, keep=N, current_run=bundle_dir)"
  targets:
    - ".repo_studios/reports/healthview/producer_reports/test_coverage_inventory/"
  guardrails:
    - "Keeps current run; prunes older run directories beyond keep"
    - "No latest_* pointers (HOP-compliant)"
  evidence:
    - "prune_run_directories() called at L1013-1018"
    - "Test: test_threshold_enforcement_and_pruning (PASSED)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
  notes:
    - "DB schema documented in db_integration_generate_test_coverage_inventory.md (85 lines)"
    - "Tables: report_runs, report_artifacts, test_metrics"
    - "Uses create_storage() for all artifact writes (L920)"
orchestrator_integration:
  orchestrator_ready: true
  promoted_to_orchestrator: true
  target_orchestrator: "run_test_execution_telemetry.py"
  supports_output_dir: true
  supports_artifacts_to_keep: true
  uses_argv_kwarg: false
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_test_coverage_inventory.py#L1-L33 (module docstring)"
    - ".repo_studios/scripts/producers/generate_test_coverage_inventory.py#L805-L822 (run(argv) entry)"
    - ".repo_studios/scripts/producers/generate_test_coverage_inventory.py#L920 (create_storage())"
    - ".repo_studios/scripts/producers/generate_test_coverage_inventory.py#L1005-L1011 (artifact writing)"
  tests:
    - "test_generates_structured_artifacts (PASSED)"
    - "test_threshold_enforcement_and_pruning (PASSED)"
    - "test_helper_timestamp_and_filename_resolution (PASSED)"
    - "test_refresh_coverage_xml_continue_on_error_emits_bundle (PASSED)"
    - "test_refresh_coverage_xml_without_continue_on_error_exits_nonzero (PASSED)"
    - "test_refresh_omit_tests_creates_and_removes_cov_config (PASSED)"
  fixtures: []
  qa_evidence:
    mypy_strict: "✅ Success (2026-01-29)"
    pytest: "✅ 6/6 passed (2026-01-29)"
    output_truth: "✅ 6/6 claims verified TRUE against coverage.xml ground truth"
notes:
  - "Classification: HOP-compliant producer, orchestrator integration complete."
  - "Contract status: ✅ aligned with HOP base package (manifest.json, summary.md, telemetry.json)"
  - "Entry surface: run(argv) → dict[str, Any] — returns status, output_dir, metrics."
  - "DB integration: Uses create_storage() with DB_INTEGRATION_MARKER comments."
  - "Phase 4 processing: Complete 2026-01-29; see phase4_build_doc for verification details."
  - "Coverage refresh mode supports multi-suite execution with continue-on-error semantics."
```

##### TER-004: analyze_test_hardening.py

```yaml
record_id: "TER-004"
script:
  path: ".repo_studios/scripts/producers/analyze_test_hardening.py"
  name: "analyze_test_hardening.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_analyze_test_hardening.yaml"
  meets_template: "yes"
  last_updated: "2025-12-22"
tier3_yaml: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_analyze_test_hardening.yaml"
phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_1_1/TER-004_analyze_test_hardening_build.md"
db_integration_doc: ".repo_studios/command_center/docs/db_integrations/db_integration_analyze_test_hardening.md"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--tests-dir"
    - "--output-dir"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Test directory tree (--tests-dir, default: .repo_studios/tests)"
    - "Python test files (test_*.py, *_test.py) for AST analysis"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/producer_reports/test_hardening/<YYYYMMDD-HHMM>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/producer_reports/test_hardening/<YYYYMMDD-HHMM>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    status: "✅ Base package aligned (2026-01-29)"
retention:
  surfaces:
    - "--artifacts-to-keep (default: 5 via retention_policy.yaml)"
    - "Run directory format: YYYYMMDD-HHMM"
  mechanism: "prune_run_directories(base_dir, keep=N, current_run=bundle_dir)"
  targets:
    - ".repo_studios/reports/healthview/producer_reports/test_hardening/"
  guardrails:
    - "Keeps current run; prunes older run directories beyond keep"
    - "No latest_* pointers (HOP-compliant)"
  evidence:
    - "prune_history() calls prune_run_directories(..., keep=N, current_run=bundle_dir)"
    - "Test: test_artifacts_written (PASSED)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
  notes:
    - "DB_INTEGRATION_MARKER callsites present for manifest/summary/telemetry writes"
    - "Uses create_storage() for all artifact writes"
orchestrator_integration:
  orchestrator_ready: true
  promoted_to_orchestrator: true
  target_orchestrator: "run_test_execution_telemetry.py"
  supports_output_dir: true
  supports_artifacts_to_keep: true
  uses_argv_kwarg: false
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/analyze_test_hardening.py#L1-L20 (module docstring)"
    - ".repo_studios/scripts/producers/analyze_test_hardening.py (run(argv) entry)"
    - ".repo_studios/scripts/producers/analyze_test_hardening.py (create_storage() callsite)"
  tests:
    - "test_detects_missing_assertions_and_long_test (PASSED)"
    - "test_clean_file_marked_ok (PASSED)"
    - "test_artifacts_written (PASSED)"
  fixtures: []
  qa_evidence:
    mypy_strict: "✅ Success (2026-01-29)"
    pytest: "✅ 3/3 passed (2026-01-29)"
    output_truth: "✅ Severity counts verified (194+101+4=299=total_issues)"
notes:
  - "Classification: HOP-compliant producer, orchestrator integration complete."
  - "Contract status: ✅ aligned with HOP base package (manifest.json, summary.md, telemetry.json)"
  - "Entry surface: run(argv) → dict[str, Any] — returns status, output_dir, metrics."
  - "DB integration: Uses create_storage() with DB_INTEGRATION_MARKER comments."
  - "Phase 4 processing: Complete 2026-01-29; see phase4_build_doc for verification details."
  - "Exit code 1 indicates high-severity issues found (expected behavior)."
```

##### TER-005: generate_test_log_health_report.py

```yaml
record_id: "TER-005"
script:
  path: ".repo_studios/scripts/consumers/generate_test_log_health_report.py"
  name: "generate_test_log_health_report.py"
  category: "consumer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_generate_test_log_health_report.yaml"
  meets_template: "yes"
  last_updated: "2025-12-21"
tier3_yaml: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_test_log_health_report.yaml"
phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_1_1/TER-005_generate_test_log_health_report_build.md"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--logs-dir"
    - "--output-base"
    - "--timestamp"
    - "--producer-bundle-dir"
    - "--producer-reports-root"
    - "--producer-report"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Producer bundle telemetry.json (--producer-bundle-dir, preferred)"
    - "Raw pytest logs under --logs-dir (fallback)"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/consumer_reports/test_log_health_reports/<YYYYMMDD-HHMM>/"
      artifacts:
        - "report.json"
        - "report.md"
        - "report.csv"
        - "bundle_summary.json"
    status: "✅ Output contract aligned (2026-01-29)"
    notes: "Consumer does not emit HOP base package; uses report.* convention"
retention:
  surfaces:
    - "--artifacts-to-keep (default: 5 via retention_policy.yaml)"
  mechanism: "prune_run_directories(base_dir, keep=N, current_run=out_dir)"
  evidence:
    - "_prune_history() calls prune_run_directories"
    - "Test: test_generate_test_log_health_report_prunes_history (PASSED)"
db_integration:
  marker_required: false
  notes:
    - "No DB_INTEGRATION_MARKER callsites"
orchestrator_integration:
  orchestrator_ready: true
  target_orchestrator: "run_test_execution_telemetry.py"
evidence:
  tests:
    - "test_generate_test_log_health_report_prefers_producer_bundle (PASSED)"
    - "test_generate_test_log_health_report_falls_back_to_logs (PASSED)"
    - "test_generate_test_log_health_report_prunes_history (PASSED)"
    - "test_timestamp_slug_helpers (PASSED)"
    - "test_markdownlint_injection_is_idempotent (PASSED)"
    - "test_append_delta_markdown_formats_values (PASSED)"
    - "test_select_latest_bundle_dir_prefers_latest_slug (PASSED)"
    - "test_write_csv_emits_expected_rows (PASSED)"
  qa_evidence:
    mypy_strict: "✅ Success (2026-01-29)"
    pytest: "✅ 8/8 passed (2026-01-29)"
    output_truth: "✅ Pass rate verified (63/64=98.44%)"
notes:
  - "Classification: Consumer, HOP output contract aligned."
  - "Does not emit HOP base package; uses report.* convention."
  - "Phase 4 processing: Complete 2026-01-29; see phase4_build_doc."
```

##### TER-006: generate_churn_complexity_heatmap.py

```yaml
record_id: "TER-006"
script:
  path: ".repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py"
  name: "generate_churn_complexity_heatmap.py"
  category: "aggregator"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_generate_churn_complexity_heatmap.yaml"
  meets_template: "yes"
  last_updated: "2025-12-24"
tier3_yaml: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_churn_complexity_heatmap.yaml"
phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_1_1/TER-006_generate_churn_complexity_heatmap_build.md"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-base"
    - "--metrics-source"
    - "--test-log-summary"
    - "--logs-dir"
    - "--window"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Git repository for churn metrics"
    - "Python files for complexity analysis (via lizard)"
    - "Consumer bundle summary (preferred) or raw JUnit logs (fallback)"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/<YYYYMMDD-HHMM>/"
      artifacts:
        - "heatmap.json"
        - "heatmap.md"
        - "bundle_summary.json"
    status: "✅ Output contract aligned (2026-01-29)"
    notes: "Aggregator does not emit HOP base package; uses heatmap.* convention"
retention:
  surfaces:
    - "--artifacts-to-keep (default: 5 via retention_policy.yaml)"
  mechanism: "prune_run_directories(base_dir, keep=N, current_run=run_dir)"
  evidence:
    - "_prune_history() calls prune_run_directories"
    - "Test: test_retention_prunes_old_runs (PASSED)"
db_integration:
  marker_required: false
  notes:
    - "No DB_INTEGRATION_MARKER callsites"
orchestrator_integration:
  orchestrator_ready: true
  target_orchestrator: "run_test_execution_telemetry.py"
evidence:
  tests:
    - "test_prefers_consumer_bundle (PASSED)"
    - "test_fallback_to_logs_when_summary_missing (PASSED)"
    - "test_retention_prunes_old_runs (PASSED)"
    - "test_main_returns_nonzero_when_no_python_files (PASSED)"
    - "test_collect_git_churn_handles_oserror (PASSED)"
    - "test_load_junit_failures_uses_classname_when_file_missing (PASSED)"
  qa_evidence:
    mypy_strict: "✅ Success (2026-01-29)"
    pytest: "✅ 6/6 passed (2026-01-29)"
    output_truth: "✅ 261 files scored, window=500, mode=consumer, top_score=15.67"
notes:
  - "Classification: Aggregator, HOP output contract aligned."
  - "Does not emit HOP base package; uses heatmap.* convention."
  - "Phase 4 processing: Complete 2026-01-29; see phase4_build_doc."
  - "Prefers consumer bundle summary; falls back to logs/JUnit discovery."
  - "No latest_* pointer artifacts (Tier-1 compliant)."
```

#### TER-007: summarize_test_execution_telemetry.py

```yaml
record_id: "TER-007"

script:
  path: ".repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py"
  category: "summarizer"
  entry_surface: "run(argv) and main(argv)"

phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_1_1/TER-007_summarize_test_execution_telemetry_build.md"

key_cli_inputs:
  - "--manifest (path to manifest.json)"
  - "--telemetry (path to telemetry.json)"
  - "--output-dir (default: .repo_studios/reports/healthview)"
  - "--artifacts-to-keep (retention for summary artifacts)"

current_output_roots:
  - ".repo_studios/reports/healthview/summarizer_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/"

current_artifacts:
  base_package: "N/A (this script emits additional artifacts, not base package)"
  additional:
    - name: "test_execution_telemetry_summary.md"
      reason: "additional summary markdown"
    - name: "test_execution_telemetry_summary.json"
      reason: "additional summary JSON"

retention_surface: "--artifacts-to-keep forwarded to write_report_artifacts(..., keep=...)"

pruning:
  mechanism: "shared-helper"
  surface: "callsite write_report_artifacts(..., keep=options.artifacts_to_keep, current_run=<run_dir>)"
  target: "--output-dir/summarizer_reports/test_execution_telemetry/<run_slug>/"
  evidence:
    - ".repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py (write_report_artifacts)"
    - ".repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py"

compliance:
  output_root_compliant: true
  output_root_note: "Default output dir is .repo_studios/reports/healthview and uses the summarizer_reports class token."
  base_package_compliant: "N/A"
  db_integration: false
  db_integration_note: "No DB markers observed in this summarizer"

tier3:
  appropriate: true
  decision: "create"
  yaml_exists: true
  yaml_name: "tier3_summarize_test_execution_telemetry.yaml"
  meets_template: true
  last_updated: "2025-12-24"

tests:
  - ".repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py"

evidence:
  - "Constants: SUMMARY_STEM = 'test_execution_telemetry_summary', TOPIC_SLUG = 'test_execution_telemetry'."
  - "Default: DEFAULT_OUTPUT_DIR = build_topic_path('summarizer', TOPIC_SLUG)."
  - "Artifacts written via write_report_artifacts(...) using filenames f'{SUMMARY_STEM}.md' and f'{SUMMARY_STEM}.json'."

qa_evidence:
  pytest: "✅ 1/1 passed (2026-01-29)"
  mypy: "✅ (2025-12-22)"
  coverage: "✅ 93% (2025-12-24)"
  output_truth: "✅ 5 components (collect, coverage, hardening, health, heatmap), 3 steps (collect, analyse, summarize) verified from bundle 20260129-1756"
```

---

## 4. Signals & Telemetry

**Regression suites (current evidence):**

- `pytest -q .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`

**Telemetry outputs:**

- Stage 1.1 produces `telemetry.json` alongside a manifest containing step outcomes and artifact
  locations.

**Doc evidence workflow:**

- Run `make -C .repo_studios doc-index` after editing this Tier-2 doc and capture the timestamp in
  Update Logs.

---

## 5. Dependencies & Stop-Gates

- **Tier-1 stop-gates:** ✅ All Stage 1.1 stop-gates closed (2025-12-25).
  - Output root: migrated to canonical `.repo_studios/reports/healthview/`.
  - Base package: `manifest.json`, `summary.md`, `telemetry.json` verified.

- **Tier-3 YAML dependencies:**
  - `tier3_cli.yaml` (shared CLI builders)
  - `tier3_prune_logs.yaml` (retention + current_run protection)
  - `tier3_artifacts.yaml` (base package contract)
  - `tier3_database_integration.yaml` (DB dual-write semantics)

- **Feature flags:**
  - `REPO_STUDIOS_DB_ENABLED` (DB dual-write toggle; best-effort/warn-only)

---

## 6. Agent Automation Block

<!-- agents:begin:healthview_stage1_1_roster -->
```yaml
audience: [Copilot, Repo_Studios]
intent: stage_roster
rules:
  - require_front_matter: true
  - require_single_h1: true
  - require_update_log: true
  - no_inline_chat_transcripts: true
  - require_language_fences: true
checks:
  - id: hv-stage1-1-contract
    title: Verify current vs target contract captured
    severity: error
  - id: hv-stage1-1-chain
    title: Verify chain inventory includes 7 scripts (1 orchestrator + 6 delegated)
    severity: error
  - id: hv-stage1-1-stopgates
    title: Stop-gates closed (output root + base package verified)
    severity: warning
```
<!-- agents:end:healthview_stage1_1_roster -->

---

## 7. Decision Log

- 2025-12-19 — Section 3.1 is the authoritative Stage 1.1 script inventory for agents.
  Assertions must carry evidence or be logged as a stop-gate.
- 2025-12-19 — TER-001 serves as the formatting + completeness reference for per-script records.
- 2025-12-19 — Extra per-run artifacts emitted by Stage 1.1 scripts are allowed but must be listed
  with a short, factual reason in the record's `current_artifacts.additional` block.
- 2025-12-25 — Closed `summary.md` stop-gate; migrated output root to canonical HealthView location.
- 2026-01-29 — All 7 Stage 1.1 scripts (TER-001 through TER-007) processed to Phase 4 complete.

---

## 8. Update Log

|Date|Change|Author|Doc-index timestamp|Regression suites|
|---|---|---|---|---|
|2026-01-29|Document cleanup: removed stale stop-gate language (contradictions resolved 2025-12-25); removed redundant Section 6; renumbered sections 7-9 → 6-8; updated Decision Log; updated Agent Automation Block checks.|repo_ai|—|—|
|2026-01-29|Completed Phase 4 processing for TER-001 `run_test_execution_telemetry.py`; converted "Fixture Example" record to YAML format; verified output truth (base package + 3 steps success); linked phase4_build_doc; removed legacy workstream.|repo_ai|—|pytest 14/14; mypy ✅|
|2026-01-29|Completed Phase 4 processing for TER-007 `summarize_test_execution_telemetry.py`; converted record to YAML format; verified output truth (5 components, 3 steps); linked phase4_build_doc; removed legacy workstream.|repo_ai|—|pytest 1/1; mypy ✅|
|2026-01-29|Completed Phase 4 processing for TER-006 `generate_churn_complexity_heatmap.py`; converted record to YAML format; verified output truth (261 files, window=500, top_score=15.67); linked phase4_build_doc; removed legacy workstream.|repo_ai|—|pytest 6/6; mypy ✅|
|2026-01-29|Completed Phase 4 processing for TER-005 `generate_test_log_health_report.py`; converted record to YAML format; verified output truth (63/64=98.44% pass rate); linked phase4_build_doc; removed legacy workstream noise from TER-003/004/005.|repo_ai|—|pytest 8/8; mypy ✅|
|2026-01-29|Completed Phase 4 processing for TER-004 `analyze_test_hardening.py`; converted record to YAML format; verified output truth (severity counts 194+101+4=299); linked phase4_build_doc and db_integration_doc; added qa_evidence section.|repo_ai|—|pytest 3/3; mypy ✅|
|2026-01-29|Completed Phase 4 processing for TER-003 `generate_test_coverage_inventory.py`; converted record to YAML format; verified output truth (6/6 claims TRUE); linked phase4_build_doc and db_integration_doc; added qa_evidence section.|repo_ai|—|pytest 6/6; mypy ✅|
|2026-01-04|Updated Stage 1.1 records to reflect repo-root coverage defaults (`coverage.xml`, `--refresh-cov-target .`) and snapshot-mode coverage refresh behavior (continue-on-error + recorded exit codes).|repo_ai|20260104-1710|doc-index; make studio-orchestrate-test-execution-telemetry|
|2025-12-25|Closed output-root + base-package stop-gates for `run_test_execution_telemetry.py`; updated tests; captured pytest/mypy/coverage evidence.|repo_ai|20251225-0011|pytest; mypy; coverage; doc-index|
|2025-12-22|QA re-run for `analyze_test_hardening.py` (pytest + mypy) and marked record DONE. Doc-index refresh deferred to loop closure (post Tier-1 update).|repo_ai|—|pytest; mypy|
|2025-12-22|Relocated per-script Tier-3 YAMLs for Stage 1.1 Test Execution Telemetry under `healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/`; updated Tier-2 references + refreshed Tier-3 scripts index.|repo_ai|20251222-0222|doc-index|
|2025-12-22|Completed Workstream A discovery for `analyze_test_hardening.py`; recorded DB marker + pruning surfaces; explicitly deferred Tier-3 pending output-root migration.|repo_ai|20251222-0040|doc-index|
|2025-12-22|Completed Workstream A discovery for `generate_test_coverage_inventory.py`; recorded positional bundle outputs + pruning + DB markers; explicitly deferred Tier-3 pending output-root + orchestrator alignment.|repo_ai|20251222-0035|doc-index|
|2025-12-22|Migrated `generate_test_coverage_inventory.py` to Tier-1 compliant output root; aligned Stage 1.1 orchestrator coverage discovery to positional bundles; created + validated `tier3_generate_test_coverage_inventory.yaml`.|repo_ai|20251222-0124|pytest; mypy; coverage; doc-index|
|2025-12-22|Wired Stage 1.1 Tier-3 dependencies to horizontals; drafted + validated `tier3_collect_test_log_reports.yaml`; closed Workstream D and marked `collect_test_log_reports.py` DONE.|repo_ai|20251222-0029|pytest (tier3_index: 28 passed); doc-index|
|2025-12-21|Clarified Workstream D semantics (Tier-3 YAML as reward/conditional) and DONE requirements (A–C + E + explicit D decision).|repo_ai|20251221-1527|doc-index|
|2025-12-21|Migrated `collect_test_log_reports.py` + defaults to canonical `.repo_studios/reports/healthview` root; updated record + tests.|repo_ai|20251221-1827|pytest (8 passed, focused)|
|2025-12-19|Expanded Stage 1.1 placeholders into full records.|repo_ai|—|—|
|2025-12-19|Added schema + fixture + Decision Log.|repo_ai|—|—|
|2025-12-19|Correct doc-index command + evidence.|repo_ai|20251219-1058|doc-index|
|2025-12-18|Drafted Stage 1.1 roster doc.|repo_studios_ai|20251219-1058|mdlint; doc-index|
