---
title: DB Integration — Docs Integrity Validation (healthview/docs_integrity_validation)
audience: [Copilot, Agents, Developer]
role: [Operational-Doc, DB-Integration]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 1.0.0
updated: 2025-12-18
tags: [db-integration, healthview, docs-integrity, producer]
related_files:
  - .repo_studios/scripts/producers/verify_docs_integrity.py
  - .repo_studios/docs/automation/verify_docs_integrity.md
  - .repo_studios/tests/tests_producers/test_verify_docs_integrity.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - REPORT_NAMING_STANDARDS.md
---

# DB Integration — Docs Integrity Validation (healthview/docs_integrity_validation)

## Goals

Define the database-facing contract for the docs integrity validation producer so dual-write storage can persist run
metadata, summary markdown, and telemetry metrics.

## System Context

- Producer: `.repo_studios/scripts/producers/verify_docs_integrity.py`
- Output bundle: `.repo_studios/reports/producer_reports/healthview/docs_integrity_validation/<YYYYMMDD-HHMM>/`
- Artifacts: `manifest.json`, `summary.md`, `telemetry.json`
- Storage facade: `create_storage(...)` from `.repo_studios/command_center/scripts/libraries/database_integration.py`

## Write Sites

The producer writes exactly three artifacts through the shared storage abstraction:

- `write_manifest(manifest)`
- `write_summary({"markdown": summary_md}, format="markdown")`
- `write_telemetry(telemetry)`

Each call site is preceded by a `DB_INTEGRATION_MARKER:` comment.

## Schema Mapping

### manifest.json → report_runs

The manifest captures:

- `viewer_slug`: `healthview`
- `topic`: `docs_integrity_validation`
- `run_timestamp`: `YYYYMMDD-HHMM`
- `generated_utc`: ISO-8601 timestamp
- `status`: `ok|fail`
- `inputs`: index path + update/no-table toggles + retention settings
- `summary`: rollups (documents processed, blocks checked, mismatches)
- `catalog`: script identifiers for traceability

### summary.md → report_summaries / report_artifacts

- Artifact kind: markdown
- Primary value: human-readable triage output listing mismatched blocks and remediation notes.

### telemetry.json → test_metrics (plus payload retention)

- `metrics`: compact scalar counts (`documents_processed`, `json_blocks_checked`, `mismatched_blocks`,
  `documents_updated`, etc.).
- `payload`: full docs-integrity report retained for agent drill-down.

## Compatibility Notes

- No `latest_*` pointers are written.
- Downstream consumers should load the latest run directory from
  `.repo_studios/reports/producer_reports/healthview/docs_integrity_validation/` and read `telemetry.json`.

## Update Log

- 2025-12-18: Initial DB integration mapping doc created for the positional bundle migration.
