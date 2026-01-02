---
title: DB Integration — aggregate_docs_health_signals.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-01-02
tags: [db-integration, aggregator, healthview, docs-health-signals]
related_files:
  - .repo_studios/scripts/aggregators/aggregate_docs_health_signals.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — aggregate_docs_health_signals.py

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

- Document the database integration markers and intended table mappings for the docs health signals aggregator.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Aggregator script: `.repo_studios/scripts/aggregators/aggregate_docs_health_signals.py`
- Topic slug: `docs_health_signals`
- Output contract (file system): `.repo_studios/reports/healthview/aggregator_reports/docs_health_signals/<YYYYMMDD-HHMM>/`
- Artifacts: `manifest.json`, `summary.md`, `telemetry.json`, `signals.tsv`, `signals.csv`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)

## Upstream Producer Dependencies

This aggregator consolidates signals from multiple upstream producers:

| Producer | Default Path | Signal Category |
| --- | --- | --- |
| `generate_code_doc_churn_report.py` | `.repo_studios/reports/healthview/producer_reports/code_doc_churn` | Documentation Freshness |
| `generate_undocumented_logic_report.py` | `.repo_studios/reports/healthview/producer_reports/undocumented_logic` | Coverage |
| `generate_anchor_inventory.py` | `.repo_studios/reports/healthview/producer_reports/anchor_inventory` | Anchor Inventory |
| `validate_markdown_anchors.py` | `.repo_studios/reports/healthview/producer_reports/markdown_anchor_validation` | Anchor Validation |
| `verify_docs_integrity.py` | `.repo_studios/reports/healthview/producer_reports/docs_integrity_validation` | Docs Integrity |
| `validate_metrics_anchor_stubs.py` | `.repo_studios/reports/healthview/producer_reports/metrics_anchor_stub_validation` | Metrics Stubs |
| Code Placeholders | `.repo_studios/reports/healthview/producer_reports/code_placeholders` | Hygiene |
| Monkey Patches | `.repo_studios/reports/healthview/producer_reports/monkey_patches` | Hygiene |

## CLI Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--repo-root` | (inferred) | Repository root override |
| `--output-dir` | `.repo_studios/reports/healthview/aggregator_reports/docs_health_signals` | Output directory |
| `--churn-report` | (default path) | Path to churn input |
| `--undocumented-report` | (default path) | Path to undocumented logic input |
| `--anchor-inventory` | (default path) | Path to anchor inventory input |
| `--anchor-validation` | (default path) | Path to markdown anchor validation report |
| `--docs-integrity` | (default path) | Path to docs integrity report |
| `--metrics-stub` | (default path) | Path to metrics anchor stub validation report |
| `--placeholder-report` | (default path) | Path to code placeholder scan report |
| `--monkey-patch-report` | (default path) | Path to monkey patch scan report |
| `--artifacts-to-keep` | `5` | Retention count for timestamped runs |
| `--skip-hygiene` | `false` | Skip hygiene signal blending |
| `--log-level` | `INFO` | Logging verbosity |

## Agent Instructions

<!-- agents:begin:db_integration_aggregate_docs_health_signals -->
```yaml
aggregator:
  viewer_slug: healthview
  topic: docs_health_signals
artifacts:
  - manifest.json
  - summary.md
  - telemetry.json
  - signals.tsv
  - signals.csv
markers:
  - description: Persist aggregated manifest (report_runs + report_artifacts)
    method: storage.write_manifest
  - description: Persist human-readable summary (report_artifacts)
    method: storage.write_summary
  - description: Persist telemetry payload (report_artifacts + aggregated_metrics)
    method: storage.write_telemetry
signal_categories:
  - freshness: Documentation Freshness (churn correlation)
  - coverage: Documentation Coverage (undocumented logic)
  - anchor_inventory: Anchor Inventory Health
  - anchor_validation: Anchor Link Validation
  - docs_integrity: Docs Integrity Blocks
  - metrics_stubs: Metrics Anchor Stubs
  - hygiene: Code Hygiene (placeholders, monkey patches)
```
<!-- agents:end:db_integration_aggregate_docs_health_signals -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `manifest.json`
  - Key fields: `viewer_slug`, `topic`, `run_timestamp`, `generated_utc`, `status`

- `report_artifacts`
  - Source: `manifest.json`, `summary.md`, `telemetry.json`, `signals.tsv`, `signals.csv`
  - Roles:
    - `manifest_json` (JSON — aggregator manifest)
    - `summary_md` (Markdown — consolidated health digest)
    - `telemetry_json` (JSON — full telemetry)
    - `signals_tsv` (TSV — signal scores for spreadsheet import)
    - `signals_csv` (CSV — signal scores for programmatic consumption)

- `aggregated_metrics`
  - Source: `telemetry.json` → `metrics`
  - Suggested metrics:
    - `overall_health_score`
    - `freshness_score`
    - `coverage_score`
    - `anchor_health_score`
    - `integrity_score`
    - `hygiene_score`
    - `signals_count`
    - `critical_signals_count`

- `signal_scores`
  - Source: `signals.tsv` / `signals.csv`
  - Key fields: `category`, `title`, `score`, `status`, `notes`

## Human Notes

- This aggregator consolidates metrics from 8 upstream producers into a unified docs health view.
- Each signal category computes a normalized score (0-100) with status thresholds (healthy ≥80, warning ≥60, critical <60).
- The `--skip-hygiene` flag allows excluding placeholder/monkey-patch signals when those producers haven't run.
- Retention is controlled by `--artifacts-to-keep` and enforced via `write_report_artifacts`.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.

## Reference Prompts

- "Run marker audit and confirm aggregate_docs_health_signals.py appears with 3 markers"
- "Show the overall docs health score from the latest aggregation"
- "List signals in critical status"

## Update Log

| Date | Author | Changes |
| --- | --- | --- |
| 2025-01-02 | repo_studios_ai | Initial creation from code inspection during Stage 2.1 Pass 3 |
