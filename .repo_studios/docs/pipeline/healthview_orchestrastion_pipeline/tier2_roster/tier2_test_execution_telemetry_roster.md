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
updated_at: 2025-12-19
tags:
  - pipeline
  - healthview
  - stage-1
  - test-execution-telemetry
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier1_healthview_orchestration_pipeline.md
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
- **Tier-3 dependencies (placeholders):**
  - Tier-3 placeholder — `tier3_cli.yaml` (shared CLI builders)
  - Tier-3 placeholder — `tier3_prune_logs.yaml` (retention + current_run protection)
  - Tier-3 placeholder — `tier3_artifacts.yaml` (base package contract + discovery semantics)
  - Tier-3 placeholder — `tier3_database_integration.yaml` (DB dual-write semantics + schema)

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

- Output root currently defaults under:
  `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<run_slug>/`
  via `--healthview-root` default.
- Timestamp/run slug shape observed in tests: `YYYYmmdd-HHmm` (example: `20251201-0101`).
- Base package completeness mismatch (current evidence):
  - `manifest.json` is emitted.
  - `telemetry.json` is emitted.
  - `summary.md` is not emitted by the current Stage 1.1 chain.
- Additional artifacts currently emitted:
  - `test_execution_telemetry_summary.md` (summary markdown)
  - `test_execution_telemetry_summary.json` (summary JSON)

This mismatch is a stop-gate for any Stage 1.1 contract migration work.

---

## 3. Stage Narrative — Stage 1.1 Test Execution Telemetry

### 3.1 Per-Script Inspection Table (v1)

This section uses a bullet layout (not a wide markdown table) to keep line length ≤100 and improve
scanability.

Agents must treat this section as the authoritative script inventory for Stage 1.1.

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
    - `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<YYYYmmdd-HHMM>/`
  - **Current artifacts (observed):**
    - Base package (Tier-1 HealthView contract):
      - `manifest.json` (emitted)
      - `summary.md` (not emitted)
      - `telemetry.json` (emitted)
    - Additional artifacts (allowed) written by summarizer:
      - `test_execution_telemetry_summary.md` — additional summary markdown.
      - `test_execution_telemetry_summary.json` — additional summary JSON.
  - **Retention surface:** `--artifacts-to-keep` forwarded to `write_report_artifacts()`.

  Pruning:
  - Mechanism: shared-helper
  - Surface: callsite `write_report_artifacts(..., keep=options.artifacts_to_keep, current_run=<run_dir>)`
  - Target: `--healthview-root/healthview/test_execution_telemetry/<YYYYmmdd-HHMM>/`
  - Evidence: `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` (`write_report_artifacts`)

  - **Output root compliant (Tier-1 HealthView contract):** ❌
  - **Base package compliant (manifest + summary + telemetry):** ❌
  - **DB integration:** ❌ (no direct DB callsites observed)
    - Delegated scripts include DB integration markers and/or storage writers.
  - **Tier-3 allowed:** no (until refactor standards are met)
  - **Tier-3 YAML exists:** no
  - **Tier-3 YAML name:** `tier3_run_test_execution_telemetry.yaml`
  - **Tier-3 meets template:** NA
  - **Tier-3 last updated:** —
  - **Tests:** `.repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`
  - **Evidence:**
    - Run slug derived from `options.run_timestamp.strftime("%Y%m%d-%H%M")`.
    - Manifest + telemetry written via `write_report_artifacts(stem=HEALTHVIEW_TOPIC, ...)`.
    - Summarizer invoked with `--manifest`, `--telemetry`, `--output-dir`, and `--artifacts-to-keep`.
  - **Notes:**
    - Output-root + base-package mismatches are stop-gates for Tier-1 HealthView contract
      compliance.

#### Implementation Workstreams (checkbox-driven) — run_test_execution_telemetry.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_run_test_execution_telemetry.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — run_test_execution_telemetry.py complete; update Tier-1 Stage 1.1 script gate

#### Record — collect_test_log_reports.py

