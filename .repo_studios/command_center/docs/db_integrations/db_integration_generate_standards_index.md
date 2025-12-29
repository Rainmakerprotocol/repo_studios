---
title: DB Integration — Standards Index Producer
audience:
  - Agents
  - Developers
role:
  - Automation
owners:
  - Repo Studios
status: draft
version: 1
updated_at: 2025-12-17
tags:
  - database
  - integration
  - standards
  - producer
related_files:
  - .repo_studios/scripts/producers/generate_standards_index.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — generate_standards_index

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

See `.github/instructions/markdown.instructions.md` for repo-wide rules.

## Goals

- Document where `generate_standards_index.py` places `DB_INTEGRATION_MARKER` tags.
- Describe how the canonical bundle maps to the dormant database write interface.

## System Context

The producer builds a standards index snapshot (YAML) and emits a canonical bundle using `create_storage()` from:

- `.repo_studios/command_center/scripts/libraries/database_integration.py`

Current behavior is **file-first**, with database writes **dormant** unless enabled via environment/config.

Bundle layout (positional encoding):

- `.repo_studios/reports/producer_reports/rawview/standards_index/<YYYYMMDD-HHMM>/`
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`

## Agent Instructions

- Prefer `telemetry.json.metrics` for trendable time-series fields.
- Prefer `telemetry.json.payload` as the authoritative structured payload for audits.
- Use `manifest.json.catalog` to enumerate artifacts reliably.

## Human Notes

### Marker locations

In `.repo_studios/scripts/producers/generate_standards_index.py`, the following write sites are tagged:

- `DB_INTEGRATION_MARKER: write manifest.json (report_runs)`
- `DB_INTEGRATION_MARKER: write summary.md (report_summaries)`
- `DB_INTEGRATION_MARKER: write telemetry.json + extracted metrics (test_metrics)`

### Planned table mapping (dormant)

The storage interface documents the intended schema mapping:

- `write_manifest(manifest)` → `report_runs` (one row per run)
- `write_summary({"markdown": ...}, format="markdown")` → `report_artifacts` (role: `summary`, type: `md`)
- `write_telemetry(telemetry)` → `report_artifacts` (role: `telemetry`, type: `json`) and (future)
    extracted metrics

Notes:

- `telemetry.json.metrics` is designed to be a low-cardinality subset (for time-series queries).
- `telemetry.json.payload` may be stored as JSONB for audit/traceability.

### Example queries (future)

These are illustrative of the intended usage once DB writes are enabled:

```sql
-- Find the most recent standards_index producer run.
SELECT *
FROM report_runs
WHERE viewer_slug = 'rawview'
  AND topic = 'standards_index'
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

- "Give me the latest standards index run id and its status."
- "Graph rule_count and pending_written over the last 10 runs."

## Update Log

- 2025-12-17 — Initial DB integration mapping doc created for the standards index producer.
