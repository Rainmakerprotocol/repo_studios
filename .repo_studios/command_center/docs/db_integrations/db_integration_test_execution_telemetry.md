---
title: DB Integration — run_test_execution_telemetry.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-12-30
tags: [db-integration, orchestrator, healthview, test-execution-telemetry]
related_files:
  - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — run_test_execution_telemetry.py

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

- Document the database integration markers and intended table mappings for the Test Execution Telemetry orchestrator.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Orchestrator script: `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py`
- Viewer slug: `orchestrator_reports`
- Topic: `test_execution_telemetry` (HEALTHVIEW_TOPIC constant)
- Topic slug: `test-execution-telemetry` (TOPIC_SLUG constant for catalog registration)
- Output contract (file system): `.repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry/<YYYYMMDD-HHMM>/{manifest.json,summary.md,telemetry.json}`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)
- Runtime: ~5–6 minutes (invokes 6 upstream scripts)

## Invoked Scripts

The orchestrator coordinates execution of the following upstream scripts:

| Order | Script | Path | Role | Topic |
| --- | --- | --- | --- | --- |
| 1 | `generate_test_coverage_inventory.py` | `.repo_studios/scripts/producers/` | producer | test_coverage_inventory |
| 2 | `collect_test_log_reports.py` | `.repo_studios/scripts/producers/` | producer | test_log_reports |
| 3 | `analyze_test_hardening.py` | `.repo_studios/scripts/producers/` | producer | test_hardening |
| 4 | `generate_churn_complexity_heatmap.py` | `.repo_studios/scripts/aggregators/` | aggregator | churn_complexity_heatmap |
| 5 | `generate_test_log_health_report.py` | `.repo_studios/scripts/consumers/` | consumer | test_log_health |
| 6 | `summarize_test_execution_telemetry.py` | `.repo_studios/command_center/scripts/summarizers/` | summarizer | test_execution_telemetry |

## CLI Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--repo-root` | (inferred) | Repository root override |
| `--logs-dir` | `.repo_studios/logs` | Pytest log input directory |
| `--test-log-reports-dir` | `.repo_studios/reports/healthview/producer_reports/test_log_reports` | Log report output |
| `--test-log-health-dir` | `.repo_studios/reports/healthview/consumer_reports/test_log_health` | Health report output |
| `--test-coverage-output-dir` | `.repo_studios/reports/healthview/producer_reports/` | Coverage inventory output |
| `--test-coverage-xml` | `coverage.xml` | Coverage XML source |
| `--heatmap-output-dir` | `.repo_studios/reports/healthview/aggregator_reports/` | Heatmap output |
| `--heatmap-metrics-source` | (none) | Optional external metrics JSON |
| `--heatmap-window` | `500` | Commit window for churn analysis |
| `--hardening-output-dir` | `.repo_studios/reports/healthview/producer_reports/` | Hardening analysis output |
| `--healthview-root` | `.repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry` | Orchestrator output root |
| `--artifacts-to-keep` | `3` | Orchestrator topic artifacts to retain |
| `--collector-artifacts-to-keep` | `10` | Log report retention |
| `--health-artifacts-to-keep` | `5` | Health report retention |
| `--coverage-artifacts-to-keep` | `10` | Coverage inventory retention |
| `--heatmap-artifacts-to-keep` | `10` | Heatmap retention |
| `--hardening-artifacts-to-keep` | `10` | Hardening retention |
| `--timestamp` | (current UTC) | ISO8601 timestamp for run slug |
| `--log-level` | `INFO` | Logging verbosity |

## Agent Instructions

<!-- agents:begin:db_integration_test_execution_telemetry -->
```yaml
orchestrator:
  viewer_slug: orchestrator_reports
  topic: test_execution_telemetry
  topic_slug: test-execution-telemetry
artifacts:
  - manifest.json
  - summary.md
  - telemetry.json
markers:
  - description: Persist orchestrator manifest (report_runs + report_artifacts + orchestration_catalog)
    method: storage.write_manifest
  - description: Persist human-readable summary (report_artifacts)
    method: storage.write_summary
  - description: Persist telemetry payload (report_artifacts + telemetry_metrics)
    method: storage.write_telemetry
catalog_entries:
  - script_path: .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py
    topic: test-execution-telemetry
    role: orchestrator
  - script_path: .repo_studios/scripts/producers/collect_test_log_reports.py
    topic: test-execution-telemetry
    role: producer
  - script_path: .repo_studios/scripts/consumers/generate_test_log_health_report.py
    topic: test-execution-telemetry
    role: consumer
  - script_path: .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py
    topic: test-execution-telemetry
    role: aggregator
  - script_path: .repo_studios/scripts/producers/generate_test_coverage_inventory.py
    topic: test-execution-telemetry
    role: producer
  - script_path: .repo_studios/scripts/producers/analyze_test_hardening.py
    topic: test-execution-telemetry
    role: producer
  - script_path: .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py
    topic: test-execution-telemetry
    role: summarizer
```
<!-- agents:end:db_integration_test_execution_telemetry -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `manifest.json`
  - Key fields: `viewer`, `topic`, `run_slug`, `generated_at`, `schema_version`

- `report_artifacts`
  - Source: `manifest.json`, `summary.md`, `telemetry.json`
  - Roles:
    - `manifest_json` (JSON — orchestrator manifest with artifact refs)
    - `summary_md` (Markdown — enhanced summary with pipeline status, metrics tables, concerns)
    - `telemetry_json` (JSON — full pipeline telemetry payload)

- `orchestration_catalog`
  - Source: `manifest.json` → `catalog` array
  - Key fields: `script_path`, `topic`, `role`
  - Purpose: Track which scripts were registered for this orchestrator run

- `telemetry_metrics`
  - Source: `telemetry.json` → `metrics`
  - Suggested metrics:
    - `tests_total`
    - `tests_passed`
    - `tests_failed`
    - `warnings_total`
    - `slow_tests`
    - `coverage_pct`
    - `hardening_issues_count`
    - `hotspot_files_count`
    - `artifact_count`
    - `total_bytes`

- `artifact_references`
  - Source: `manifest.json` → `artifacts`
  - Links: `log_report`, `coverage_report`, `heatmap`, `hardening`, `health_report`, `summary_markdown`, `summary_json`

## Human Notes

- This is the Stage 1.1 orchestrator that coordinates all test execution telemetry gathering, analysis, and summarization.
- The pipeline executes three steps: `collect` → `analyse` → `summarize`, with the summarize step depending on successful log collection.
- Script registration uses `CatalogRegistry` to record all 7 scripts (1 orchestrator + 6 invoked) in the manifest.
- Retention is controlled per-script via dedicated `--*-artifacts-to-keep` flags plus the orchestrator-level `--artifacts-to-keep`.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.
- The enhanced summary includes: Pipeline Status, Test Results, Coverage Analysis, Test Hardening, Churn × Complexity Hotspots, and Pass Rate Trend sections.

## Reference Prompts

- "Run marker audit and confirm run_test_execution_telemetry.py appears with 3 markers"
- "Execute the test execution telemetry orchestrator and show the summary"
- "List all catalog entries registered by the orchestrator"
- "Compare telemetry metrics between two orchestrator runs"

## Update Log

| Date | Author | Changes |
| --- | --- | --- |
| 2025-12-30 | repo_studios_ai | Initial creation from code inspection during Pass 3 Stage 1.1 verification |
