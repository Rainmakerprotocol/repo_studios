---
title: DB Integration — generate_anchor_inventory.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-01-02
tags: [db-integration, producer, healthview, anchor-inventory]
related_files:
  - .repo_studios/scripts/producers/generate_anchor_inventory.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — generate_anchor_inventory.py

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

- Document the database integration markers and intended table mappings for the anchor inventory producer.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Producer script: `.repo_studios/scripts/producers/generate_anchor_inventory.py`
- Topic slug: `anchor_inventory`
- Output contract (file system): `.repo_studios/reports/healthview/producer_reports/anchor_inventory/<YYYYMMDD-HHMM>/`
- Artifacts: `manifest.json`, `summary.md`, `telemetry.json`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)

## CLI Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--repo-root` | (inferred) | Repository root override |
| `--docs-root` | `docs` | Docs directory to scan |
| `--output-dir` | `.repo_studios/reports/healthview/producer_reports/anchor_inventory` | Base output directory |
| `--artifacts-to-keep` | `5` | Retention count for timestamped runs |
| `--timestamp` | (current UTC) | Override run timestamp (ISO 8601) |
| `--json-out` | (none) | Optional legacy JSON mirror path |
| `--allow-file` | (none) | Optional file containing generic allowlist |
| `--test-file` | (none) | Path to test_global_anchors.py for ALLOWED baseline extraction |
| `--additional-docs-root` | (none) | Additional documentation directories to scan (repeatable) |
| `--log-level` | `INFO` | Logging verbosity |

## Agent Instructions

<!-- agents:begin:db_integration_anchor_inventory -->
```yaml
producer:
  viewer_slug: healthview
  topic: anchor_inventory
artifacts:
  - manifest.json
  - summary.md
  - telemetry.json
markers:
  - description: Persist anchor inventory manifest (report_runs + report_artifacts)
    method: storage.write_manifest
  - description: Persist human-readable summary (report_artifacts)
    method: storage.write_summary
  - description: Persist telemetry payload (report_artifacts + inventory_metrics)
    method: storage.write_telemetry
```
<!-- agents:end:db_integration_anchor_inventory -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `manifest.json`
  - Key fields: `viewer_slug`, `topic`, `run_timestamp`, `generated_utc`, `status`, `inputs`

- `report_artifacts`
  - Source: `manifest.json`, `summary.md`, `telemetry.json`
  - Roles:
    - `manifest_json` (JSON — producer manifest with catalog and summary)
    - `summary_md` (Markdown — human-readable anchor inventory digest)
    - `telemetry_json` (JSON — full telemetry payload)

- `inventory_metrics`
  - Source: `telemetry.json` → `metrics`
  - Suggested metrics:
    - `total_slugs`
    - `duplicate_slugs`
    - `files_scanned`
    - `documents_with_missing_h1`
    - `documents_with_missing_h2`

## Human Notes

- This producer scans markdown files for H1/H2 headings and builds an inventory of anchor slugs.
- It identifies duplicate slugs across documents and documents missing required heading levels.
- Retention is controlled by `--artifacts-to-keep` and enforced via `prune_run_directories`.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.
- The producer supports multiple docs roots via `--additional-docs-root` for comprehensive scanning.

## Reference Prompts

- "Run marker audit and confirm generate_anchor_inventory.py appears with 3 markers"
- "Show duplicate anchor slugs from the latest anchor inventory"
- "List documents missing H1 headings"

## Update Log

| Date | Author | Changes |
| --- | --- | --- |
| 2025-01-02 | repo_studios_ai | Initial creation from code inspection during Stage 2.1 Pass 3 |
