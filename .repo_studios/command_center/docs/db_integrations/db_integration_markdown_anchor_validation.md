---
title: DB Integration — Markdown Anchor Validation (healthview/markdown_anchor_validation)
audience: [Copilot, Agents, Developer]
role: [Operational-Doc, DB-Integration]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 1.0.0
updated: 2025-12-18
tags: [db-integration, healthview, markdown-anchor-validation, producer]
related_files:
  - .repo_studios/scripts/producers/validate_markdown_anchors.py
  - .repo_studios/docs/automation/validate_markdown_anchors.md
  - .repo_studios/tests/tests_producers/test_validate_markdown_anchors.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - REPORT_NAMING_STANDARDS.md
---

# DB Integration — Markdown Anchor Validation (healthview/markdown_anchor_validation)

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

Define the database-facing contract for the markdown anchor validation producer so dual-write storage can persist run
metadata, summary markdown, and telemetry metrics.

## System Context

- Producer: `.repo_studios/scripts/producers/validate_markdown_anchors.py`
- Output bundle: `.repo_studios/reports/producer_reports/healthview/markdown_anchor_validation/<YYYYMMDD-HHMM>/`
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
- `topic`: `markdown_anchor_validation`
- `run_timestamp`: `YYYYMMDD-HHMM`
- `generated_utc`: ISO-8601 timestamp
- `status`: `ok|fail`
- `inputs`: scan root + glob patterns + retention settings
- `summary`: rollups (files scanned, issue count)
- `catalog`: script identifier for traceability

### summary.md → report_summaries / report_artifacts

- Artifact kind: markdown
- Primary value: human-readable triage output for broken anchors and missing links.

### telemetry.json → test_metrics (plus payload retention)

- `metrics`: compact scalar counts (`files_scanned`, `links_checked`, `missing_file_count`, `missing_anchor_count`).
- `payload.report`: full issue list retained for agent drill-down.

## Compatibility Notes

- No `latest_*` pointers are written.
- Downstream consumers should load the latest run directory from
  `.repo_studios/reports/producer_reports/healthview/markdown_anchor_validation/` and read `telemetry.json`.

## Update Log

- 2025-12-18: Initial DB integration mapping doc created for the positional bundle migration.