- **Script:** `.repo_studios/scripts/producers/collect_test_log_reports.py`
  - **Role:** Producer
  - **Entry surface:** `run(argv)` and `main(argv)`
  - **Key CLI inputs (selected):**
    - `--logs-dir` (default: `.repo_studios/command_center/reports/rawview/test_execution_runs`)
    - `--logs-run` (optional explicit run directory)
    - `--output-dir` (default: `.repo_studios/command_center/reports`)
    - `--run-timestamp` (UTC slug in `YYYYMMDD-HHMM`)
    - `--artifacts-to-keep`
  - **Current output roots:**
    - `.repo_studios/command_center/reports/rawview/test_log_reports/<YYYYmmdd-HHMM>/`
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

  - **Output root compliant (Tier-1 HealthView contract):** ❌
    - Default output root is under `.repo_studios/command_center/reports/rawview/...`.
  - **Base package compliant (manifest + summary + telemetry):** ✅
  - **DB integration:** ✅
    - `DB_INTEGRATION_MARKER:` callsites present for manifest/summary/telemetry writes.
  - **Tier-3 allowed:** no (until refactor standards are met)
  - **Tier-3 YAML exists:** no
  - **Tier-3 YAML name:** `tier3_collect_test_log_reports.yaml`
  - **Tier-3 meets template:** NA
  - **Tier-3 last updated:** —
  - **Tests:** `.repo_studios/tests/tests_producers/test_collect_test_log_reports.py`
  - **Evidence:**
    - Defaults: `DEFAULT_OUTPUT_DIR = Path(".repo_studios/command_center/reports")`,
      `VIEWER_SLUG = "rawview"`, `TOPIC_SLUG = "test_log_reports"`.
    - Bundle paths: `bundle_dir = output_dir / VIEWER_SLUG / TOPIC_SLUG / timestamp`.
    - Artifact filenames: `manifest.json`, `summary.md`, `telemetry.json`.

#### Implementation Workstreams (checkbox-driven) — collect_test_log_reports.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to migrate outputs into Tier-1 canonical root

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_collect_test_log_reports.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — collect_test_log_reports.py complete; update Tier-1 Stage 1.1 script gate

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
    - `.repo_studios/reports/producer_reports/healthview/test_coverage_inventory/<YYYYmmdd-HHMM>/`
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
  - Target: `--output-dir/healthview/test_coverage_inventory/<YYYYmmdd-HHMM>/`
  - Evidence:
    - `.repo_studios/scripts/producers/generate_test_coverage_inventory.py` (`prune_run_directories`)
    - `.repo_studios/tests/tests_producers/test_generate_test_coverage_inventory.py` (prunes history)

  - **Output root compliant (Tier-1 HealthView contract):** ❌
    - Default output root is under `.repo_studios/reports/producer_reports/healthview/...`.
  - **Base package compliant (manifest + summary + telemetry):** ✅
  - **DB integration:** ✅
    - `DB_INTEGRATION_MARKER:` callsites present for manifest/summary/telemetry writes.
  - **Tier-3 allowed:** no (until refactor standards are met)
  - **Tier-3 YAML exists:** no
  - **Tier-3 YAML name:** `tier3_generate_test_coverage_inventory.yaml`
  - **Tier-3 meets template:** NA
  - **Tier-3 last updated:** —
  - **Tests:** `.repo_studios/tests/tests_producers/test_generate_test_coverage_inventory.py`
  - **Evidence:**
    - Bundle path: `output_dir / VIEWER_SLUG / TOPIC_SLUG / timestamp_slug`.
    - Artifacts asserted in tests: `manifest.json`, `summary.md`, `telemetry.json`.
    - Threshold failure returns non-zero exit code and prunes historical run dirs.

