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
status: draft
version: 0.1.0
updated_at: 2025-12-25
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
- When Stage 1.1 code changes begin, enforce the repo standards:
  - code changes + tests
  - ≥80% coverage on touched modules
  - updated Tier-1/Tier-2 docs
  - clean formatting/lint behavior
- After meaningful checkbox edits, run `make -C .repo_studios doc-index` and record the timestamp in
  the Update Log.
- Workstream semantics:
  - Workstream D (Tier-3 YAML) is the reward workstream and is conditional.
    - If Tier-3 is allowed/required for a record, complete Workstream D and check its checkbox.
    - If Tier-3 is not allowed/required, do not silently skip D: explicitly record
      "Deferred: Tier-3 not appropriate" (or similar) in the record notes/evidence.
  - Tier-2 DONE requires Workstreams A–C + E, plus an explicit Workstream D decision
    (completed if required, otherwise explicitly deferred).

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

**Delegated scripts (6 total, Tier-1 stated chain):**

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

Implementation Workstreams are inactive until Discovery (Workstream A) is completed for the script.

**Records index:**

- [Fixture Example (Permanent) — `run_test_execution_telemetry.py`](#fixture-example-permanent--run_test_execution_telemetrypy)
- [Record — collect_test_log_reports.py](#record--collect_test_log_reportspy)
- [Record — generate_test_coverage_inventory.py](#record--generate_test_coverage_inventorypy)
- [Record — analyze_test_hardening.py](#record--analyze_test_hardeningpy)
- [Record — generate_test_log_health_report.py](#record--generate_test_log_health_reportpy)
- [Record — generate_churn_complexity_heatmap.py](#record--generate_churn_complexity_heatmappy)
- [Record — summarize_test_execution_telemetry.py](#record--summarize_test_execution_telemetrypy)

**Pruning index:**

- [Fixture Example (Permanent)](#fixture-example-permanent--run_test_execution_telemetrypy) (shared-helper)
- [Record — collect_test_log_reports.py](#record--collect_test_log_reportspy) (shared-helper)
- [Record — generate_test_coverage_inventory.py](#record--generate_test_coverage_inventorypy) (shared-helper)
- [Record — analyze_test_hardening.py](#record--analyze_test_hardeningpy) (shared-helper)
- [Record — generate_test_log_health_report.py](#record--generate_test_log_health_reportpy) (shared-helper)
- [Record — generate_churn_complexity_heatmap.py](#record--generate_churn_complexity_heatmappy) (shared-helper)
- [Record — summarize_test_execution_telemetry.py](#record--summarize_test_execution_telemetrypy) (shared-helper)

<!-- agents:begin:stage_1_1_script_inspection_schema_v1 -->
```yaml
schema: ScriptInspectionRecordV1
scope:
  tier1_stage: "Stage 1.1"
  tier2_doc: "tier2_test_execution_telemetry_roster.md"
required_fields:
  - script_path
  - role
  - entry_surface
  - key_cli_inputs
  - current_output_roots
  - current_artifacts
  - retention_surface
  - output_root_compliance
  - base_package_compliance
  - db_integration
  - tests
  - evidence
update_rules:
  - "If the script CLI or outputs change, update the corresponding record in this section."
  - >-
    If additional artifacts are introduced, list them under current_artifacts with a short,
    factual reason.
  - >-
    If an exception to locked decisions is introduced (non-canonical output root, pointer files),
    add a Decision Log entry with rationale and scope.
  - "If a field is unknown, mark it as a stop-gate or gap; do not guess."
```
<!-- agents:end:stage_1_1_script_inspection_schema_v1 -->

#### Fixture Example (Permanent) — `run_test_execution_telemetry.py`

This fixture is intentionally verbose. Keep it as the canonical reference for how to fill out a
record.

- **Script:** `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py`
  - **Role:** Orchestrator
  - **Entry surface:** `run(argv)` and `main()`
  - **Key CLI inputs (selected):**
    - `--repo-root` (override repository root resolution)
    - `--logs-dir` (default: `.repo_studios/command_center/reports/rawview/test_execution_runs`)
    - `--test-coverage-xml` (default fixture: `.repo_studios/tests/fixtures/test_run_coverage/coverage.xml`)
    - `--heatmap-metrics-source` (optional)
    - `--healthview-root` (default: `.repo_studios/command_center/reports`)
    - `--timestamp` (ISO 8601; run slug becomes `YYYYmmdd-HHMM` in UTC)
    - `--artifacts-to-keep`
    - Delegated retention flags:
      - `--collector-artifacts-to-keep`
      - `--health-artifacts-to-keep`
      - `--coverage-artifacts-to-keep`
      - `--heatmap-artifacts-to-keep`
      - `--hardening-artifacts-to-keep`
  - **Current output roots:**
    - `.repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/`
  - **Current artifacts (observed):**
    - Base package (Tier-1 HealthView contract):
      - `manifest.json` (emitted)
      - `summary.md` (emitted)
      - `telemetry.json` (emitted)
    - Additional artifacts (allowed) written by summarizer:
      - `test_execution_telemetry_summary.md` — additional summary markdown.
      - `test_execution_telemetry_summary.json` — additional summary JSON.
  - **Retention surface:** `--artifacts-to-keep` forwarded to `write_report_artifacts()`.

  Pruning:
  - Mechanism: shared-helper
  - Surface: callsite `write_report_artifacts(..., keep=options.artifacts_to_keep, current_run=<run_dir>)`
  - Target: `--healthview-root/orchestrator_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/`
  - Evidence: `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` (`write_report_artifacts`)

  - **Output root compliant (Tier-1 HealthView contract):** ✅
  - **Base package compliant (manifest + summary + telemetry):** ✅
  - **DB integration:** ❌ (no direct DB callsites observed)
    - Delegated scripts include DB integration markers and/or storage writers.
  - **Tier-3 appropriate:** deferred (delegated scripts have Tier-3 YAML; orchestrator invoked directly)
  - **Tier-3 YAML exists:** no
  - **Tier-3 YAML name:** `tier3_run_test_execution_telemetry.yaml`
  - **Tier-3 meets template:** NA
  - **Tier-3 last updated:** —
  - **Tests:** `.repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`
  - **Evidence:**
    - Run slug derived from `options.run_timestamp.strftime("%Y%m%d-%H%M")`.
    - Manifest + summary + telemetry written via `write_report_artifacts(stem=HEALTHVIEW_TOPIC, ...)`.
    - Summarizer invoked with `--manifest`, `--telemetry`, `--output-dir`, and `--artifacts-to-keep`.
    - Producer timestamp alignment: orchestrator forwards `--run-timestamp <YYYYmmdd-HHMM>` to
      `collect_test_log_reports.py`.
  - **Notes:**
    - Delegated scripts continue to own Tier-3 execution recipes.

#### Implementation Workstreams (checkbox-driven) — run_test_execution_telemetry.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [x] Draft plan to close output-root/base-package stop-gates

Plan notes (draft):

- Target output root (Tier-1 HealthView contract): write the orchestrator base package under
  `.repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/`.
- Orchestrator change set:
  - Update `--healthview-root` default to `.repo_studios/reports/healthview`.
  - Set `VIEWER_SLUG = "orchestrator_reports"` so the bundle path includes the required class
    segment.
  - Add `summary.md` to the base package (alongside `manifest.json` and `telemetry.json`) using a
    small `_summarize_steps(...)` helper consistent with other orchestrators.
  - Pass deterministic timestamp into `collect_test_log_reports.py` (`--run-timestamp
    <YYYYmmdd-HHMM>`) so the producer bundle aligns with the orchestrator run slug.
  - Update `DEFAULT_HEATMAP_OUTPUT_DIR` to
    `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap` so the
    orchestrator default matches the aggregator's canonical output root.
- Tests:
  - Update `.repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`
    to assert the new base package directory layout and the presence of `summary.md`.

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.

Implementation evidence (2025-12-25):

- Updated `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py`:
  - `DEFAULT_HEALTHVIEW_ROOT` now defaults to `.repo_studios/reports/healthview`.
  - `VIEWER_SLUG = "orchestrator_reports"`.
  - Base package now includes `summary.md`.
  - `_execute_collect(...)` forwards `--run-timestamp`.
- Updated `.repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`:
  - Asserts `summary.md` exists and `manifest["viewer"] == "orchestrator_reports"`.

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
  - Decision (2025-12-25): deferred; orchestrator is invoked directly and does not require a
    Tier-3 YAML recipe for the current HealthView loop.
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_run_test_execution_telemetry.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [x] Pytest evidence captured
- [x] Mypy evidence captured or marked N/A (in record)
- [x] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

Evidence (2025-12-25):

- Pytest: `.\.venv\Scripts\python.exe -m pytest -q .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`
- Mypy: `\.\.venv\Scripts\python.exe -m mypy .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py`
- Coverage:
  - `.\.venv\Scripts\python.exe -m coverage run -m pytest -q .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`
  - `.\.venv\Scripts\python.exe -m coverage report --include=.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py --fail-under=80`
- Doc-index: `make -C .repo_studios doc-index` (20251225-0011)


- [x] DONE — run_test_execution_telemetry.py complete; update Tier-1 Stage 1.1 script gate

#### Record — collect_test_log_reports.py

- **Script:** `.repo_studios/scripts/producers/collect_test_log_reports.py`
  - **Role:** Producer
  - **Entry surface:** `run(argv)` and `main(argv)`
  - **Key CLI inputs (selected):**
    - `--logs-dir` (default: `.repo_studios/command_center/reports/rawview/test_execution_runs`)
    - `--logs-run` (optional explicit run directory)
    - `--output-dir` (default: `.repo_studios/reports/healthview`)
    - `--run-timestamp` (UTC slug in `YYYYMMDD-HHMM`)
    - `--artifacts-to-keep`
  - **Current output roots:**
    - `.repo_studios/reports/healthview/rawview/test_log_reports/<YYYYmmdd-HHMM>/`
  - **Current artifacts (observed):**
    - Base package (Tier-1 HealthView contract):
      - `manifest.json` (emitted)
      - `summary.md` (emitted)
      - `telemetry.json` (emitted)
    - Additional artifacts (allowed): none observed.
  - **Retention surface:**
    - `--artifacts-to-keep` forwarded to `prune_run_directories(..., keep=..., ...)`.

  Pruning:
  - Mechanism: shared-helper
  - Surface: callsite `prune_run_directories(base_dir, keep=..., current_run=bundle_dir, ...)`
  - Target: `--output-dir/rawview/test_log_reports/<YYYYmmdd-HHMM>/`
  - Evidence:
    - `.repo_studios/scripts/producers/collect_test_log_reports.py` (`prune_run_directories`)
    - `.repo_studios/tests/tests_producers/test_collect_test_log_reports.py` (prunes history)

  - **Output root compliant (Tier-1 HealthView contract):** ✅
  - **Base package compliant (manifest + summary + telemetry):** ✅
  - **DB integration:** ✅
    - `DB_INTEGRATION_MARKER:` callsites present for manifest/summary/telemetry writes.
  - **Tier-3 appropriate:** yes (decision: create Tier-3 YAML)
  - **Tier-3 YAML exists:** yes
  - **Tier-3 YAML name:** `tier3_collect_test_log_reports.yaml`
  - **Tier-3 meets template:** yes (Tier-3 agent pipeline YAML template)
  - **Tier-3 last updated:** 2025-12-21
  - **Tests:** `.repo_studios/tests/tests_producers/test_collect_test_log_reports.py`
  - **Evidence:**
    - Defaults: `DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/healthview")`,
      `VIEWER_SLUG = "rawview"`, `TOPIC_SLUG = "test_log_reports"`.
    - Bundle paths: `bundle_dir = output_dir / VIEWER_SLUG / TOPIC_SLUG / timestamp`.
    - Artifact filenames: `manifest.json`, `summary.md`, `telemetry.json`.
    - Discovery (2025-12-21): this workspace had no existing run directories under
      `.repo_studios/command_center/reports/rawview/test_log_reports/` or
      `.repo_studios/command_center/reports/rawview/test_execution_runs/` at time of inspection.
    - Retention helper:
      `prune_run_directories(base_dir=output_dir/VIEWER_SLUG/TOPIC_SLUG, current_run=bundle_dir, keep=...)`
      sorts candidates by filesystem `st_mtime` (not directory name) and deletes beyond `keep`,
      honoring `.keep`.
    - Unit test evidence:
      `.\.venv/Scripts/python.exe -m pytest -q .repo_studios/tests/tests_producers/test_collect_test_log_reports.py`
      (3 passed).
    - Focused regression evidence:
      `.\.venv/Scripts/python.exe -m pytest -q .repo_studios/tests/tests_producers/test_collect_test_log_reports.py .repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`
      (8 passed).
    - Mypy evidence (2025-12-21):
      `.\.venv/Scripts/python.exe -m mypy .repo_studios/scripts/producers/collect_test_log_reports.py`
      (success).
    - Coverage evidence (2025-12-21):
      `.\.venv/Scripts/python.exe -m coverage run -m pytest -q .repo_studios/tests/tests_producers/test_collect_test_log_reports.py`
      + `.\.venv/Scripts/python.exe -m coverage report --include=.repo_studios/scripts/producers/collect_test_log_reports.py --fail-under=80`
      (84%).
    - Doc-index evidence (2025-12-21):
      `make -C .repo_studios doc-index LOG_LEVEL=INFO` (timestamp: 20251221-2237).
    - Tier-3 YAML evidence (2025-12-21):
      `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_collect_test_log_reports.yaml` validated via
      `\.\.venv/Scripts/python.exe -m pytest -q .repo_studios/docs/pipeline/tier3_index/test_tier3_index.py`.
    - Orchestrator wiring:
      `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` passes
      `--output-dir <test_log_reports_dir>` into this script, where `test_log_reports_dir` is
      controlled by the orchestrator flag `--test-log-reports-dir` and defaults to
      `.repo_studios/reports/healthview`.

#### Implementation Workstreams (checkbox-driven) — collect_test_log_reports.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [x] Draft plan to migrate outputs into Tier-1 canonical root

Plan notes (draft):

- Target output root (Tier-1 HOP contract): write bundles under
  `.repo_studios/reports/healthview/rawview/test_log_reports/<YYYYmmdd-HHMM>/`.
- Producer change: update `DEFAULT_OUTPUT_DIR` to `.repo_studios/reports/healthview` (keeping
  `VIEWER_SLUG="rawview"` and `TOPIC_SLUG="test_log_reports"`).
- Orchestrator compatibility: because
  `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` always passes
  `--output-dir` into the producer, we must also either:
  - update the orchestrator default `--test-log-reports-dir` to `.repo_studios/reports/healthview`,
    or
  - keep the orchestrator default as-is for a migration window, but explicitly set
    `--test-log-reports-dir .repo_studios/reports/healthview` in any HealthView contract runs.
- Consumer/orchestrator compatibility: update consumers that read producer bundles to prefer the new
  root but fall back to the legacy root when the new location is empty (migration window).
  - Example dependent: `.repo_studios/scripts/consumers/generate_test_log_health_report.py`.
- Tests: update/add coverage so:
  - default output location is validated,
  - pruning continues to honor `.keep` and does not delete the current run,
  - no pointer artifacts are created.

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create)
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_collect_test_log_reports.yaml`
- [x] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [x] Pytest evidence captured
- [x] Mypy evidence captured or marked N/A (in record)
- [x] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

- [x] DONE — collect_test_log_reports.py complete; update Tier-1 Stage 1.1 script gate

#### Record — generate_test_coverage_inventory.py

- **Script:** `.repo_studios/scripts/producers/generate_test_coverage_inventory.py`
  - **Role:** Producer
  - **Entry surface:** `run(argv)` and `main(argv)`
  - **Key CLI inputs (selected):**
    - `--repo-root` (override repository root resolution)
    - `--coverage-xml` (Coverage.py XML)
    - `--output-dir` (reports root)
    - `--timestamp` (ISO 8601; run slug becomes `YYYYmmdd-HHMM` in UTC)
    - `--min-coverage` (optional threshold gate)
    - `--include-empty` (include files with zero detected functions)
    - `--artifacts-to-keep`
  - **Current output roots:**
    - `.repo_studios/reports/healthview/producer_reports/test_coverage_inventory/<YYYYmmdd-HHMM>/`
  - **Current artifacts (observed):**
    - Base package (Tier-1 HealthView contract):
      - `manifest.json` (emitted)
      - `summary.md` (emitted)
      - `telemetry.json` (emitted)
    - Additional artifacts (allowed): none observed.
  - **Retention surface:**
    - `--artifacts-to-keep` forwarded to
      `prune_run_directories(..., keep=..., current_run=bundle_dir, ...)`.

  Pruning:
  - Mechanism: shared-helper
  - Surface: callsite `prune_run_directories(base_dir, keep=..., current_run=bundle_dir, ...)`
  - Target: `--output-dir/producer_reports/test_coverage_inventory/<YYYYmmdd-HHMM>/`
  - Evidence:
    - `.repo_studios/scripts/producers/generate_test_coverage_inventory.py` (`prune_run_directories`)
    - `.repo_studios/tests/tests_producers/test_generate_test_coverage_inventory.py` (prunes history)

  - **Output root compliant (Tier-1 HealthView contract):** ✅
    - Default output root is under `.repo_studios/reports/healthview/...`.
  - **Base package compliant (manifest + summary + telemetry):** ✅
  - **DB integration:** ✅
    - `DB_INTEGRATION_MARKER:` callsites present for manifest/summary/telemetry writes.
  - **Tier-3 appropriate:** yes (decision: create)
  - **Tier-3 YAML exists:** yes
  - **Tier-3 YAML name:** `tier3_generate_test_coverage_inventory.yaml`
  - **Tier-3 meets template:** yes
  - **Tier-3 last updated:** 2025-12-21
  - **Tests:** `.repo_studios/tests/tests_producers/test_generate_test_coverage_inventory.py`
  - **Evidence:**
    - Bundle path: `output_dir / VIEWER_SLUG / TOPIC_SLUG / timestamp_slug`.
    - Artifacts asserted in tests: `manifest.json`, `summary.md`, `telemetry.json`.
    - Threshold failure returns non-zero exit code (still writes the bundle) and prunes historical run dirs.
    - DB marker discipline: manifest/summary/telemetry writes are annotated with `DB_INTEGRATION_MARKER:`.
    - Orchestrator alignment: Stage 1.1 orchestrator now passes `--timestamp`, discovers the positional
      bundle under `.../producer_reports/test_coverage_inventory/<YYYYmmdd-HHMM>/`, and reads
      `telemetry.json` for summary fields.

#### Implementation Workstreams (checkbox-driven) — generate_test_coverage_inventory.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [x] Draft plan to migrate outputs into Tier-1 canonical root
  - Update default output root to `.repo_studios/reports/healthview`.
  - Treat the first path segment after the root as the “class” (`producer_reports`).
  - Update Stage 1.1 orchestrator coverage discovery to use the positional bundle and a stable timestamp.
  - Update tests and satisfy the coverage gate.

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.
  - Implemented output-root + class-slug changes in `generate_test_coverage_inventory.py`.
  - Updated `run_test_execution_telemetry.py` coverage step to pass `--timestamp` and read `telemetry.json`.
  - Updated producer tests to match the new output layout.

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create)
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_generate_test_coverage_inventory.yaml`
- [x] Validate Tier-3 YAML
  - Parsed required sections present; indexed as
    `healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_test_coverage_inventory.yaml`.

Workstream E — QA & Evidence

- [x] Pytest evidence captured
- [x] Mypy evidence captured or marked N/A (in record)
- [x] Coverage ≥80% (or exception recorded)
- [x] Doc-index timestamp recorded
  - Evidence: `.repo_studios/reports/producer_reports/healthview/doc_index/20251222-0124/`
  - Pytest: `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_producers/test_generate_test_coverage_inventory.py -q`
  - Mypy: `.venv/Scripts/python.exe -m mypy .repo_studios/scripts/producers/generate_test_coverage_inventory.py .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py`
  - Coverage: `coverage report --include="*/.repo_studios/scripts/producers/generate_test_coverage_inventory.py" --fail-under=80` (observed: 80%)

- [x] DONE — generate_test_coverage_inventory.py complete; update Tier-1 Stage 1.1 script gate

#### Record — analyze_test_hardening.py

- **Script:** `.repo_studios/scripts/producers/analyze_test_hardening.py`
  - **Role:** Producer
  - **Entry surface:** `run(argv)` and `main(argv)`
  - **Key CLI inputs (selected):**
    - `--repo-root` (override repository root resolution)
    - `--output-dir` (reports root)
    - `--timestamp` (ISO 8601; run slug becomes `YYYYmmdd-HHMM` in UTC)
    - `--artifacts-to-keep`
    - `--log-level`
  - **Current output roots:**
    - `.repo_studios/reports/healthview/producer_reports/test_hardening/<YYYYmmdd-HHMM>/`
  - **Current artifacts (observed):**
    - Base package (Tier-1 HealthView contract):
      - `manifest.json` (emitted)
      - `summary.md` (emitted)
      - `telemetry.json` (emitted)
    - Additional artifacts (allowed): none observed.
  - **Retention surface:**
    - `--artifacts-to-keep` forwarded to `prune_history(...)` →
      `prune_run_directories(..., keep=..., current_run=bundle_dir, ...)`.

  Pruning:
  - Mechanism: shared-helper
  - Surface: callsite `prune_run_directories(topic_dir, keep=..., current_run=bundle_dir, ...)`
  - Target: `--output-dir/producer_reports/test_hardening/<YYYYmmdd-HHMM>/`
  - Evidence:
    - `.repo_studios/scripts/producers/analyze_test_hardening.py` (`prune_history`)
    - `.repo_studios/tests/tests_producers/test_analyze_test_hardening.py`

  - **Output root compliant (Tier-1 HealthView contract):** ✅
    - Default output root is under `.repo_studios/reports/healthview/...`.
  - **Base package compliant (manifest + summary + telemetry):** ✅
  - **DB integration:** ✅
    - `DB_INTEGRATION_MARKER:` callsites present for manifest/summary/telemetry writes.
  - **Tier-3 appropriate:** yes (decision: create)
  - **Tier-3 YAML exists:** yes
  - **Tier-3 YAML name:** `tier3_analyze_test_hardening.yaml`
  - **Tier-3 meets template:** yes (Tier-3 agent pipeline YAML template)
  - **Tier-3 last updated:** 2025-12-22
  - **Tests:** `.repo_studios/tests/tests_producers/test_analyze_test_hardening.py`
  - **Evidence:**
    - Bundle path: `paths.output_dir / VIEWER_SLUG / TOPIC_SLUG / timestamp_slug`.
    - Artifacts asserted in tests: `manifest.json`, `summary.md`, `telemetry.json`.
    - Exit code derived from payload `exit_code` (high severity issues gate).
    - Defaults: `DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/healthview")`,
      `VIEWER_SLUG = "producer_reports"`, `TOPIC_SLUG = "test_hardening"`.
    - Orchestrator wiring:
      `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` defaults
      `--hardening-output-dir` to `.repo_studios/reports/healthview` and passes `--timestamp` into
      this producer for deterministic positional bundles.

#### Implementation Workstreams (checkbox-driven) — analyze_test_hardening.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [x] Draft plan to migrate outputs into Tier-1 canonical root

Plan notes (draft):

- Target output root (Tier-1 HealthView contract): write bundles under
  `.repo_studios/reports/healthview/producer_reports/test_hardening/<YYYYmmdd-HHMM>/`.
- Producer change: update `DEFAULT_OUTPUT_DIR` to `.repo_studios/reports/healthview` and set
  `VIEWER_SLUG="producer_reports"` (keeping `TOPIC_SLUG="test_hardening"`).
- Orchestrator compatibility: update Stage 1.1 orchestrator defaults so
  `--hardening-output-dir` defaults to `.repo_studios/reports/healthview`; pass `--timestamp` into
  the producer so runs are deterministic and discoverable.
- Tests: update `test_analyze_test_hardening.py` to assert the new default output root and bundle
  layout; keep pruning behavior unchanged.

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.
  - Updated `analyze_test_hardening.py` defaults to emit bundles under
    `.repo_studios/reports/healthview/producer_reports/test_hardening/<YYYYmmdd-HHMM>/`.
  - Updated Stage 1.1 orchestrator to default hardening outputs to `.repo_studios/reports/healthview`
    and pass `--timestamp` into the producer.

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create)
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_analyze_test_hardening.yaml`
- [x] Validate Tier-3 YAML
  - Tier-3 YAML evidence (2025-12-22):
    `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_analyze_test_hardening.yaml` validated via
    `.\\.venv/Scripts/python.exe -m pytest -q .repo_studios/docs/pipeline/tier3_index/test_tier3_index.py` (28 passed).

Workstream E — QA & Evidence

- [x] Pytest evidence captured
  - `.\.venv/Scripts/python.exe -m pytest -q .repo_studios/tests/tests_producers/test_analyze_test_hardening.py` (3 passed).
- [x] Mypy evidence captured or marked N/A (in record)
  - `.\.venv/Scripts/python.exe -m mypy .repo_studios/scripts/producers/analyze_test_hardening.py .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` (success).
- [x] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded
  - Coverage:
    `.\.venv/Scripts/python.exe -m coverage report --include="*/.repo_studios/scripts/producers/analyze_test_hardening.py" --fail-under=80` (observed: 88%).
  - Doc-index evidence:
    `make -C .repo_studios doc-index LOG_LEVEL=INFO` (timestamp: 20251222-0250).

- [x] DONE — analyze_test_hardening.py complete; update Tier-1 Stage 1.1 script gate

#### Record — generate_test_log_health_report.py

- **Script:** `.repo_studios/scripts/consumers/generate_test_log_health_report.py`
  - **Role:** Consumer
  - **Entry surface:** `run(argv)` and `main(argv)`
  - **Key CLI inputs (selected):**
    - `--logs-dir` (primary logs search root)
    - `--output-base` (reports root)
    - `--timestamp` (ISO 8601; run slug becomes `YYYYmmdd-HHMM` in UTC)
    - `--producer-bundle-dir` (preferred structured input containing `telemetry.json`)
    - `--producer-reports-root` (fallback search root for producer bundles)
    - `--producer-report` (legacy single-file input)
    - `--artifacts-to-keep`
  - **Current output roots:**
    - `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/<YYYYmmdd-HHMM>/`
  - **Current artifacts (observed):**
    - `report.json` — structured summary payload.
    - `report.md` — human-readable report (includes pass-rate delta + source references).
    - `report.csv` — export of key metrics.
    - `bundle_summary.json` — metadata + provenance + artifact pointers.
  - **Retention surface:**
    - `--artifacts-to-keep` forwarded to `_prune_history(...)` →
      `prune_run_directories(..., keep=..., current_run=out_dir, ...)`.

  Pruning:
  - Mechanism: shared-helper
  - Surface: callsite `prune_run_directories(base, keep=..., current_run=out_dir, ...)`
  - Target: `--output-base/<YYYYmmdd-HHMM>/`
  - Evidence:
    - `.repo_studios/scripts/consumers/generate_test_log_health_report.py` (`_prune_history`)
    - `.repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py` (prunes history)

  - **Output root compliant (Tier-1 HealthView contract):** ✅
    - Default output root is under `.repo_studios/reports/healthview/...`.
  - **Base package compliant (manifest + summary + telemetry):** N/A
    - This consumer emits `report.*` artifacts; it does not emit a HealthView base package.
  - **DB integration:** ❌ (no DB markers observed)
  - **Tier-3 appropriate:** yes (decision: create)
  - **Tier-3 YAML exists:** yes
  - **Tier-3 YAML name:** `tier3_generate_test_log_health_report.yaml`
  - **Tier-3 meets template:** yes
  - **Tier-3 last updated:** 2025-12-21
  - **Tests:** `.repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py`
  - **Evidence:**
    - Prefers structured producer bundle (`telemetry.json`) when provided.
    - Falls back to logs scanning when no producer artifact is available.
    - Writes `bundle_summary.json` including comparisons/pass-rate delta.
    - Tier-3 YAML created + validated (2025-12-21):
      `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_test_log_health_report.yaml`.

#### Implementation Workstreams (checkbox-driven) — generate_test_log_health_report.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings
  - Output directory naming: `--output-base/<YYYYmmdd-HHMM>/` (UTC), via `--timestamp` when
    provided, otherwise `datetime.now(UTC).strftime("%Y%m%d-%H%M")`.
  - Artifacts written per run:
    - `report.json`
    - `report.md` (includes markdownlint MD013 disable comment + “Source References” section)
    - `report.csv`
    - `bundle_summary.json`
  - Producer bundle preference:
    - `--producer-bundle-dir` points at a `collect_test_log_reports` bundle containing
      `telemetry.json`.
    - Fallback selects latest bundle under `--producer-reports-root` when its run directories
      match `YYYYmmdd-HHMM`.
  - Logs fallback: if no producer artifact is found, scans `--logs-dir` (and optionally
    `.repo_studios/pytest_logs` when `TEST_LOG_HEALTH_ALLOW_LEGACY` is enabled).
  - Retention: `_prune_history(...)` calls
    `prune_run_directories(base, keep=..., current_run=out_dir, ...)`.
  - DB integration: no `DB_INTEGRATION_MARKER:` callsites present (as expected for this consumer).

Workstream B — Plan

- [x] Draft plan to migrate outputs into Tier-1 canonical root

Plan notes (draft):

- Target output root (Tier-1 HealthView contract): write consumer runs under
  `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/<YYYYmmdd-HHMM>/`.
- Consumer change:
  - Update `OUTPUT_BASE_DEFAULT` to
    `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports`.
  - Add `--timestamp` (ISO 8601, optional) so the consumer can use the orchestrator run timestamp
    for its run directory slug (`YYYYmmdd-HHMM`, UTC).
  - Preserve `--output-base` semantics (base directory that receives timestamped run directories).
- Orchestrator compatibility:
  - Update Stage 1.1 orchestrator default `--test-log-health-dir` to
    `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports`.
  - Pass `--timestamp options.run_timestamp.isoformat()` into the consumer so run-dir naming is
    deterministic and aligned to the rest of the Stage 1.1 chain.
- Tests:
  - Update `.repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py` to pass a
    fixed `--timestamp` and assert the output run dir is the expected `YYYYmmdd-HHMM`.
  - Update orchestrator integration tests to match the new default output root and deterministic
    output run dir.

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.
  - Updated `generate_test_log_health_report.py` default output base to emit runs under
    `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/<YYYYmmdd-HHMM>/`.
  - Added `--timestamp` (ISO 8601) so Stage 1.1 orchestrator can enforce deterministic run slugs.
  - Updated Stage 1.1 orchestrator to default `--test-log-health-dir` under
    `.repo_studios/reports/healthview/...` and pass `--timestamp` into this consumer.
  - Updated consumer + orchestrator tests to match the new output root + slug semantics.

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create)
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_generate_test_log_health_report.yaml`
- [x] Validate Tier-3 YAML
  - Tier-3 YAML evidence (2025-12-21):
    `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_test_log_health_report.yaml` validated via
    `\.\.venv/Scripts/python.exe .repo_studios/docs/pipeline/tier3_index/generate_tier3_index.py --repo-root . --validate` and
    `\.\.venv/Scripts/python.exe -m pytest -q .repo_studios/docs/pipeline/tier3_index/test_tier3_index.py` (29 passed).

Workstream E — QA & Evidence

- [x] Pytest evidence captured
  - `./.venv/Scripts/python.exe -m pytest -q .repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py` (8 passed).
  - `./.venv/Scripts/python.exe -m pytest -q .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py` (2 passed).
- [x] Mypy evidence captured or marked N/A (in record)
  - `./.venv/Scripts/python.exe -m mypy .repo_studios/scripts/consumers/generate_test_log_health_report.py .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` (success).
- [x] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded
  - Coverage:
    `./.venv/Scripts/python.exe -m coverage report --include="*/.repo_studios/scripts/consumers/generate_test_log_health_report.py" --fail-under=80` (observed: 80%; pass).
  - Doc-index evidence:
    `make -C .repo_studios doc-index LOG_LEVEL=INFO` (timestamp: 20251222-0450).

- [x] DONE — generate_test_log_health_report.py complete; update Tier-1 Stage 1.1 script gate

#### Record — generate_churn_complexity_heatmap.py

- **Script:** `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py`
  - **Role:** Aggregator
  - **Entry surface:** `run(argv)` and `main(argv)`
  - **Key CLI inputs (selected):**
    - `--repo-root` (repo root for churn/complexity scan)
    - `--metrics-source` (optional precomputed metrics)
    - `--test-log-summary` (optional consumer bundle summary)
    - `--logs-dir` (fallback when consumer summary missing)
    - `--output-base`
    - `--window` (git commit window)
    - `--artifacts-to-keep`
  - **Current output roots:**
    - `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/churn_complexity_heatmap-<YYYY-MM-DD_HHMMSS>/`
  - **Current artifacts (observed):**
    - `heatmap.json` — scored metrics.
    - `heatmap.md` — human-readable report.
    - `bundle_summary.json` — metadata + artifact pointers.
  - **Retention surface:**
    - `--artifacts-to-keep` forwarded to `_prune_history(...)` →
      `prune_run_directories(..., keep=..., stem_prefix=RUN_PREFIX, current_run=run_dir, ...)`.

  Pruning:
  - Mechanism: shared-helper
  - Surface: callsite `prune_run_directories(base, keep=..., stem_prefix=RUN_PREFIX,`
    `current_run=run_dir, ...)`
  - Target: `--output-base/churn_complexity_heatmap-<YYYY-MM-DD_HHMMSS>/`
  - Evidence:
    - `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py` (`_prune_history`)
    - `.repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py` (prunes history)

  - **Output root compliant (Tier-1 HealthView contract):** ❌
    - Default output root is now under `.repo_studios/reports/healthview/aggregator_reports/...`,
      but this vertical still requires end-to-end Stage 1.1 contract alignment.
  - **Base package compliant (manifest + summary + telemetry):** N/A
    - This aggregator emits `heatmap.*` artifacts; it does not emit a HealthView base package.
  - **DB integration:** ❌ (no DB markers observed)
  - **Tier-3 appropriate:** yes (decision: create)
  - **Tier-3 YAML exists:** yes
  - **Tier-3 YAML name:** `tier3_generate_churn_complexity_heatmap.yaml`
  - **Tier-3 meets template:** yes (Tier-3 agent pipeline YAML template)
  - **Tier-3 last updated:** 2025-12-24
  - **Tests:** `.repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py`
  - **Evidence:**
    - Prefers consumer bundle summary when present; falls back to logs/JUnit discovery.
    - No `latest_*` pointer artifacts are written (Tier-1 compliant).
    - Retention prunes old run directories with `stem_prefix=RUN_PREFIX`.

#### Implementation Workstreams (checkbox-driven) — generate_churn_complexity_heatmap.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings
  - Output root default updated to `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap`.
  - Pointer artifacts removed: no `latest_*` files are written.
  - Default `--test-log-summary` no longer points at a `latest/...` path; directory discovery is used.
  - Pytest (evidence):
    `./.venv/Scripts/python.exe -m pytest -q .repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py` (6 passed).

Workstream B — Plan

- [x] Draft plan to remove pointer artifacts and migrate outputs
  - Remove `_update_latest(...)` and all `latest_*` writes.
  - Migrate default output root under `.repo_studios/reports/healthview/aggregator_reports/...`.
  - Update tests to stop asserting `latest_*` artifacts.

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.
  - Updated `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py`.
  - Updated `.repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py`.

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
  - Decision: create Tier-3 YAML (align with other Stage 1.1 scripts).
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_generate_churn_complexity_heatmap.yaml`
  - Created: `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_churn_complexity_heatmap.yaml`.
- [x] Validate Tier-3 YAML
  - `./.venv/Scripts/python.exe .repo_studios/docs/pipeline/tier3_index/generate_tier3_index.py --repo-root . --validate` (2025-12-24).
  - `./.venv/Scripts/python.exe -m pytest -q .repo_studios/docs/pipeline/tier3_index/test_tier3_index.py` (2025-12-24).

Workstream E — QA & Evidence

- [x] Pytest evidence captured
  - `./.venv/Scripts/python.exe -m pytest -q .repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py` (6 passed).
- [x] Mypy evidence captured or marked N/A (in record)
  - `./.venv/Scripts/python.exe -m mypy .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py` (success).
- [x] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded
  - Coverage:
    `./.venv/Scripts/python.exe -m coverage run -m pytest -q .repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py`
    then
    `./.venv/Scripts/python.exe -m coverage report --include="*/.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py" --fail-under=80` (observed: 81%; pass).
  - Doc-index evidence:
    `make -C .repo_studios doc-index LOG_LEVEL=INFO` (timestamp: 20251224-2030).
    Output: `.repo_studios/reports/producer_reports/healthview/doc_index/20251224-2030/doc_index.csv`.

- [x] DONE — generate_churn_complexity_heatmap.py complete; update Tier-1 Stage 1.1 script gate

#### Record — summarize_test_execution_telemetry.py

- **Script:** `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py`
  - **Role:** Summarizer
  - **Entry surface:** `run(argv)` and `main(argv)`
  - **Key CLI inputs (selected):**
    - `--manifest` (path to `manifest.json`)
    - `--telemetry` (path to `telemetry.json`)
    - `--output-dir` (default: `.repo_studios/reports/healthview`)
    - `--artifacts-to-keep` (retention for summary artifacts)
  - **Current output roots:**
    - `.repo_studios/reports/healthview/summarizer_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/`
  - **Current artifacts (observed):**
    - Base package (Tier-1 HealthView contract): N/A (this script emits additional artifacts).
    - Additional artifacts (allowed):
      - `test_execution_telemetry_summary.md` — additional summary markdown.
      - `test_execution_telemetry_summary.json` — additional summary JSON.
  - **Retention surface:** `--artifacts-to-keep` forwarded to `write_report_artifacts(..., keep=...)`.

  Pruning:
  - Mechanism: shared-helper
  - Surface: callsite `write_report_artifacts(..., keep=options.artifacts_to_keep, current_run=<run_dir>)`
  - Target: `--output-dir/summarizer_reports/test_execution_telemetry/<run_slug>/`
  - Evidence:
    - `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py` (`write_report_artifacts`)
    - `.repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py`

  - **Output root compliant (Tier-1 HealthView contract):** ✅
    - Default output dir is `.repo_studios/reports/healthview` and uses the `summarizer_reports` class token.
  - **Base package compliant (manifest + summary + telemetry):** N/A
  - **DB integration:** ❌ (no DB markers observed in this summarizer)
  - **Tier-3 appropriate:** yes (decision: create)
  - **Tier-3 YAML exists:** yes
  - **Tier-3 YAML name:** `tier3_summarize_test_execution_telemetry.yaml`
  - **Tier-3 meets template:** yes (Tier-3 agent pipeline YAML template)
  - **Tier-3 last updated:** 2025-12-24
  - **Tests:** `.repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py`
  - **Evidence:**
    - Constants: `SUMMARY_STEM = "test_execution_telemetry_summary"`, `VIEWER_SLUG = "summarizer_reports"`,
      `TOPIC_SLUG = "test_execution_telemetry"`.
    - Artifacts written via `write_report_artifacts(...)` using filenames
      `f"{SUMMARY_STEM}.md"` and `f"{SUMMARY_STEM}.json"`.

#### Implementation Workstreams (checkbox-driven) — summarize_test_execution_telemetry.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings
  - Script defaults:
    - `DEFAULT_OUTPUT_DIR = .repo_studios/reports/healthview`.
    - `VIEWER_SLUG = "summarizer_reports"`, `TOPIC_SLUG = "test_execution_telemetry"`.
  - Output layout is controlled by `write_report_artifacts(...)`:
    - Callsite passes `output_dir=<--output-dir>`, `viewer=VIEWER_SLUG`, `topic=TOPIC_SLUG`, `timestamp=<run_slug>`.
    - Resulting run directory is under `--output-dir/<viewer>/<topic>/<timestamp>/`.
  - Artifacts written per run:
    - `test_execution_telemetry_summary.json`
    - `test_execution_telemetry_summary.md`
  - Retention surface:
    - `--artifacts-to-keep` forwarded to `write_report_artifacts(..., keep=...)`.
  - Current compliance status (Stage 1.1 HOP contract): ✅
    - Defaults emit under `.repo_studios/reports/healthview/summarizer_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/`.

Workstream B — Plan

- [x] Draft plan to migrate outputs into Tier-1 canonical root
  - Target output root (Stage 1.1 HOP contract):
    - `.repo_studios/reports/healthview/summarizer_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/`
  - Summarizer changes:
    - Change `VIEWER_SLUG` to `"summarizer_reports"` (class token).
    - Keep `TOPIC_SLUG = "test_execution_telemetry"`.
    - Change `DEFAULT_OUTPUT_DIR` to `.repo_studios/reports/healthview`.
  - Orchestrator compatibility:
    - Update Stage 1.1 orchestrator to pass `--output-dir .repo_studios/reports/healthview` into this summarizer so the run lands in the canonical HealthView root.
    - Ensure it passes the Stage 1.1 run timestamp consistently (manifest/telemetry already carry run slug).
  - Tests:
    - Update `.repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py` to assert the new default class/topic tokens and/or updated output root when `--output-dir` points at `.repo_studios/reports/healthview`.
    - Update the fixture hardening artifact path to match the current Stage 1.1 producer output layout (post-migration) when required.

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.
  - Updated `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py`:
    - Default output root moved to `.repo_studios/reports/healthview`.
    - Class token set via `VIEWER_SLUG = "summarizer_reports"`.
  - Updated Stage 1.1 orchestrator `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` to pass the canonical HealthView root into the summarizer (`--output-dir` wired to `--test-log-reports-dir`).
  - Updated tests to assert the new summary artifact paths + viewer token.

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
  - Decision: create Tier-3 YAML (align with other Stage 1.1 scripts).
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_summarize_test_execution_telemetry.yaml`
  - Created: `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_summarize_test_execution_telemetry.yaml`.
- [x] Validate Tier-3 YAML
  - `./.venv/Scripts/python.exe .repo_studios/docs/pipeline/tier3_index/generate_tier3_index.py --repo-root . --validate` (2025-12-24).
  - `./.venv/Scripts/python.exe -m pytest -q .repo_studios/docs/pipeline/tier3_index/test_tier3_index.py` (2025-12-24; 29 passed).

Workstream E — QA & Evidence

- [x] Pytest evidence captured
  - `./.venv/Scripts/python.exe -m pytest -q .repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py` (3 passed).
- [x] Mypy evidence captured or marked N/A (in record)
  - `./.venv/Scripts/python.exe -m mypy .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` (success).
- [x] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded
  - Coverage:
    `./.venv/Scripts/python.exe -m coverage run -m pytest -q .repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`
    then
    `./.venv/Scripts/python.exe -m coverage report --include="*/.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py" --fail-under=80` (observed: 93%; pass).
  - Doc-index evidence:
    `make -C .repo_studios doc-index LOG_LEVEL=INFO` (timestamp: 20251224-2314).
    Output: `.repo_studios/reports/producer_reports/healthview/doc_index/20251224-2314/doc_index.csv`.

- [x] DONE — summarize_test_execution_telemetry.py complete; update Tier-1 Stage 1.1 script gate

#### Stage 1.1 Chain Records (Quick Links) — Placeholder Index (Not a Record)

The chain records below must be promoted into full ScriptInspectionRecordV1 entries before Stage
1.1 code migrations rely on this doc as the single source of truth.

**Non-record placeholder index (do not copy forward as an inspection record).**

- None remaining (as of 2025-12-19).
  - If the Stage 1.1 chain adds a new delegated script, add it here first as a placeholder, then
    promote it into a full ScriptInspectionRecordV1 record above once evidence is collected.

### 3.2 Stop-Gates

**Stage 1.1 Tier-2 authoring stop-gates (docs-first):**

- [ ] Confirm the canonical `<class>/<topic>` tokens for Stage 1.1 under
  `.repo_studios/reports/healthview/`.
- [ ] Confirm the canonical `<timestamp>` formatting expectation and record it here (do not assume
  `YYYY-MM-DD` or `YYYYmmdd-HHmm` without evidence and an explicit decision).

**Stage 1.1 Tier-1 contract migration stop-gates (code-phase, later):**

- [ ] Output root migrated to `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- [ ] Base package required: `manifest.json`, `summary.md`, `telemetry.json` (current: Stage 1.1
  orchestrator bundle is missing `summary.md`).
- [ ] Additional artifacts (if any) are listed with a short, factual reason.
- [ ] No pointer files remain (current: `generate_churn_complexity_heatmap.py` writes
  `latest_*`).
- [ ] Retention behavior verified via pruning mechanism + evidence.
- [ ] If DB writes are added: gate behind `REPO_STUDIOS_DB_ENABLED`, warn-only failures, and include
  `DB_INTEGRATION_MARKER:` at each callsite.
- [ ] Update Tier-1 Stage 1.1 and close contradiction entries as they are resolved.

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

- **Tier-1 stop-gates blocked by this doc:**
  - Stage 1.1 migration cannot be considered Tier-1 HealthView contract compliant until the base
    package and output root contradictions are resolved.

- **Tier-3 YAML required (placeholders until created):**
  - `tier3_cli.yaml`
  - `tier3_prune_logs.yaml`
  - `tier3_artifacts.yaml`
  - `tier3_database_integration.yaml`

- **Feature flags:**
  - `REPO_STUDIOS_DB_ENABLED` (DB dual-write toggle)

---

## 6. Instruction Block (Required by Tier Rules)

This section exists to satisfy Tier-rule “Instruction Block” placement requirements.

Canonical instructions live in Section 0: “Instruction Block for Editors & AI Assistants”.

---

## 7. Agent Automation Block

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
    title: Verify chain inventory includes 6 delegated scripts
    severity: error
  - id: hv-stage1-1-stopgates
    title: Stop-gates include output root + base package requirement
    severity: error
```
<!-- agents:end:healthview_stage1_1_roster -->

---

## 8. Decision Log

- 2025-12-19 — Section 3.1 is the authoritative Stage 1.1 script inventory for agents.
  Assertions must carry evidence or be logged as a stop-gate.
- 2025-12-19 — The Section 3.1 fixture example is permanent and must not be deleted; it serves as a
  formatting + completeness reference for future per-script records.
- 2025-12-19 — Extra per-run artifacts emitted by the current Stage 1.1 summarizer are treated as a
  allowed but must be listed with a short, factual reason.
- 2025-12-19 — The missing base package artifact `summary.md` is treated as a stop-gate against the
  Tier-1 HealthView contract until resolved in Tier-1 decisions.
- 2025-12-25 — Closed the `summary.md` stop-gate for the Stage 1.1 orchestrator base package and
  migrated the default output root to the canonical HealthView location.

---

## 9. Update Log

|Date|Change|Author|Doc-index timestamp|Regression suites|
|---|---|---|---|---|
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
