---
title: DB Integration — generate_test_log_health_report.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-12-27
tags: [db-integration, consumer, healthview, test-health, pass-rate]
related_files:
  - .repo_studios/scripts/consumers/generate_test_log_health_report.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — generate_test_log_health_report.py

## Goals

- Document the database integration markers and intended table mappings for the test log health report consumer.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Consumer script: `.repo_studios/scripts/consumers/generate_test_log_health_report.py`
- Output contract (file system): `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/<YYYYMMDD-HHMM>/{manifest.json,summary.md,telemetry.json,bundle_summary.json}`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)

## Agent Instructions

<!-- agents:begin:db_integration_generate_test_log_health_report -->
```yaml
consumer:
  viewer_slug: healthview
  topic: test_log_health_reports
artifacts:
  - manifest.json
  - summary.md
  - telemetry.json
  - bundle_summary.json
markers:
  - description: Persist manifest bundle (report_runs + report_artifacts)
    method: storage.write_manifest
  - description: Persist human-readable health summary (report_artifacts)
    method: storage.write_summary
  - description: Persist telemetry payload + extracted metrics (report_artifacts + health_metrics)
    method: storage.write_telemetry
```
<!-- agents:end:db_integration_generate_test_log_health_report -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `manifest.json`
  - Key fields (typical): `viewer_slug`, `topic`, `run_timestamp`, `status`, `repo_root`, `inputs`, `source`

- `report_artifacts`
  - Source: `manifest.json`, `summary.md`, `telemetry.json`, `bundle_summary.json`
  - Roles:
    - `manifest` (JSON — run metadata)
    - `summary` (Markdown — human-readable digest)
    - `telemetry` (JSON — metrics + payload)
    - `bundle_summary` (JSON — comparisons with previous runs)

- `health_metrics`
  - Source: `telemetry.json` → `metrics` and `bundle_summary.json` → `comparisons`
  - Suggested metrics:
    - `pass_rate_current` (percentage)
    - `pass_rate_previous` (percentage)
    - `pass_rate_delta` (percentage change)
    - `total_tests`
    - `passed_tests`
    - `failed_tests`
    - `source_bundle` (upstream producer bundle path)

## Human Notes

- This consumer reads from upstream producer bundles (`rawview/test_log_reports`) and computes pass rate trends.
- Retention is controlled by `--artifacts-to-keep` (default: 5) and enforced via `prune_run_directories`.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.
- The `comparisons` object in `bundle_summary.json` tracks delta against the previous run for trend analysis.

## Reference Prompts

- "Run marker audit and confirm generate_test_log_health_report.py appears with 3 markers"
- "Show the pass rate trend over the last 5 runs"
- "Alert if pass_rate_delta is negative for two consecutive runs"
