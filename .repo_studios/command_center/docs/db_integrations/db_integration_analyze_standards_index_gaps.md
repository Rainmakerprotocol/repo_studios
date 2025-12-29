---
title: DB Integration — analyze_standards_index_gaps
audience: [Copilot, Agents, Developers]
role: [Documentation, Integration]
owners: [command_center]
status: active
version: 1
updated_at: 2025-12-15
tags: [db-integration, commandview, standards, telemetry, positional-encoding]
related_files:
  - .repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/libraries/prune_logs.py
---

# DB Integration — analyze_standards_index_gaps

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

- Describe how the standards gap producer writes positional-encoded artifacts.
- Document the dual-write storage calls (`create_storage`) and marker locations.
- Map `manifest.json` and `telemetry.json` fields to database tables for agent queries.

## System Context

- Producer: `.repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py`
- Viewer/topic: `commandview / standards_index_gaps`
- Output layout (positional encoding):

```text
<reports_root>/commandview/standards_index_gaps/<YYYYMMDD-HHMM>/
  manifest.json
  summary.md
  telemetry.json
```

- Storage API: `.repo_studios/command_center/scripts/libraries/database_integration.py:create_storage`
  - File writes are the primary output.
  - DB writes are dormant unless enabled via config/env; failures do not abort file outputs.

## Agent Instructions

<!-- agents:begin:db_integration_analyze_standards_index_gaps -->
```yaml
viewer_slug: commandview
topic: standards_index_gaps
artifacts:
  - role: manifest
    path: commandview/standards_index_gaps/<YYYYMMDD-HHMM>/manifest.json
  - role: summary
    path: commandview/standards_index_gaps/<YYYYMMDD-HHMM>/summary.md
  - role: telemetry
    path: commandview/standards_index_gaps/<YYYYMMDD-HHMM>/telemetry.json
notes:
  - Prefer querying telemetry.metrics for trend work.
  - Use telemetry.sources for file-level candidate triage.
```
<!-- agents:end:db_integration_analyze_standards_index_gaps -->

## Human Notes

### Marker locations

The producer includes `DB_INTEGRATION_MARKER` tags immediately above each storage write:

- manifest write: `storage.write_manifest(...)`
- summary write: `storage.write_summary(..., format="md")`
- telemetry write: `storage.write_telemetry(...)`

### Pruning

The producer prunes historical run folders under:

- `<reports_root>/commandview/standards_index_gaps/`

using `.repo_studios/command_center/scripts/libraries/prune_logs.py:prune_run_directories(keep=N, current_run=...)`.

## Database Mapping

### report_runs (manifest.json)

`manifest.json` is intended to map to the `report_runs` table (see the documented target schema in `.repo_studios/command_center/scripts/libraries/database_integration.py`).

Suggested mapping:

- `viewer_slug` → `report_runs.viewer_slug`
- `topic` → `report_runs.topic`
- `run_timestamp` (YYYYMMDD-HHMM) + `generated_utc` → `report_runs.run_timestamp` (timestamptz)
- `git_sha` → `report_runs.git_sha`
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

The current `DatabaseStorage.write_telemetry()` stub documents extraction into `test_metrics` primarily for test/coverage telemetry.

For `standards_index_gaps`, recommended approach is:

- Always store full telemetry in `report_artifacts` (`artifact_role='telemetry'`).
- If/when `test_metrics` is extended to support topic-agnostic metrics, map:
  - `telemetry.metric_timestamp` → `test_metrics.metric_timestamp`
  - `telemetry.metrics.total_candidates` → `test_metrics.custom_metrics.total_candidates` (JSONB)
  - `telemetry.metrics.sources_with_candidates` → `test_metrics.custom_metrics.sources_with_candidates` (JSONB)

Until schema support exists, treat `test_metrics` insertion as a planned enhancement for this topic.

## Example SQL (agent queries)

```sql
-- Latest standards gap run for commandview
SELECT *
FROM report_runs
WHERE viewer_slug = 'commandview'
  AND topic = 'standards_index_gaps'
ORDER BY run_timestamp DESC
LIMIT 1;
```

```sql
-- Fetch telemetry artifact for the latest run
SELECT a.content_json
FROM report_runs r
JOIN report_artifacts a ON a.run_id = r.id
WHERE r.viewer_slug = 'commandview'
  AND r.topic = 'standards_index_gaps'
  AND a.artifact_role = 'telemetry'
ORDER BY r.run_timestamp DESC
LIMIT 1;
```

## Reference Prompts

- "Load the latest commandview standards_index_gaps telemetry and summarize top_sources."
- "List sources with candidates and show the first 3 candidate lines per file."

## Update Log

- 2025-12-15 — Added manifest/summary/telemetry mapping, marker notes, pruning notes, and example SQL.
