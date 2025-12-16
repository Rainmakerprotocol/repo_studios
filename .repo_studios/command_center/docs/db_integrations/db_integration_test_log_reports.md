---
title: DB Integration — Test Log Reports
audience:
  - coding_agent
  - human_developer
role:
  - Operational-Doc
  - Memory-Source
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: active
version: 1.0.0
updated: 2025-12-15
tags:
  - db
  - integration
  - rawview
  - pytest
related_files:
  - ../../scripts/libraries/database_integration.py
  - ../../../scripts/producers/collect_test_log_reports.py
  - ../../../tests/tests_producers/test_collect_test_log_reports.py
---

# Database Integration Documentation — Test Log Reports

## Goals

* Capture the database mapping for the canonical report bundle emitted by `collect_test_log_reports.py`.
* Keep the integration dormant unless explicitly enabled via `REPO_STUDIOS_DB_ENABLED` / `REPO_STUDIOS_DB_URL`.

## System Context

* **Script:** `.repo_studios/scripts/producers/collect_test_log_reports.py`
* **Tier:** producer
* **Viewer:** `rawview`
* **Topic:** `test_log_reports`
* **Bundle path:** `.repo_studios/command_center/reports/rawview/test_log_reports/<YYYYMMDD-HHMM>/`
* **Artifacts:** `manifest.json`, `summary.md`, `telemetry.json`

## Agent Instructions

* Use the bundle’s `run_timestamp` (folder slug) as the primary time key.
* Treat `telemetry.json.metrics` as the source of time-series columns; treat `telemetry.json.payload` as JSONB detail.

## Database Mapping

### Primary Tables

```sql
-- Per-run identity and inputs
CREATE TABLE report_runs (
    id BIGSERIAL PRIMARY KEY,
    viewer_slug VARCHAR(50) NOT NULL,
    topic VARCHAR(100) NOT NULL,
    run_timestamp TIMESTAMPTZ NOT NULL,
    git_sha VARCHAR(40),
    repo_root TEXT,
    status VARCHAR(20),
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    inputs JSONB,
    catalog JSONB,

    UNIQUE(viewer_slug, topic, run_timestamp)
);

-- Full artifact storage (JSON + Markdown)
CREATE TABLE report_artifacts (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES report_runs(id) ON DELETE CASCADE,
    artifact_role VARCHAR(50) NOT NULL,      -- 'manifest' | 'summary' | 'telemetry'
    artifact_type VARCHAR(10) NOT NULL,      -- 'json' | 'md'
    file_path TEXT,
    file_size_bytes BIGINT,
    content_json JSONB,
    content_text TEXT,
    checksum VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Extracted metrics for time-series queries
CREATE TABLE test_metrics (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES report_runs(id) ON DELETE CASCADE,
    metric_timestamp TIMESTAMPTZ NOT NULL,

    total_tests INTEGER,
    passed_tests INTEGER,
    failed_tests INTEGER,
    skipped_tests INTEGER,
    xfailed_tests INTEGER,
    error_tests INTEGER,

    warnings_total INTEGER,
    tracebacks INTEGER,
    slow_tests_count INTEGER,

    details JSONB
);
```

### Artifact → Table Mapping

| Artifact | Role | Tables | Notes |
| --- | --- | --- | --- |
| `manifest.json` | manifest | `report_runs`, `report_artifacts` | Primary run record + full JSON backup |
| `summary.md` | summary | `report_artifacts` | Human-readable digest |
| `telemetry.json` | telemetry | `report_artifacts`, `test_metrics` | Full telemetry backup + extracted metrics |

### Telemetry Extraction

Source fields (from `telemetry.json`):

* `metrics.tests_total` → `test_metrics.total_tests`
* `metrics.tests_passed` → `test_metrics.passed_tests`
* `metrics.tests_failed` → `test_metrics.failed_tests`
* `metrics.tests_skipped` → `test_metrics.skipped_tests`
* `metrics.tests_xfailed` → `test_metrics.xfailed_tests`
* `metrics.tests_errors` → `test_metrics.error_tests`
* `metrics.warnings_total` → `test_metrics.warnings_total`
* `metrics.tracebacks` → `test_metrics.tracebacks`
* `metrics.slow_tests_count` → `test_metrics.slow_tests_count`
* `payload` → `test_metrics.details` (JSONB)

## Reference Prompts

```text
Given the latest rawview/test_log_reports telemetry bundle, summarize warning trends and list the top slow tests.
```

## Update Log

* 2025-12-15 — Initial DB integration mapping for `collect_test_log_reports.py` canonical bundle.
