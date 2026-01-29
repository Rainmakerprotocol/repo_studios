---
title: "Script Build Template — run_test_execution_telemetry.py"
tier: working-document
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - build-template
  - phase-4-artifact
status: complete
version: 1.0.0
updated_at: 2026-01-29
tags:
  - stage-1.1
  - orchestrator
  - phase-4
  - TER-001
related_files:
  - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_run_test_execution_telemetry.yaml
  - .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py
---

<!-- markdownlint-disable-next-line MD025 -->
# Script Build Template — run_test_execution_telemetry.py

> **Purpose:** Working document for Phase 4 per-script processing of TER-001.
> This template will evolve as the script is inspected, modified, documented, and tested.
> Upon completion, content transfers to Tier-2 and this doc is archived with `status: archived`.
>
> **Record ID:** TER-001
> **Status:** `complete`
> **Created:** 2026-01-29
> **Completed:** 2026-01-29
>
> **Universal Law:** Every script in the HealthView pipeline SHALL be orchestration-ready,
> agent-discoverable via Tier-3 YAML, and database-integration prepared — regardless of
> whether it is currently assigned to an orchestrator.

---

## 1. Script Identity

| Field | Value |
|-------|-------|
| **Name** | `run_test_execution_telemetry.py` |
| **Path** | `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` |
| **Tier Class** | Orchestrator |
| **Compliance Tier** | A (Report Generator) |
| **Lines** | 1897 |
| **Record ID** | TER-001 |
| **Planned Stage** | Stage 1.1 |

**Compliance Tier Definitions:**

1. **Tier A (Report Generator):** Produces HOP bundles (manifest/summary/telemetry). Includes
   Producers, Consumers, Aggregators, Summarizers, and Orchestrators.
1. **Tier B (Action Utility):** Performs actions without HOP bundles. Includes Utilities,
   Configurators, Diagnostics, Libraries.

### 1.1 Purpose

Topic orchestrator for Test Execution Telemetry (Stage 1.1). Chains log collection, coverage
inventory, churn heatmap, hardening analysis, and health report summarizer into a unified pipeline.
Emits HealthView bundles under canonical orchestrator output path.

### 1.2 Current Capabilities

1. Chains 5 delegated scripts via `_load_run_callable()` dynamic imports
1. Collects pytest telemetry artifacts (logs, coverage, junit)
1. Runs hardening analysis and churn × complexity heatmap
1. Generates health report summary from consumer bundle
1. Emits base package (manifest.json, summary.md, telemetry.json)
1. Tracks child script outcomes with per-step timing
1. Supports per-script retention overrides via CLI flags
1. Uses topic pipeline framework for step orchestration

---

## 2. Current State Analysis

### 2.1 CLI Interface

```text
usage: run_test_execution_telemetry.py [-h] [--repo-root REPO_ROOT]
       [--logs-dir LOGS_DIR] [--test-log-reports-dir TEST_LOG_REPORTS_DIR]
       [--test-log-health-dir TEST_LOG_HEALTH_DIR]
       [--test-coverage-output-dir TEST_COVERAGE_OUTPUT_DIR]
       [--test-coverage-xml TEST_COVERAGE_XML]
       [--heatmap-output-dir HEATMAP_OUTPUT_DIR]
       [--heatmap-metrics-source HEATMAP_METRICS_SOURCE]
       [--heatmap-window HEATMAP_WINDOW]
       [--hardening-output-dir HARDENING_OUTPUT_DIR]
       [--healthview-root HEALTHVIEW_ROOT]
       [--artifacts-to-keep ARTIFACTS_TO_KEEP]
       [--collector-artifacts-to-keep COLLECTOR_ARTIFACTS_TO_KEEP]
       [--health-artifacts-to-keep HEALTH_ARTIFACTS_TO_KEEP]
       [--coverage-artifacts-to-keep COVERAGE_ARTIFACTS_TO_KEEP]
       [--heatmap-artifacts-to-keep HEATMAP_ARTIFACTS_TO_KEEP]
       [--hardening-artifacts-to-keep HARDENING_ARTIFACTS_TO_KEEP]
       [--timestamp TIMESTAMP]
       [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
```

