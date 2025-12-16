---
title: DB Integration — check_inventory_health
audience: [Copilot, Agents, Developers]
role: [Documentation, Integration]
owners: [command_center]
status: active
version: 1
updated_at: 2025-12-15
tags: [db-integration, healthview, inventory, thresholds, telemetry, positional-encoding]
related_files:
  - .repo_studios/scripts/producers/check_inventory_health.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/libraries/prune_logs.py
---

# DB Integration — check_inventory_health

See `.github/instructions/markdown.instructions.md` for repo-wide Markdown rules (last reviewed 2025-12-15).

## Goals

- Describe how the inventory health producer writes positional-encoded artifacts.
- Document the dual-write storage calls (`create_storage`) and marker locations.
- Map `manifest.json` and `telemetry.json` fields to database tables for agent queries.

## System Context

- Producer: `.repo_studios/scripts/producers/check_inventory_health.py`
- Viewer/topic: `healthview / inventory_health`
- Output layout (positional encoding):

```text
<reports_root>/healthview/inventory_health/<YYYYMMDD-HHMM>/
  manifest.json
  summary.md
  telemetry.json
```

- Storage API: `.repo_studios/command_center/scripts/libraries/database_integration.py:create_storage`
  - File writes are the primary output.
  - DB writes are dormant unless enabled via config/env; failures do not abort file outputs.

## Agent Instructions

<!-- agents:begin:db_integration_check_inventory_health -->
```yaml
viewer_slug: healthview
topic: inventory_health
artifacts:
  - role: manifest
    path: healthview/inventory_health/<YYYYMMDD-HHMM>/manifest.json
  - role: summary
    path: healthview/inventory_health/<YYYYMMDD-HHMM>/summary.md
  - role: telemetry
    path: healthview/inventory_health/<YYYYMMDD-HHMM>/telemetry.json
notes:
  - Use telemetry.issues for threshold breach triage.
  - Use telemetry.deltas for baseline comparisons.
```
<!-- agents:end:db_integration_check_inventory_health -->

## Human Notes

### Marker locations

The producer includes `DB_INTEGRATION_MARKER` tags immediately above each storage write:

- manifest write: `storage.write_manifest(...)`
- summary write: `storage.write_summary(..., format="md")`
- telemetry write: `storage.write_telemetry(...)`

### Pruning

The producer prunes historical run folders under:

- `<reports_root>/healthview/inventory_health/`

using `.repo_studios/command_center/scripts/libraries/prune_logs.py:prune_run_directories(keep=N, current_run=...)`.

## Database Mapping

### report_runs (manifest.json)

`manifest.json` is intended to map to the `report_runs` table (see the documented target schema in `.repo_studios/command_center/scripts/libraries/database_integration.py`).

Suggested mapping:

- `viewer_slug` → `report_runs.viewer_slug`
- `topic` → `report_runs.topic`
- `run_timestamp` (YYYYMMDD-HHMM) + `generated_at` → `report_runs.run_timestamp` (timestamptz)
- `status` → `report_runs.status`
- `inputs` (object) → `report_runs.inputs` (JSONB)
- `catalog` (array) → `report_runs.catalog` (JSONB)

### report_artifacts (summary.md, telemetry.json)

Suggested mapping:

- `summary.md` → `report_artifacts` with:
  - `artifact_role = 'summary'`
  - `artifact_type = 'md'`
  - `content_text = <markdown>`

- `telemetry.json` → `report_artifacts` with:
  - `artifact_role = 'telemetry'`
  - `artifact_type = 'json'`
  - `content_json = <telemetry payload>`

### test_metrics (telemetry.json)

If you later extract time-series metrics from inventory health runs, recommended fields include:

- `telemetry.run_timestamp` → `test_metrics.metric_timestamp`
- `telemetry.summary.total_assets` → numeric metric column (or JSONB)
- `telemetry.summary.issues` → numeric metric column (or JSONB)
- `telemetry.issues` → JSONB for per-threshold diagnostics

Until the schema is fully wired, treat metric extraction as a planned enhancement; the full
telemetry artifact should always be stored in `report_artifacts`.

## Example SQL (agent queries)

```sql
-- Latest inventory health run
SELECT *
FROM report_runs
WHERE viewer_slug = 'healthview'
  AND topic = 'inventory_health'
ORDER BY run_timestamp DESC
LIMIT 1;
```

```sql
-- Fetch telemetry artifact for the latest run
SELECT a.content_json
FROM report_runs r
JOIN report_artifacts a ON a.run_id = r.id
WHERE r.viewer_slug = 'healthview'
  AND r.topic = 'inventory_health'
  AND a.artifact_role = 'telemetry'
ORDER BY r.run_timestamp DESC
LIMIT 1;
```

## Reference Prompts

- "Load the latest inventory_health telemetry and list failing statuses and missing consumers."
- "Show baseline delta for total assets for the latest inventory_health run."

## Update Log

- 2025-12-15 — Added positional-encoding layout, marker notes, pruning notes, and DB mapping guidance.