#### Implementation Workstreams (checkbox-driven) — generate_test_coverage_inventory.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to migrate outputs into Tier-1 canonical root

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_test_coverage_inventory.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — generate_test_coverage_inventory.py complete; update Tier-1 Stage 1.1 script gate

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
    - `.repo_studios/command_center/reports/healthview/test_hardening/<YYYYmmdd-HHMM>/`
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
  - Target: `--output-dir/healthview/test_hardening/<YYYYmmdd-HHMM>/`
  - Evidence:
    - `.repo_studios/scripts/producers/analyze_test_hardening.py` (`prune_history`)
    - `.repo_studios/tests/tests_producers/test_analyze_test_hardening.py`

  - **Output root compliant (Tier-1 HealthView contract):** ❌
    - Default output root is under `.repo_studios/command_center/reports/healthview/...`.
  - **Base package compliant (manifest + summary + telemetry):** ✅
  - **DB integration:** ✅
    - `DB_INTEGRATION_MARKER:` callsites present for manifest/summary/telemetry writes.
  - **Tier-3 allowed:** no (until refactor standards are met)
  - **Tier-3 YAML exists:** no
  - **Tier-3 YAML name:** `tier3_analyze_test_hardening.yaml`
  - **Tier-3 meets template:** NA
  - **Tier-3 last updated:** —
  - **Tests:** `.repo_studios/tests/tests_producers/test_analyze_test_hardening.py`
  - **Evidence:**
    - Bundle path: `paths.output_dir / VIEWER_SLUG / TOPIC_SLUG / timestamp_slug`.
    - Artifacts asserted in tests: `manifest.json`, `summary.md`, `telemetry.json`.
    - Exit code derived from payload `exit_code` (high severity issues gate).

#### Implementation Workstreams (checkbox-driven) — analyze_test_hardening.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to migrate outputs into Tier-1 canonical root

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_analyze_test_hardening.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — analyze_test_hardening.py complete; update Tier-1 Stage 1.1 script gate

#### Record — generate_test_log_health_report.py

- **Script:** `.repo_studios/scripts/consumers/generate_test_log_health_report.py`
  - **Role:** Consumer
  - **Entry surface:** `run(argv)` and `main(argv)`
  - **Key CLI inputs (selected):**
    - `--logs-dir` (primary logs search root)
    - `--output-base` (reports root)
    - `--producer-bundle-dir` (preferred structured input containing `telemetry.json`)
    - `--producer-reports-root` (fallback search root for producer bundles)
    - `--producer-report` (legacy single-file input)
    - `--artifacts-to-keep`
  - **Current output roots:**
    - `.repo_studios/reports/consumer_reports/test_log_health_reports/<YYYY-MM-DD_HHMM>/`
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
  - Target: `--output-base/<YYYY-MM-DD_HHMM>/`
  - Evidence:
    - `.repo_studios/scripts/consumers/generate_test_log_health_report.py` (`_prune_history`)
    - `.repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py` (prunes history)

  - **Output root compliant (Tier-1 HealthView contract):** ❌
    - Default output root is under `.repo_studios/reports/consumer_reports/...`.
  - **Base package compliant (manifest + summary + telemetry):** N/A
    - This consumer emits `report.*` artifacts; it does not emit a HealthView base package.
  - **DB integration:** ❌ (no DB markers observed)
  - **Tier-3 allowed:** no (until refactor standards are met)
  - **Tier-3 YAML exists:** no
  - **Tier-3 YAML name:** `tier3_generate_test_log_health_report.yaml`
  - **Tier-3 meets template:** NA
  - **Tier-3 last updated:** —
  - **Tests:** `.repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py`
  - **Evidence:**
    - Prefers structured producer bundle (`telemetry.json`) when provided.
    - Falls back to logs scanning when no producer artifact is available.
    - Writes `bundle_summary.json` including comparisons/pass-rate delta.

#### Implementation Workstreams (checkbox-driven) — generate_test_log_health_report.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to migrate outputs into Tier-1 canonical root

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_test_log_health_report.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — generate_test_log_health_report.py complete; update Tier-1 Stage 1.1 script gate

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
    - `.repo_studios/reports/aggregator_reports/churn_complexity_heatmap/churn_complexity_heatmap-<YYYY-MM-DD_HHMMSS>/`
  - **Current artifacts (observed):**
    - `heatmap.json` — scored metrics.
    - `heatmap.md` — human-readable report.
    - `bundle_summary.json` — metadata + artifact pointers.
    - `latest_heatmap.json`, `latest_heatmap.md`, `latest_bundle_summary.json` — pointer artifacts.
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
    - Default output root is under `.repo_studios/reports/aggregator_reports/...`.
  - **Base package compliant (manifest + summary + telemetry):** N/A
    - This aggregator emits `heatmap.*` artifacts; it does not emit a HealthView base package.
  - **DB integration:** ❌ (no DB markers observed)
  - **Tier-3 allowed:** no (until refactor standards are met)
  - **Tier-3 YAML exists:** no
  - **Tier-3 YAML name:** `tier3_generate_churn_complexity_heatmap.yaml`
  - **Tier-3 meets template:** NA
  - **Tier-3 last updated:** —
  - **Tests:** `.repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py`
  - **Evidence:**
    - Prefers consumer bundle summary when present; falls back to logs/JUnit discovery.
    - Writes `latest_*` pointer artifacts (contradiction with Tier-1 “no pointer files”).
    - Retention prunes old run directories with `stem_prefix=RUN_PREFIX`.