**Key Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repo-root` | path | auto | Repository root override |
| `--healthview-root` | path | orchestrator_reports/test_execution_telemetry | Output root |
| `--logs-dir` | path | rawview/test_execution_runs | Raw logs directory |
| `--artifacts-to-keep` | int | 3 | Orchestrator retention budget |
| `--collector-artifacts-to-keep` | int | per-config | Collector retention |
| `--health-artifacts-to-keep` | int | per-config | Health report retention |
| `--coverage-artifacts-to-keep` | int | per-config | Coverage retention |
| `--heatmap-artifacts-to-keep` | int | per-config | Heatmap retention |
| `--hardening-artifacts-to-keep` | int | per-config | Hardening retention |
| `--timestamp` | ISO8601 | now (UTC) | Run slug timestamp |
| `--log-level` | choice | INFO | Logging verbosity |

### 2.2 Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `Sequence[str] \| None` → `None` | raises SystemExit | ✅ |
| `run(argv)` | `Sequence[str] \| None` → `dict[str, Any]` | Payload dict | ✅ |

#### 2.2.1 Universal Interface Contract (ALL Scripts)

> **⚠️ MANDATORY — Every script MUST pass this section regardless of Tier Class.**

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` entry point exists | ✅ | Line L1435 |
| Returns `dict[str, Any]` (not int) | ✅ | Return type annotation L1435, returns dict at L1862-1876 |
| Return dict has `status` key | ✅ | L1863 `"status": status` |
| Return dict has `exit_code` key | ✅ | L1864 `"exit_code": exit_code` |
| `--repo-root` flag supported | ✅ | argparse definition |
| `--log-level` flag supported | ✅ | argparse definition |
| Google-style docstring on `run()` | ✅ | L1436-1458 with Args/Returns/Raises |
| No `sys.exit()` inside `run()` | ✅ | grep confirms absence |
| No `input()` prompts | ✅ | Non-interactive execution |
| Exceptions return error payload | ✅ | Pipeline handles failures gracefully |

#### 2.2.2 Return Payload Contract

**Orchestrator-specific keys returned:**

| Key | Type | Description |
|-----|------|-------------|
| `status` | str | "ok", "partial", or "error" |
| `exit_code` | int | 0 (success), 1 (partial/error) |
| `run_dir` | str | Path to orchestrator run directory |
| `output_dir` | str | Path to healthview root |
| `run_id` | str | Run slug (YYYYmmdd-HHMM) |
| `manifest` | dict | Full manifest payload |
| `telemetry` | dict | Telemetry metrics |
| `summary` | str | Summary markdown content |
| `child_outcomes` | list[dict] | Per-script outcome records |
| `scripts_run` | int | Total scripts executed |
| `scripts_passed` | int | Scripts with exit_code=0 |
| `scripts_failed` | int | Scripts with exit_code≠0 |

### 2.3 Current Output Contract

**Output root:** `.repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry/<YYYYmmdd-HHMM>/`

**Base package (Tier-1 HealthView contract):**

| Artifact | Format | Description |
|----------|--------|-------------|
| `manifest.json` | JSON | Pipeline manifest with child outcomes |
| `summary.md` | Markdown | Human-readable summary |
| `telemetry.json` | JSON | Metrics and timing data |

**Additional artifacts:**

| Artifact | Format | Description |
|----------|--------|-------------|
| `child_outcomes.json` | JSON | Per-script execution records |

### 2.4 Compliance Assessment

#### 2.4.1 Universal Compliance (Tier A & B)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` returns dict | ✅ | L1435 signature, L1862-1876 return |
| Status in return | ✅ | L1863 `"status": status` |
| Standard CLI flags (repo-root, log-level) | ✅ | argparse definitions |
| Can be dynamically imported | ✅ | Standard module structure |
| Idempotent (safe to re-run) | ✅ | Multiple runs don't corrupt |

#### 2.4.2 Bundle Compliance (Orchestrator-specific)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Timestamped output directory | ✅ | YYYYmmdd-HHMM format via run_slug |
| Uses `write_report_artifacts()` | ✅ | via create_storage().write_* |
| No `latest_*` pointer files | ✅ | No evidence of latest files |
| `--artifacts-to-keep` flag supported | ✅ | argparse definition |
| Base package emitted (manifest/summary/telemetry) | ✅ | via storage.write_* calls |

