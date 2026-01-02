---
title: DB Integration — Import Graph (healthview/import_graph)
audience: [Copilot, Agents, Developer]
role: [Operational-Doc, DB-Integration]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 1.0.0
updated: 2025-12-16
tags: [db-integration, healthview, import-graph, producer]
related_files:
  - .repo_studios/scripts/producers/generate_import_graph_report.py
  - .repo_studios/docs/automation/generate_import_graph_report.md
  - .repo_studios/scripts/producers/validate_import_boundaries.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - REPORT_NAMING_STANDARDS.md
---

# DB Integration — Import Graph (healthview/import_graph)

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

Define the database-facing contract for the Import Graph producer so dual-write storage can persist the run metadata,
summary markdown, and telemetry payload in a stable schema.

## System Context

- Producer: `.repo_studios/scripts/producers/generate_import_graph_report.py`
- Output bundle: `.repo_studios/reports/healthview/producer_reports/import_graph/<YYYYMMDD-HHMM>/`
- Artifacts: `manifest.json`, `summary.md`, `telemetry.json`
- Storage facade: `create_storage(...)` from `.repo_studios/command_center/scripts/libraries/database_integration.py`

## Write Sites

The producer writes exactly three artifacts through the shared storage abstraction:

- `write_manifest(manifest)`
- `write_summary({"markdown": summary_md}, format="markdown")`
- `write_telemetry(telemetry)`

Each call site is preceded by a `DB_INTEGRATION_MARKER` comment.

## Schema Mapping

### manifest.json → report_runs

Intended shape (high-level):

- `viewer_slug`: `healthview`
- `topic`: `import_graph`
- `run_timestamp`: `YYYYMMDD-HHMM`
- `generated_utc`: ISO-8601 timestamp (stored in telemetry)
- `status`: `ok|failed`
- `inputs`: JSON object (repo root, owned roots, retention)
- `catalog`: list of artifact descriptors

### summary.md → report_summaries / report_artifacts

- Artifact kind: markdown
- Primary value: the bundle markdown rendered by the producer.

### telemetry.json → test_metrics (plus payload retention)

- `metrics`: compact scalar metrics for quick dashboards (`module_count`, `edge_count`, `cycle_count`, etc.).
- `payload`: full legacy report payload including the adjacency `graph`.

## Compatibility Notes

- No `latest_*` pointers are written.
- Downstream consumers should load the latest run directory from
  `.repo_studios/reports/healthview/producer_reports/import_graph/` and read `telemetry.json`.

## Update Log

- 2025-12-16: Initial DB integration mapping doc created for the positional bundle migration.
