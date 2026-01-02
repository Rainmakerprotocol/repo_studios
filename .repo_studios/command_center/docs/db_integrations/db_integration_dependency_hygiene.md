---
title: Dependency Hygiene — DB Integration Mapping
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
  - dependency-hygiene
related_files:
  - ../../scripts/producers/generate_dependency_hygiene_report.py
  - ../../tests/tests_producers/test_generate_dependency_hygiene_report.py
---

# Dependency Hygiene — DB Integration Mapping

<!-- markdownlint-disable MD013 -->
<!-- Technical integration spec with inline code mappings; line length exempt -->

## Goals

* Define how the Dependency Hygiene producer maps its canonical bundle outputs into DB-ready shapes.
* Keep the mapping stable while allowing the producer to preserve a legacy payload for drill-down.

## System Context

The producer writes canonical positional bundles under:

* `.repo_studios/reports/healthview/producer_reports/dependency_hygiene/<YYYYMMDD-HHMM>/`

Each run folder contains exactly:

* `manifest.json`
* `summary.md`
* `telemetry.json`

## Agent Instructions

* Ingest the bundle as a single “run” entity keyed by `(viewer_slug, topic, run_timestamp_utc)`.
* Use `telemetry.json.metrics` for structured DB columns.
* Store `telemetry.json.payload` as semi-structured JSON for debugging, backfills, and future metric extraction.

## Mapping

### Run identity

Source: `manifest.json`

* `viewer_slug` → `healthview`
* `topic` → `dependency_hygiene`
* `run_timestamp_utc` → the `<YYYYMMDD-HHMM>` folder name (UTC)

### Core metrics

Source: `telemetry.json.metrics`

Recommended columns (names are illustrative; use your project’s canonical naming):

* `status` (string)
* `issue_count` (int)
* `requirements_scanned` (int)
* `pyproject_scanned` (bool)
* `issue_counts` (json) — list of `{kind, count}`

### Full payload

Source: `telemetry.json.payload`

Store as JSON blob:

* `payload.schema_version`
* `payload.generated_utc`
* `payload.repo_root`
* `payload.requirements_patterns`
* `payload.requirements_files`
* `payload.pyproject_path`
* `payload.issues[]`

## Human Notes

* The producer is expected to evolve metric extraction over time; keep `payload` intact to preserve backwards compatibility.
* If you need per-issue rows, derive them from `payload.issues` with a foreign key to the run identity.

## Update Log

* 2025-12-16 — Initial DB mapping for canonical Dependency Hygiene producer bundle.