### 2.5 Output Quality Assessment

> **⚠️ MANDATORY STOP-GATE — DO NOT SKIP**

#### 2.5.1 QA Verification

| Check | Command | Result | Evidence |
|-------|---------|--------|----------|
| mypy --strict | `python -m mypy --strict <script>` | ✅ | Success after fixes (2026-01-29) |
| pytest | `pytest <test_file> -v` | ✅ 14/14 | All tests passing |
| CLI execution | `python <script> --help` | ✅ | Runs without error |

#### 2.5.2 Tier-3 YAML

| Check | Status | Evidence |
|-------|--------|----------|
| Tier-3 YAML file exists | ✅ | tier3_run_test_execution_telemetry.yaml |
| YAML is valid | ✅ | Validated via tier3_index tests |
| Registered in script inventory | ✅ | Referenced in metadata.tier2_rosters |

---

## 3. Gap Analysis

### 3.1 Required Changes

#### 3.1.1 Universal Compliance Gaps

| Gap | Priority | Effort | Status |
|-----|----------|--------|--------|
| Missing return type on `_load_run_callable` | Medium | S | ✅ Fixed |
| Missing return type on `collect_step` | Medium | S | ✅ Fixed |
| Missing return type on `analyse_step` | Medium | S | ✅ Fixed |
| Missing return type on `summarize_step` | Medium | S | ✅ Fixed |
| Missing `Callable` import | Medium | S | ✅ Fixed |
| Missing `TopicStepOutcome` import | Medium | S | ✅ Fixed |

**All gaps resolved (2026-01-29).**

### 3.2 Alteration Locations

| Location | Change | Standard | Status |
|----------|--------|----------|--------|
| L25 | Added `Callable` to typing imports | mypy --strict | ✅ Complete |
| L40 | Added `TopicStepOutcome` to libraries imports | mypy --strict | ✅ Complete |
| L525-527 | Added return type annotation to `_load_run_callable` | mypy --strict | ✅ Complete |
| L544-548 | Added cast() for return from sys.modules | mypy --strict | ✅ Complete |
| L555-557 | Added cast() for run_callable return | mypy --strict | ✅ Complete |
| L1481 | Added return type `TopicStepOutcome` to `collect_step` | mypy --strict | ✅ Complete |
| L1553 | Added return type `TopicStepOutcome` to `analyse_step` | mypy --strict | ✅ Complete |
| L1623 | Added return type `TopicStepOutcome` to `summarize_step` | mypy --strict | ✅ Complete |

---

## 4. Changes Made

### 4.1 Type Annotation Fixes (2026-01-29)

**File:** `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py`

| Change | Lines | Description |
|--------|-------|-------------|
| Added `Callable` import | L25 | `from typing import Any, Callable, Sequence, cast` |
| Added `TopicStepOutcome` import | L40 | Added to libraries import block |
| Typed `_load_run_callable` | L525-527 | Return `Callable[[Sequence[str] \| None], dict[str, Any]]` |
| Cast return values | L544-548, L555-557 | Used `cast()` for dynamic returns |
| Typed `collect_step` | L1481 | Return `TopicStepOutcome` |
| Typed `analyse_step` | L1553 | Return `TopicStepOutcome` |
| Typed `summarize_step` | L1623 | Return `TopicStepOutcome` |

### 4.2 Verification Summary (2026-01-29)

| Item | Finding |
|------|---------|
| Return payload | Compliant — `status`, `exit_code`, `run_dir` present |
| Tier-3 YAML | Exists (validated via tier3_index) |
| pytest | 14/14 tests passing |
| mypy --strict | ✅ Success (after fixes) |

---

## 5. Evidence

### 5.1 Tests

