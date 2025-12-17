---
title: DB Integration — generate_test_coverage_inventory.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-12-17
tags: [db-integration, producer, healthview, test-coverage]
related_files:
  - .repo_studios/scripts/producers/generate_test_coverage_inventory.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — generate_test_coverage_inventory.py

## Goals

- Document the database integration markers and intended table mappings for the test coverage inventory producer.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Producer script: `.repo_studios/scripts/producers/generate_test_coverage_inventory.py`
- Output contract (file system): `.repo_studios/reports/producer_reports/healthview/test_coverage_inventory/<YYYYMMDD-HHMM>/{manifest.json,summary.md,telemetry.json}`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)

## Agent Instructions

<!-- agents:begin:db_integration_generate_test_coverage_inventory -->
```yaml
producer:
  viewer_slug: healthview
  topic: test_coverage_inventory
artifacts:
  - manifest.json
  - summary.md
  - telemetry.json
markers:
  - description: Persist manifest bundle (report_runs + report_artifacts)
    method: storage.write_manifest
  - description: Persist human-readable report summary (report_artifacts)
    method: storage.write_summary
  - description: Persist telemetry payload + extracted metrics (report_artifacts + test_metrics)
    method: storage.write_telemetry
```
<!-- agents:end:db_integration_generate_test_coverage_inventory -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `manifest.json`
  - Key fields (typical): `viewer_slug`, `topic`, `run_timestamp`, `status`, `repo_root`, `inputs`, `catalog`

- `report_artifacts`
  - Source: `manifest.json`, `summary.md`, `telemetry.json`
  - Roles:
    - `summary` (Markdown)
    - `telemetry` (JSON)

- `test_metrics`
  - Source: `telemetry.json` → `telemetry.metrics`
  - Suggested metrics:
    - `overall_coverage_pct`
    - `total_functions`
    - `covered_functions`
    - `total_files`
    - `files_below_threshold_count`
    - `threshold`

## Human Notes

- This producer is expected to remain in **history mode** (trendable). Retention is controlled by `--artifacts-to-keep` and enforced via `prune_run_directories`.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.

## Reference Prompts

- "Run marker audit and confirm generate_test_coverage_inventory.py appears with 3 markers"
- "Show the manifest + telemetry schemas produced by the latest healthview/test_coverage_inventory run"

## Update Log

- 2025-12-17 — Initial draft created for the positional bundle migration.
