---
title: DB Integration — generate_fault_artifacts.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-01-02
tags: [db-integration, consumer, healthview, fault-artifacts]
related_files:
  - .repo_studios/scripts/consumers/generate_fault_artifacts.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — generate_fault_artifacts.py

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

- Document the database integration markers and intended table mappings for the fault artifacts consumer.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Consumer script: `.repo_studios/scripts/consumers/generate_fault_artifacts.py`
- Topic slug: `fault_artifacts`
- Output contract (file system): `.repo_studios/reports/healthview/consumer_reports/fault_artifacts/<YYYYMMDD-HHMM>/`
- Artifacts: `manifest.json`, `summary.md`, `telemetry.json`
- Rawview artifacts (within run_dir): `MANIFEST.json`, `dumps/combined.txt`, `stacks.csv`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)

## CLI Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--outdir` | (latest under rawview/fault_diagnostics_runs) | Run directory containing stacks.log |
| `--report` | (none) | Explicit producer report JSON to reuse |
| `--output-dir` | `.repo_studios/reports/healthview/consumer_reports/fault_artifacts` | Consumer output root |
| `--artifacts-to-keep` | `5` | Retention budget for timestamped bundles |
| `--log-level` | `INFO` | Logging verbosity |

## Environment Variables

| Variable | Description |
| --- | --- |
| `FAULT_OUTDIR` | Alternative to `--outdir` CLI argument |
| `FAULT_TOP_FRAMES_N` | Override frame depth for signature extraction (default: 10) |
| `FAULT_LOGS_ALLOW_LEGACY` | Allow legacy faulthandler run paths |

## Agent Instructions

<!-- agents:begin:db_integration_fault_artifacts -->
```yaml
consumer:
  viewer_slug: healthview
  topic: fault_artifacts
artifacts:
  - manifest.json
  - summary.md
  - telemetry.json
  - stacks.csv (rawview)
markers:
  - description: Persist fault artifacts manifest (report_runs + report_artifacts)
    method: storage.write_manifest
  - description: Persist human-readable summary (report_artifacts)
    method: storage.write_summary
  - description: Persist telemetry payload (report_artifacts + fault_metrics)
    method: storage.write_telemetry
csv_schema:
  - signature_id
  - count
  - top_module
  - top_func
  - top_file
  - top_line
  - threads
  - first_seen_ts
  - last_seen_ts
```
<!-- agents:end:db_integration_fault_artifacts -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `manifest.json`
  - Key fields: `viewer_slug`, `topic`, `run_timestamp`, `generated_utc`, `status`

- `report_artifacts`
  - Source: `manifest.json`, `summary.md`, `telemetry.json`
  - Roles:
    - `manifest_json` (JSON — consumer manifest)
    - `summary_md` (Markdown — human-readable fault digest)
    - `telemetry_json` (JSON — metrics and signatures)

- `fault_metrics`
  - Source: `telemetry.json` → `metrics`
  - Suggested metrics:
    - `signature_count`
    - `repeat_offender_signatures`
    - `total_stack_dumps`
    - `severity_buckets`

- `fault_signatures`
  - Source: `stacks.csv`
  - Key fields: `signature_id`, `count`, `top_module`, `top_func`, `top_file`, `top_line`

## Human Notes

- This consumer processes raw faulthandler stack dumps from producer reports.
- Parser is best-effort against stdlib faulthandler format.
- Timestamps default to current UTC when unavailable.
- No pointer files (`latest_*`) are emitted per HOP contract.
- Retention is controlled by `--artifacts-to-keep` and enforced via `prune_run_directories`.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.

## Reference Prompts

- "Run marker audit and confirm generate_fault_artifacts.py appears with 3 markers"
- "Show repeat offender fault signatures from latest run"
- "List top 5 fault signatures by occurrence count"

## Update Log

| Date | Author | Changes |
| --- | --- | --- |
| 2025-01-02 | repo_studios_ai | Initial creation from code inspection during Stage 3.1 Pass 3 |