| Test | Status |
|------|--------|
| test_parse_timestamp_invalid_raises | ✅ PASSED |
| test_parse_timestamp_naive_assumes_utc | ✅ PASSED |
| test_latest_directory_selects_latest | ✅ PASSED |
| test_read_json_returns_dict_only | ✅ PASSED |
| test_relativize_handles_outside_repo | ✅ PASSED |
| test_load_run_callable_errors_when_missing_run | ✅ PASSED |
| test_load_run_callable_uses_sys_modules_shortcut | ✅ PASSED |
| test_execute_coverage_finds_run_dir | ✅ PASSED |
| test_execute_hardening_passes_tests_dir | ✅ PASSED |
| test_section_hardening_uses_telemetry_metrics | ✅ PASSED |
| test_section_coverage_prefers_telemetry_metrics_even_when_zero | ✅ PASSED |
| test_section_coverage_labels_heuristic_threshold_when_none_configured | ✅ PASSED |
| test_run_generates_healthview_bundle | ✅ PASSED |
| test_run_handles_missing_logs | ✅ PASSED |

**Test file:** `.repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`

### 5.2 Code References

1. L1435-1458 — `run()` function with docstring
1. L1878-1891 — `main()` function
1. L1862-1876 — return payload
1. L525-557 — `_load_run_callable()` with type annotations

---

## 6. Orchestrator Integration

> **This IS the orchestrator for Stage 1.1.**

### 6.1 Delegated Scripts

| Script | Module | Role |
|--------|--------|------|
| `collect_test_log_reports.py` | producers | Log collection |
| `generate_test_coverage_inventory.py` | producers | Coverage inventory |
| `analyze_test_hardening.py` | producers | Hardening analysis |
| `generate_test_log_health_report.py` | consumers | Health report |
| `generate_churn_complexity_heatmap.py` | aggregators | Churn heatmap |
| `summarize_test_execution_telemetry.py` | summarizers | Final summary |

### 6.2 Pipeline Steps

| Step | Function | Purpose |
|------|----------|---------|
| collect | `collect_step()` | Coverage + log collection |
| analyse | `analyse_step()` | Hardening + heatmap |
| summarize | `summarize_step()` | Health report generation |

---

## 7. Completion

> **⚠️ This section is the FINAL GATE. Do not mark complete until ALL items are checked.**

### 7.1 Build Document Completion Checklist

**Discovery & Analysis:**

- [x] Section 1 (Script Identity) — All fields populated
- [x] Section 2.1 (CLI Interface) — Flags documented from `--help` output
- [x] Section 2.2 (Entry Points) — Signatures verified against code
- [x] Section 2.4 (Compliance Assessment) — All checks have evidence

**Implementation & Testing:**

- [x] Section 3 (Gap Analysis) — Gaps identified with priority/effort
- [x] Section 4 (Changes Made) — Type annotation additions documented
- [x] Section 5 (Evidence) — Test results captured (pytest 14/14, mypy ✅)

**Tier-3 & DB Integration:**

- [x] Section 2.5.2 — Tier-3 YAML exists

**Orchestrator Role:**

- [x] Section 6 — Delegated scripts and pipeline steps documented

### 7.2 Tier-2 Roster Update

> **After completing Section 7.1, update the parent Tier-2 roster document.**

**Roster location:** `tier2_test_execution_telemetry_roster.md`

**Roster update completed (2026-01-29):**

- [x] Converted TER-001 record from "Fixture Example (Permanent)" bullet-point format to YAML format
- [x] Updated Records Index anchor to `#ter-001-run_test_execution_telemetrypy`
- [x] Updated Pruning Index anchor to `#ter-001-run_test_execution_telemetrypy`
- [x] Added `phase4_build_doc` field linking to this document
- [x] Added `qa_evidence.output_truth` field with verified ground truth
- [x] Removed legacy Implementation Workstreams section for TER-001
- [x] Added Update Log entry documenting Phase 4 completion

### 7.3 Document Finalization

**Frontmatter updated:**

```yaml
status: complete        # Set to: complete
version: "1.0.0"        # Initial release
updated_at: 2026-01-29  # Completion date
```

### 7.4 Phase 4 Processing Complete

**Completion timestamp:** 2026-01-29

**Summary:**

| Aspect | Status | Evidence |
|--------|--------|----------|
| Universal compliance | ✅ | Return payload has status/exit_code keys |
| Bundle compliance | ✅ | Base package emitted (manifest/summary/telemetry) |
| Type annotations | ✅ | mypy --strict passes after fixes |
| Tier-3 YAML | ✅ | tier3_run_test_execution_telemetry.yaml |
| Roster updated | ✅ | Already marked DONE in roster |

---

## 8. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-29 | Complete — type annotations added, all verification passed |
