---
title: DB Integration Notes — Lizard Report
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: active
version: 1.0.0
updated: 2025-12-16
tags:
  - db-integration
  - healthview
  - lizard
related_files:
  - ../../scripts/producers/generate_lizard_report.py
  - ../../command_center/scripts/libraries/database_integration.py
---

# DB Integration Notes — Lizard Report

## Goals

* Document how the lizard producer writes bundle artifacts via the dual-write storage layer.
* Ensure write sites are searchable and auditable via `DB_INTEGRATION_MARKER:` comments.

## System Context

The lizard producer writes its positional bundle under:

* `.repo_studios/reports/healthview/producer_reports/lizard_complexity/<YYYYMMDD-HHMM>/`

The producer obtains a storage backend via `libraries.database_integration.create_storage(...)`, which:

* Always writes artifacts to disk (primary source of truth during transition).
* Optionally attempts parallel DB writes when enabled via `.repo_studios/db_config.json` or environment configuration.

## Agent Instructions

* Do not remove `DB_INTEGRATION_MARKER:` comments above artifact write calls.
* DB write failures must not abort the producer; they should be logged as warnings.

## Write Sites

The producer writes three artifacts, each guarded by an explicit marker comment:

* `manifest.json` via `storage.write_manifest(...)`
* `summary.md` via `storage.write_summary(..., format="markdown")`
* `telemetry.json` via `storage.write_telemetry(...)`

## Human Notes

* `telemetry.json.metrics` is intended for lightweight indexing.
* `telemetry.json.payload` holds the full report content (including a truncated raw output excerpt).

## Update Log

* 2025-12-16 — Initial DB integration note for `healthview/lizard_report` producer bundle.
