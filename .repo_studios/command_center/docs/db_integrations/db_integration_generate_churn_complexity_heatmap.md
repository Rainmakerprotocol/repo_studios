---
title: DB Integration — generate_churn_complexity_heatmap.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-12-27
tags: [db-integration, aggregator, healthview, churn, complexity, heatmap]
related_files:
  - .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — generate_churn_complexity_heatmap.py

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

- Document the database integration markers and intended table mappings for the churn-complexity heatmap aggregator.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Aggregator script: `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py`
- Output contract (file system): `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/<YYYYMMDD-HHMM>/{heatmap.json,heatmap.md,bundle_summary.json}`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)

## Agent Instructions

<!-- agents:begin:db_integration_generate_churn_complexity_heatmap -->
```yaml
aggregator:
  viewer_slug: healthview
  topic: churn_complexity_heatmap
artifacts:
  - heatmap.json
  - heatmap.md
  - bundle_summary.json
markers:
  - description: Persist heatmap bundle (report_runs + report_artifacts)
    method: storage.write_manifest
  - description: Persist human-readable heatmap summary (report_artifacts)
    method: storage.write_summary
  - description: Persist heatmap payload + extracted metrics (report_artifacts + heatmap_metrics)
    method: storage.write_telemetry
```
<!-- agents:end:db_integration_generate_churn_complexity_heatmap -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `bundle_summary.json`
  - Key fields (typical): `viewer_slug`, `topic`, `run_timestamp`, `status`, `repo_root`, `inputs`, `mode`

- `report_artifacts`
  - Source: `heatmap.json`, `heatmap.md`, `bundle_summary.json`
  - Roles:
    - `heatmap` (JSON — items array with file/churn/complexity/score)
    - `summary` (Markdown)
    - `bundle_summary` (JSON — metadata)

- `heatmap_metrics`
  - Source: `heatmap.json` → `items[]`
  - Suggested metrics per file:
    - `file_path`
    - `churn` (number of commits touching file)
    - `complexity` (aggregate cyclomatic complexity)
    - `failures` (test failure count)
    - `score` (computed hotspot score)

## Human Notes

- This aggregator operates in two modes: `producer` (standalone) or `consumer` (reads from upstream producer bundles).
- Retention is controlled by `--artifacts-to-keep` (default: 5) and enforced via `prune_run_directories`.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.
- The `items` array in `heatmap.json` is the primary time-series source; each item represents a file's hotspot score.

## Reference Prompts

- "Run marker audit and confirm generate_churn_complexity_heatmap.py appears with 3 markers"
- "Show the top 10 hotspot files from the latest churn_complexity_heatmap run"
- "Compare heatmap scores between two consecutive runs to detect emerging hotspots"
