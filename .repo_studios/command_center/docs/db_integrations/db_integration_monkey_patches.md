---
title: DB Integration — monkey_patches
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: approved
version: 1.0.0
updated: 2025-12-17
tags:
  - db
  - integration
  - producers
  - healthview
  - monkey_patches
related_files:
  - ../../scripts/libraries/database_integration.py
  - ../../../scripts/producers/scan_monkey_patches.py
  - ../../../docs/automation/scan_monkey_patches.md
---

# DB Integration — monkey_patches

## Goals

* Enable dual-write persistence (filesystem always, database optionally) for the `healthview/monkey_patches` producer.
* Ensure every persistence call site is discoverable via `DB_INTEGRATION_MARKER:` comments.

## System Context

* Producer: `.repo_studios/scripts/producers/scan_monkey_patches.py`
* Bundle location: `.repo_studios/reports/healthview/producer_reports/monkey_patches/<YYYYMMDD-HHMM>/`
* Storage facade: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage`)

## Agent Instructions

* The producer must write exactly three artifacts via `storage.write_*`:
  * `manifest.json` via `write_manifest(...)`
  * `summary.md` via `write_summary({"markdown": ...}, format="md")`
  * `telemetry.json` via `write_telemetry(...)`
* Each write call site must be preceded by a `DB_INTEGRATION_MARKER:` comment.
* DB writes must be best-effort (warnings only) and never prevent filesystem artifacts from being written.

<!-- agents:begin:db_integration_monkey_patches -->
```yaml
audience: [Copilot, Agents]
checks:
  - id: db-marker-001
    title: Verify marker comments precede each storage write
    severity: error
    match:
      file: .repo_studios/scripts/producers/scan_monkey_patches.py
      patterns:
        - "DB_INTEGRATION_MARKER: Persist manifest bundle (report_runs + report_artifacts)"
        - "DB_INTEGRATION_MARKER: Persist human-readable report summary (report_artifacts)"
        - "DB_INTEGRATION_MARKER: Persist telemetry payload + extracted metrics (report_artifacts + test_metrics)"
  - id: db-storage-001
    title: Verify producer uses create_storage facade
    severity: error
    match:
      file: .repo_studios/scripts/producers/scan_monkey_patches.py
      patterns:
        - "create_storage("
```
<!-- agents:end:db_integration_monkey_patches -->

## Human Notes

* The database integration layer is intentionally dormant unless enabled via `REPO_STUDIOS_DB_URL`, `REPO_STUDIOS_DB_ENABLED=true`, `.repo_studios/db_config.json`, or an explicit `enable_db=True` override.
* `manifest.json` stores the structured finding list under `payload.findings` so downstream consumers can avoid parsing markdown.
* `telemetry.json` stores stable, small metrics suitable for trend queries.

## Update Log

* 2025-12-17 — Added DB integration note for `healthview/monkey_patches` producer.
