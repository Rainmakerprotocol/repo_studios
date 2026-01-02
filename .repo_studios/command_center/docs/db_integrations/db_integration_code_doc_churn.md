---
title: Code Doc Churn — DB Integration
audience:
  - coding_agent
  - human_developer
role:
  - Operational-Doc
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: active
version: 1.0.0
updated: 2025-12-16
tags:
  - db-integration
  - healthview
  - producer
related_files:
  - ../../scripts/libraries/database_integration.py
  - ../../../scripts/producers/generate_code_doc_churn_report.py
---

# Code Doc Churn — DB Integration

## Goals

* Document how the `healthview/code_doc_churn` producer maps bundle artifacts to the DB write
  abstraction.
* Provide stable query patterns for agents and human operators.

## System Context

* Producer script: `.repo_studios/scripts/producers/generate_code_doc_churn_report.py`
* Bundle location:
  * `.repo_studios/reports/healthview/producer_reports/code_doc_churn/YYYYMMDD-HHMM/`
* Storage abstraction:
  * `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage()`)

## Agent Instructions

* Prefer `telemetry.json.metrics` for time-series or dashboard calculations.
* Use `telemetry.json.payload` for drill-down (module lists, paths, authors, commit hashes).

## Human Notes

### Bundle artifacts

* `manifest.json`
  * Includes `viewer_slug`, `topic`, `run_timestamp`, `inputs`, and headline counts under `summary`.
* `summary.md`
  * Human-readable digest.
* `telemetry.json`
  * `metrics`: flat counters suitable for DB insertion.
  * `payload`: full legacy payload (structured report) for agent drill-down.

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

* `modules_missing_docs`
* `modules_with_docs`
* `commits_examined`
* `distinct_authors`
* `allowlisted_modules`

## Reference Prompts

```text
Show me the last 10 `code_doc_churn` runs and trend `modules_missing_docs`.
```

```text
For the latest run, list the top modules missing docs and include sample code paths.
```

## Update Log

* 2025-12-16 — Initial mapping doc for churn producer canonical bundle + storage writes.
