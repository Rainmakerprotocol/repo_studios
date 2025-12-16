---
title: DB Integration — Standards Index Diff
audience:
  - Agents
  - Developers
role:
  - Automation
owners:
  - Repo Studios
status: draft
version: 1
updated_at: 2025-12-15
tags:
  - database
  - integration
  - standards
  - producer
related_files:
  - .repo_studios/scripts/producers/diff_standards_index.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
---

# DB Integration — diff_standards_index

See `.github/instructions/markdown.instructions.md` for repo-wide rules.

## Goals

- Document where `diff_standards_index.py` places `DB_INTEGRATION_MARKER` tags.
- Describe how the canonical bundle maps to the dormant database write interface.

## System Context

The producer writes a canonical bundle to disk using `create_storage()` from:

- `.repo_studios/command_center/scripts/libraries/database_integration.py`

Current behavior is **file-first**, with database writes **dormant** unless enabled via environment/config.

Bundle layout (positional encoding):

- `.repo_studios/command_center/reports/rawview/standards_index_diff/<YYYYMMDD-HHMM>/`
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`

## Agent Instructions

- Prefer `telemetry.json.payload` as the authoritative structured diff.
- Use `manifest.json.catalog` to enumerate artifacts reliably.

## Human Notes

### Marker locations

In `.repo_studios/scripts/producers/diff_standards_index.py`, the following write sites are tagged:

- `DB_INTEGRATION_MARKER: standards index diff manifest write`
- `DB_INTEGRATION_MARKER: standards index diff summary markdown write`
- `DB_INTEGRATION_MARKER: standards index diff telemetry write`

### Planned table mapping (dormant)

The storage interface documents the intended schema mapping:

- `write_manifest(manifest)` → `report_runs` (one row per run)
- `write_summary(..., format="md")` → `report_artifacts` (role: `summary`, type: `md`)
- `write_telemetry(telemetry)` → `report_artifacts` (role: `telemetry`, type: `json`) and (future)
    extracted metrics

Notes:

- `telemetry.json.metrics` is designed to be a low-cardinality, time-series-friendly subset.
- `telemetry.json.payload` may be stored as JSONB for audit/traceability.

### Example queries (future)

These are illustrative of the intended usage once DB writes are enabled:

```sql
-- Find the most recent standards index diff run.
SELECT *
FROM report_runs
WHERE viewer_slug = 'rawview'
  AND topic = 'standards_index_diff'
ORDER BY run_timestamp DESC
LIMIT 1;
```

```sql
-- Fetch the telemetry artifact for a given run.
SELECT *
FROM report_artifacts
WHERE run_id = :run_id
  AND artifact_role = 'telemetry'
LIMIT 1;
```

## Reference Prompts

- "Give me the latest standards index diff run id and its status."
- "Summarize the `severity_changed` deltas over the last 10 runs."

## Update Log

- 2025-12-15 — Initial DB integration mapping doc created for the canonical bundle producer.
