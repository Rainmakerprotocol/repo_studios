---
title: DB Integration — summarize_fault_diagnostics_overview.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-01-02
tags: [db-integration, summarizer, healthview, fault-diagnostics]
related_files:
  - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — summarize_fault_diagnostics_overview.py

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

- Document the database integration markers and intended table mappings for the fault diagnostics summarizer.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Summarizer script: `.repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py`
- Topic slug: `fault_diagnostics_overview`
- Input contract: `.repo_studios/reports/healthview/consumer_reports/fault_artifacts/<YYYYMMDD-HHMM>/`
- Output contract (file system): `.repo_studios/reports/healthview/summarizer_reports/fault_diagnostics_overview/<YYYYMMDD-HHMM>/`
- Artifacts: `manifest.json`, `summary.md`, `telemetry.json`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)

## CLI Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--repo-root` | (inferred) | Repository root override |
| `--consumer-output-dir` | `.repo_studios/reports/healthview/consumer_reports/fault_artifacts` | Consumer bundle location |
| `--consumer-telemetry` | (auto-discovered) | Explicit telemetry.json path override |
| `--consumer-manifest` | (auto-discovered) | Explicit manifest.json path override |
| `--output-dir` | `.repo_studios/reports/healthview/summarizer_reports/fault_diagnostics_overview` | Summarizer output root |
| `--artifacts-to-keep` | `5` | Retention budget for timestamped bundles |
| `--log-level` | `INFO` | Logging verbosity |

## Agent Instructions

<!-- agents:begin:db_integration_fault_diagnostics_overview -->
```yaml
summarizer:
  viewer_slug: healthview
  topic: fault_diagnostics_overview
input_topic: fault_artifacts
artifacts:
  - manifest.json
  - summary.md
  - telemetry.json
markers:
  - description: Persist summarizer manifest (report_runs + report_artifacts)
    method: storage.write_manifest
  - description: Persist human-readable summary with baseline comparison (report_artifacts)
    method: storage.write_summary
  - description: Persist aggregated telemetry payload (report_artifacts + summary_metrics)
    method: storage.write_telemetry
```
<!-- agents:end:db_integration_fault_diagnostics_overview -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `manifest.json`
  - Key fields: `viewer_slug`, `topic`, `run_timestamp`, `generated_utc`, `status`

- `report_artifacts`
  - Source: `manifest.json`, `summary.md`, `telemetry.json`
  - Roles:
    - `manifest_json` (JSON — summarizer manifest)
    - `summary_md` (Markdown — consolidated digest with baseline comparison)
    - `telemetry_json` (JSON — aggregated metrics)

- `summary_metrics`
  - Source: `telemetry.json` → consolidated fields
  - Suggested metrics:
    - `signature_count`
    - `repeat_offender_count`
    - `baseline_delta`
    - `new_signatures`
    - `resolved_signatures`

## Human Notes

- This summarizer consumes fault artifact bundles from the consumer stage.
- Discovers latest consumer bundle via timestamp-sorted directory listing.
- Compares current run against previous bundle for baseline delta.
- No pointer files (`latest_*`) are used for discovery per HOP contract.
- Retention is controlled by `--artifacts-to-keep` and enforced via `write_report_artifacts`.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.

## Reference Prompts

- "Run marker audit and confirm summarize_fault_diagnostics_overview.py appears with 3 markers"
- "Show baseline comparison from latest fault diagnostics summary"
- "List new fault signatures compared to previous run"

## Update Log

| Date | Author | Changes |
| --- | --- | --- |
| 2025-01-02 | repo_studios_ai | Initial creation from code inspection during Stage 3.1 Pass 3 |