#### Implementation Workstreams (checkbox-driven) — generate_churn_complexity_heatmap.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to remove pointer artifacts and migrate outputs

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_churn_complexity_heatmap.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — generate_churn_complexity_heatmap.py complete; update Tier-1 Stage 1.1 script gate

#### Record — summarize_test_execution_telemetry.py

- **Script:** `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py`
  - **Role:** Summarizer
  - **Entry surface:** `run(argv)` and `main(argv)`
  - **Key CLI inputs (selected):**
    - `--manifest` (path to `manifest.json`)
    - `--telemetry` (path to `telemetry.json`)
    - `--output-dir` (default: `.repo_studios/command_center/reports`)
    - `--artifacts-to-keep` (retention for summary artifacts)
  - **Current output roots:**
    - `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<YYYYmmdd-HHMM>/`
  - **Current artifacts (observed):**
    - Base package (Tier-1 HealthView contract): N/A (this script emits additional artifacts).
    - Additional artifacts (allowed):
      - `test_execution_telemetry_summary.md` — additional summary markdown.
      - `test_execution_telemetry_summary.json` — additional summary JSON.
  - **Retention surface:** `--artifacts-to-keep` forwarded to `write_report_artifacts(..., keep=...)`.

  Pruning:
  - Mechanism: shared-helper
  - Surface: callsite `write_report_artifacts(..., keep=options.artifacts_to_keep, current_run=<run_dir>)`
  - Target: `--output-dir/healthview/test_execution_telemetry/<run_slug>/`
  - Evidence:
    - `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py` (`write_report_artifacts`)
    - `.repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py`

  - **Output root compliant (Tier-1 HealthView contract):** ❌
    - Default output dir is `.repo_studios/command_center/reports`.
  - **Base package compliant (manifest + summary + telemetry):** N/A
  - **DB integration:** ❌ (no DB markers observed in this summarizer)
  - **Tier-3 allowed:** no (until refactor standards are met)
  - **Tier-3 YAML exists:** no
  - **Tier-3 YAML name:** `tier3_summarize_test_execution_telemetry.yaml`
  - **Tier-3 meets template:** NA
  - **Tier-3 last updated:** —
  - **Tests:** `.repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py`
  - **Evidence:**
    - Constants: `SUMMARY_STEM = "test_execution_telemetry_summary"`, `VIEWER_SLUG = "healthview"`,
      `TOPIC_SLUG = "test_execution_telemetry"`.
    - Artifacts written via `write_report_artifacts(...)` using filenames
      `f"{SUMMARY_STEM}.md"` and `f"{SUMMARY_STEM}.json"`.

#### Implementation Workstreams (checkbox-driven) — summarize_test_execution_telemetry.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to migrate outputs into Tier-1 canonical root

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_summarize_test_execution_telemetry.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — summarize_test_execution_telemetry.py complete; update Tier-1 Stage 1.1 script gate

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

---

## 9. Update Log

|Date|Change|Author|Doc-index timestamp|Regression suites|
|---|---|---|---|---|
|2025-12-19|Expanded Stage 1.1 placeholders into full records.|repo_ai|—|—|
|2025-12-19|Added schema + fixture + Decision Log.|repo_ai|—|—|
|2025-12-19|Correct doc-index command + evidence.|repo_ai|20251219-1058|doc-index|
|2025-12-18|Drafted Stage 1.1 roster doc.|repo_studios_ai|20251219-1058|mdlint; doc-index|
