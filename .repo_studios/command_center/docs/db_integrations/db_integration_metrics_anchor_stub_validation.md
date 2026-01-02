---
title: DB Integration Mapping — Metrics Anchor Stub Validation
audience: [Copilot, Agents, Developer]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 1.0.0
updated: 2025-12-18
tags: [db-integration, producer, healthview, metrics, anchors]
related_files:
  - .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - REPORT_NAMING_STANDARDS.md
---

# DB Integration Mapping — Metrics Anchor Stub Validation

## Goals

* Record how `validate_metrics_anchor_stubs.py` performs dual writes (filesystem + dormant DB).
* Provide a stable reference for DB wiring during the Repo Studios → main repo integration.

## System Context

The producer emits canonical positional bundles under:

`.repo_studios/reports/healthview/producer_reports/metrics_anchor_stub_validation/<YYYYMMDD-HHMM>/`

Containing exactly:

* `manifest.json`
* `summary.md`
* `telemetry.json`

## Agent Instructions

* Ensure each persistence call is immediately preceded by a `DB_INTEGRATION_MARKER:` comment.
* Keep DB writes best-effort (never block filesystem output).
* Do not introduce `latest_*` pointer artifacts.

## Write Mapping

### Manifest

* File: `manifest.json`
* Writer: `storage.write_manifest(manifest)`
* Marker: `DB_INTEGRATION_MARKER: metrics anchor stub validation manifest`

### Summary

* File: `summary.md`
* Writer: `storage.write_summary({"markdown": summary_md}, format="markdown")`
* Marker: `DB_INTEGRATION_MARKER: metrics anchor stub validation summary markdown`

### Telemetry

* File: `telemetry.json`
* Writer: `storage.write_telemetry(telemetry)`
* Marker: `DB_INTEGRATION_MARKER: metrics anchor stub validation telemetry`

## Notes

* The storage factory is `create_storage(...)` from the shared integration layer.
* If DB connectivity is enabled, DB writes should mirror the filesystem payloads.

## Update Log

* 2025-12-18 — Added initial mapping for canonical bundle + marker locations.
