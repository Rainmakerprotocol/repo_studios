---
title: DB Integration — Doc Index (healthview/doc_index)
audience: [Copilot, Agents, Developer]
role: [Operational-Doc, DB-Integration]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 1.0.0
updated: 2025-12-16
tags: [db-integration, healthview, doc-index, producer]
related_files:
  - .repo_studios/scripts/producers/generate_doc_index.py
  - .repo_studios/docs/automation/generate_doc_index.md
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - REPORT_NAMING_STANDARDS.md
---

# DB Integration — Doc Index (healthview/doc_index)

## Goals

Define the database-facing contract for the Doc Index producer so dual-write storage can persist the run metadata,
summary markdown, and telemetry payload in a stable schema.

## System Context

- Producer: `.repo_studios/scripts/producers/generate_doc_index.py`
- Output bundle: `.repo_studios/reports/producer_reports/healthview/doc_index/<YYYYMMDD-HHMM>/`
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
- `topic`: `doc_index`
- `run_timestamp`: `YYYYMMDD-HHMM`
- `generated_utc`: ISO-8601 timestamp
- `status`: `ok|error`
- `inputs`: JSON object (repo root, exclusions, retention, requested db target)
- `catalog`: list of producer identifiers

### summary.md → report_summaries / report_artifacts

- Artifact kind: markdown
- Primary value: the bundle markdown rendered by the producer.
- Contains embedded JSON/YAML/CSV panels for human review.

### telemetry.json → test_metrics (plus payload retention)

- `metrics`: compact scalar metrics for quick dashboards.
- `payload`: full doc index dataset (documents, advisories, scanner rules).

## Compatibility Notes

- No `latest_*` pointers are written.
- Downstream consumers should load the latest run directory from
  `.repo_studios/reports/producer_reports/healthview/doc_index/` and read `telemetry.json`.

## Update Log

- 2025-12-16: Initial DB integration mapping doc created for the positional bundle migration.
