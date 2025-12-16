---
title: DB Integration — analyze_test_hardening
audience: [Copilot, Agents, Developers]
role: [Documentation, Integration]
owners: [command_center]
status: active
version: 1
updated_at: 2025-12-15
tags: [db-integration, healthview, tests, hardening, telemetry, positional-encoding]
related_files:
  - .repo_studios/scripts/producers/analyze_test_hardening.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/libraries/prune_logs.py
  - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py
---

# DB Integration — analyze_test_hardening

See `.github/instructions/markdown.instructions.md` for repo-wide Markdown rules (last reviewed 2025-12-15).

## Goals

- Describe how the test hardening producer writes positional-encoded artifacts.
- Document the dual-write storage calls (`create_storage`) and marker locations.
- Map `manifest.json` and `telemetry.json` fields to database tables for agent queries.

## System Context

- Producer: `.repo_studios/scripts/producers/analyze_test_hardening.py`
- Viewer/topic: `healthview / test_hardening`
- Output layout (positional encoding):

```text
<reports_root>/healthview/test_hardening/<YYYYMMDD-HHMM>/
  manifest.json
  summary.md
  telemetry.json
```

- Storage API: `.repo_studios/command_center/scripts/libraries/database_integration.py:create_storage`
  - File writes are the primary output.
  - DB writes are dormant unless enabled via config/env; failures do not abort file outputs.

## Agent Instructions

<!-- agents:begin:db_integration_analyze_test_hardening -->
```yaml
viewer_slug: healthview
topic: test_hardening
artifacts:
  - role: manifest
    path: healthview/test_hardening/<YYYYMMDD-HHMM>/manifest.json
  - role: summary
    path: healthview/test_hardening/<YYYYMMDD-HHMM>/summary.md
  - role: telemetry
    path: healthview/test_hardening/<YYYYMMDD-HHMM>/telemetry.json
notes:
  - Prefer telemetry.metrics for trend work.
  - Use telemetry.components.hardening.top_priority for triage.
```
<!-- agents:end:db_integration_analyze_test_hardening -->

## Human Notes

### Marker locations

The producer includes `DB_INTEGRATION_MARKER` tags immediately above each storage write:

- manifest write: `storage.write_manifest(...)`
- summary write: `storage.write_summary(..., format="md")`
- telemetry write: `storage.write_telemetry(...)`

### Pruning

The producer prunes historical run folders under:

- `<reports_root>/healthview/test_hardening/`

using `.repo_studios/command_center/scripts/libraries/prune_logs.py:prune_run_directories(keep=N, current_run=...)`.

## Database Mapping

### report_runs (manifest.json)

`manifest.json` is intended to map to the `report_runs` table (see the documented target schema in `.repo_studios/command_center/scripts/libraries/database_integration.py`).

Suggested mapping:

- `viewer_slug` → `report_runs.viewer_slug`
- `topic` → `report_runs.topic`
- `run_timestamp` (YYYYMMDD-HHMM) + `generated_at` → `report_runs.run_timestamp` (timestamptz)
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

The current `DatabaseStorage.write_telemetry()` stub is oriented around extracting time-series
metrics into `test_metrics`.

Recommended extraction for test hardening:

- `telemetry.run_timestamp` → `test_metrics.metric_timestamp`
- `telemetry.metrics` → `test_metrics.hardening_issues` (JSONB)
- Optionally extend extraction later with:
  - `total_files`, `total_test_functions`, `total_issues`
  - severity breakdown (`high|medium|low`)

Until the schema is fully wired, treat `test_metrics` insertion as a planned enhancement; the full
telemetry artifact should always be stored in `report_artifacts`.

## Example SQL (agent queries)

```sql
-- Latest test hardening run for healthview
SELECT *
FROM report_runs
WHERE viewer_slug = 'healthview'
  AND topic = 'test_hardening'
ORDER BY run_timestamp DESC
LIMIT 1;
```

```sql
-- Fetch telemetry artifact for the latest run
SELECT a.content_json
FROM report_runs r
JOIN report_artifacts a ON a.run_id = r.id
WHERE r.viewer_slug = 'healthview'
  AND r.topic = 'test_hardening'
  AND a.artifact_role = 'telemetry'
ORDER BY r.run_timestamp DESC
LIMIT 1;
```

## Reference Prompts

- "Load the latest healthview test_hardening telemetry and list the top_priority files."
- "Show the severity totals and top 5 categories driving hardening issues."

## Update Log

- 2025-12-15 — Added positional-encoding layout, marker notes, pruning notes, and DB mapping guidance.
