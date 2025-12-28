---
title: DB Integration — summarize_test_execution_telemetry.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-12-27
tags: [db-integration, summarizer, healthview, test-execution-telemetry]
related_files:
  - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — summarize_test_execution_telemetry.py

## Goals

- Document the database integration markers and intended table mappings for the test execution telemetry summarizer.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Summarizer script: `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py`
- Output contract (file system): `.repo_studios/reports/healthview/summarizer_reports/test_execution_telemetry/<YYYYMMDD-HHMM>/{test_execution_telemetry_summary.json,test_execution_telemetry_summary.md}`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)

## Agent Instructions

<!-- agents:begin:db_integration_summarize_test_execution_telemetry -->
```yaml
summarizer:
  viewer_slug: healthview
  topic: test_execution_telemetry
artifacts:
  - test_execution_telemetry_summary.json
  - test_execution_telemetry_summary.md
markers:
  - description: Persist summary bundle (report_runs + report_artifacts)
    method: storage.write_manifest
  - description: Persist human-readable telemetry summary (report_artifacts)
    method: storage.write_summary
  - description: Persist consolidated telemetry payload (report_artifacts + summary_metrics)
    method: storage.write_telemetry
```
<!-- agents:end:db_integration_summarize_test_execution_telemetry -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `test_execution_telemetry_summary.json`
  - Key fields (typical): `viewer_slug`, `topic`, `run_timestamp`, `status`, `repo_root`, `inputs`, `source_manifest`

- `report_artifacts`
  - Source: `test_execution_telemetry_summary.json`, `test_execution_telemetry_summary.md`
  - Roles:
    - `summary_json` (JSON — consolidated metrics from all upstream scripts)
    - `summary_md` (Markdown — human-readable digest)

- `summary_metrics`
  - Source: `test_execution_telemetry_summary.json` → consolidated fields
  - Suggested metrics:
    - `tests_total`
    - `tests_passed`
    - `tests_failed`
    - `coverage_pct`
    - `hardening_issues_count`
    - `hotspot_files_count`
    - `pass_rate_delta`

## Human Notes

- This summarizer reads from the orchestrator manifest and consolidates metrics from all upstream Stage 1.1 scripts.
- Retention is controlled by `--artifacts-to-keep` (default: 5) and enforced via `write_report_artifacts` with `KeepSpec`.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.
- The summary provides a single-pane view of test execution health for dashboards and alerting.

## Reference Prompts

- "Run marker audit and confirm summarize_test_execution_telemetry.py appears with 3 markers"
- "Show the latest test execution telemetry summary"
- "Compare summary metrics between two orchestrator runs"
