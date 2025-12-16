---
title: DB Integration — collect_faulthandler_reports
audience: [Copilot, Agents, Developers]
role: [Documentation, Integration]
owners: [command_center]
status: active
version: 1
updated_at: 2025-12-15
tags: [db-integration, rawview, faulthandler, fault-diagnostics, telemetry, positional-encoding]
related_files:
  - .repo_studios/scripts/producers/collect_faulthandler_reports.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/libraries/prune_logs.py
---

# DB Integration — collect_faulthandler_reports

See `.github/instructions/markdown.instructions.md` for repo-wide Markdown rules (last reviewed 2025-12-15).

## Goals

- Describe how the faulthandler producer writes positional-encoded artifacts.
- Document the dual-write storage calls (`create_storage`) and marker locations.
- Map `manifest.json` and `telemetry.json` fields to database tables for agent queries.

## System Context

- Producer: `.repo_studios/scripts/producers/collect_faulthandler_reports.py`
- Viewer/topic: `rawview / fault_artifacts_producer`
- Output layout (positional encoding):

```text
<reports_root>/rawview/fault_artifacts_producer/<YYYYMMDD-HHMM>/
  manifest.json
  summary.md
  telemetry.json
```

- Storage API: `.repo_studios/command_center/scripts/libraries/database_integration.py:create_storage`
  - File writes are the primary output.
  - DB writes are dormant unless enabled via config/env; failures do not abort file outputs.

## Agent Instructions

<!-- agents:begin:db_integration_collect_faulthandler_reports -->
```yaml
viewer_slug: rawview
topic: fault_artifacts_producer
artifacts:
  - role: manifest
    path: rawview/fault_artifacts_producer/<YYYYMMDD-HHMM>/manifest.json
  - role: summary
    path: rawview/fault_artifacts_producer/<YYYYMMDD-HHMM>/summary.md
  - role: telemetry
    path: rawview/fault_artifacts_producer/<YYYYMMDD-HHMM>/telemetry.json
notes:
  - Use telemetry.metrics.signature_count and telemetry.metrics.repeat_offender_signatures for triage.
  - Use telemetry.components.faulthandler.summary/severity_buckets for richer analysis.
  - No producer `latest_*` pointers exist for this topic.
```
<!-- agents:end:db_integration_collect_faulthandler_reports -->

## Human Notes

### Marker locations

The producer includes `DB_INTEGRATION_MARKER` tags immediately above each storage write:

- manifest write: `storage.write_manifest(...)`
- summary write: `storage.write_summary(..., format="md")`
- telemetry write: `storage.write_telemetry(...)`

### Pruning

The producer prunes historical run folders under:

- `<reports_root>/rawview/fault_artifacts_producer/`

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

If you later extract time-series metrics from fault artifacts producer runs, recommended fields include:

- `telemetry.run_timestamp` → `test_metrics.metric_timestamp`
- `telemetry.metrics.signature_count` → numeric metric column (or JSONB)
- `telemetry.metrics.repeat_offender_signatures` → numeric metric column (or JSONB)

Until the schema is fully wired, treat metric extraction as a planned enhancement; the full
telemetry artifact should always be stored in `report_artifacts`.

## Example SQL (agent queries)

```sql
-- Latest faulthandler producer run
SELECT *
FROM report_runs
WHERE viewer_slug = 'rawview'
  AND topic = 'fault_artifacts_producer'
ORDER BY run_timestamp DESC
LIMIT 1;
```

```sql
-- Fetch telemetry artifact for the latest run
SELECT a.content_json
FROM report_runs r
JOIN report_artifacts a ON a.run_id = r.id
WHERE r.viewer_slug = 'rawview'
  AND r.topic = 'fault_artifacts_producer'
  AND a.artifact_role = 'telemetry'
ORDER BY r.run_timestamp DESC
LIMIT 1;
```

## Reference Prompts

- "Load the latest rawview/fault_artifacts_producer telemetry and list the top metrics."
- "Show the latest run_dir captured by the faulthandler producer and the bundle_dir path from manifest."

## Update Log

- 2025-12-15 — Added positional-encoding layout, marker notes, pruning notes, and DB mapping guidance.
