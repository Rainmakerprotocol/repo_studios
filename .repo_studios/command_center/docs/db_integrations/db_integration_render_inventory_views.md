---
title: DB Integration — Inventory Overview (healthview/inventory_overview)
audience: [Copilot, Agents, Developer]
role: [Operational-Doc, DB-Integration]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 1.0.0
updated: 2025-12-17
tags: [db-integration, healthview, inventory, producer]
related_files:
  - .repo_studios/scripts/producers/render_inventory_views.py
  - .repo_studios/docs/automation/render_inventory_views.md
  - .repo_studios/scripts/producers/check_inventory_health.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - REPORT_NAMING_STANDARDS.md
---

# DB Integration — Inventory Overview (healthview/inventory_overview)

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

Define the database-facing contract for the Inventory Overview producer so dual-write storage can persist run metadata,
summary markdown, and telemetry payloads in a stable schema.

## System Context

- Producer: `.repo_studios/scripts/producers/render_inventory_views.py`
- Output bundle: `.repo_studios/reports/producer_reports/healthview/inventory_overview/<YYYYMMDD-HHMM>/`
- Artifacts: `manifest.json`, `summary.md`, `telemetry.json`
- Storage facade: `create_storage(...)` from `.repo_studios/command_center/scripts/libraries/database_integration.py`

## Write Sites

The producer writes exactly three artifacts through the shared storage abstraction:

- `write_manifest(manifest)`
- `write_summary({"markdown": summary_md}, format="md")`
- `write_telemetry(telemetry)`

Each call site is preceded by a `DB_INTEGRATION_MARKER` comment.

## Schema Mapping

### manifest.json → report_runs

High-level fields:

- `viewer_slug`: `healthview`
- `topic`: `inventory_overview`
- `run_timestamp`: `YYYYMMDD-HHMM`
- `generated_at`: ISO-8601 UTC timestamp
- `status`: `ok|error`
- `catalog`: includes `scripts.inventory.render_inventory_views`
- `inputs`: JSON object (schema root, views dir, output root, repo root)

### summary.md → report_artifacts

- Artifact role: `summary`
- Artifact type: `md`
- Content: the markdown digest rendered from the inventory overview counts, leading tags, and consumer list.

### telemetry.json → test_metrics (plus payload retention)

Telemetry is designed to support both quick dashboards and downstream validation:

- `summary`: includes counts keyed by `asset_kind`, `maturity`, `status`, consumers, and top tags.
- `counts`: includes total/docs/scripts/tests rollups.
- `views`: includes the rendered docs/scripts/tests view payloads for agent queries.

## Compatibility Notes

- No `latest_*` pointers are written.
- Compatibility stubs under `.repo_studios/inventory_schema/views/` redirect to the topic directory
  `reports/producer_reports/healthview/inventory_overview`.
- Consumers that need the newest data should scan the timestamp directories under the topic directory and read
  `telemetry.json`.

## Update Log

- 2025-12-17: Initial DB integration mapping doc created for the positional bundle migration.
