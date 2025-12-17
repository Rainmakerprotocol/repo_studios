---
title: Undocumented Logic — DB Integration
audience:
  - coding_agent
  - human_developer
role:
  - Operational-Doc
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: active
version: 1.0.0
updated: 2025-12-17
tags:
  - db-integration
  - healthview
  - producer
related_files:
  - ../../scripts/libraries/database_integration.py
  - ../../../scripts/producers/generate_undocumented_logic_report.py
---

# Undocumented Logic — DB Integration

## Goals

* Document how the `healthview/undocumented_logic` producer maps bundle artifacts to the DB write
  abstraction.
* Provide stable query patterns for agents and human operators.

## System Context

* Producer script: `.repo_studios/scripts/producers/generate_undocumented_logic_report.py`
* Bundle location:
  * `.repo_studios/reports/producer_reports/healthview/undocumented_logic/YYYYMMDD-HHMM/`
* Storage abstraction:
  * `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage()`)

## Agent Instructions

* Prefer `telemetry.json.metrics` for rollups (dashboards, regressions, alerting).
* Use `telemetry.json.payload` for drill-down into module-level findings.

## Human Notes

### Bundle artifacts

* `manifest.json`
  * Includes `viewer_slug`, `topic`, `run_timestamp`, `inputs`, and headline counts under `summary`.
* `summary.md`
  * Human-readable digest.
* `telemetry.json`
  * `metrics`: compact counters suitable for DB insertion.
  * `payload`: full structured report with per-module findings.

### DB mapping (conceptual)

This producer uses `DualWriteStorage` so it can remain file-first while the main repo DB wiring is
rolled out. The intended mapping is:

- `manifest.json` → `report_runs` (one row per run)
- `summary.md` → `report_summaries` (one row per run + artifact type)
- `telemetry.json` → `report_telemetry` and extracted `test_metrics`

The exact SQL schema is owned by the main repo; this document describes the fields the producer
already emits.

### Suggested extracted metrics

From `telemetry.json.metrics`:

* `modules_scanned`
* `modules_with_findings`
* `entities_missing_docs`
* `docstring_coverage_percent`

## Reference Prompts

```text
Show me the last 10 `undocumented_logic` runs and trend `docstring_coverage_percent`.
```

```text
For the latest run, list modules with the most missing docstrings and show sample qualified names.
```

## Update Log

* 2025-12-17 — Initial mapping doc for undocumented logic producer canonical bundle + storage writes.
