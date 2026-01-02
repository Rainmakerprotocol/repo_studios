---
title: DB Integration — code_placeholders
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
  - placeholders
related_files:
  - ../../scripts/libraries/database_integration.py
  - ../../../scripts/producers/scan_code_placeholders.py
  - ../../../docs/automation/scan_code_placeholders.md
---

# DB Integration — code_placeholders

## Goals

- Enable dual-write persistence (filesystem always, database optionally) for the
  `healthview/code_placeholders` producer.
- Ensure every persistence call site is discoverable via `DB_INTEGRATION_MARKER:` comments.

## System Context

- Producer: `.repo_studios/scripts/producers/scan_code_placeholders.py`
- Bundle location: `.repo_studios/reports/healthview/producer_reports/code_placeholders/<YYYYMMDD-HHMM>/`
- Storage facade: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage`)

## Agent Instructions

- The producer must write exactly three artifacts via `storage.write_*`:
  - `manifest.json` via `write_manifest(...)`
  - `summary.md` via `write_summary({"markdown": ...}, format="md")`
  - `telemetry.json` via `write_telemetry(...)`
- Each write call site must be preceded by a `DB_INTEGRATION_MARKER:` comment.
- DB writes must be best-effort (warnings only) and never prevent filesystem artifacts from being written.

<!-- agents:begin:db_integration_code_placeholders -->
```yaml
audience: [Copilot, Agents]
checks:
  - id: db-marker-001
    title: Verify marker comments precede each storage write
    severity: error
    match:
      file: .repo_studios/scripts/producers/scan_code_placeholders.py
      patterns:
        - "DB_INTEGRATION_MARKER: placeholder scan manifest write"
        - "DB_INTEGRATION_MARKER: placeholder scan summary markdown write"
        - "DB_INTEGRATION_MARKER: placeholder scan telemetry write"
  - id: db-storage-001
    title: Verify producer uses create_storage facade
    severity: error
    match:
      file: .repo_studios/scripts/producers/scan_code_placeholders.py
      patterns:
        - "create_storage("
```
<!-- agents:end:db_integration_code_placeholders -->

## Human Notes

- The database integration layer is intentionally dormant unless enabled via `REPO_STUDIOS_DB_URL`,
  `REPO_STUDIOS_DB_ENABLED=true`, `.repo_studios/db_config.json`, or an explicit
  `enable_db=True` override.
- The `telemetry.json` includes a `summary` object containing the core payload so downstream
  automation can read a stable snapshot without parsing markdown.

## Update Log

- 2025-12-17 — Added DB integration note for `healthview/code_placeholders` producer.
