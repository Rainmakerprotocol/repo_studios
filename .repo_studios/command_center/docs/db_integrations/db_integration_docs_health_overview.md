---
title: DB Integration — run_docs_health_overview.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-01-02
tags: [db-integration, orchestrator, healthview, docs-health]
related_files:
  - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — run_docs_health_overview.py

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

- Document the database integration markers and intended table mappings for the Docs Health Overview orchestrator.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Orchestrator script: `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py`
- Viewer slug: `orchestrator_reports`
- Topic: `docs_health` (HEALTHVIEW_TOPIC constant)
- Topic slug: `docs-health` (TOPIC_SLUG constant for catalog registration)
- Output contract (file system): `.repo_studios/reports/healthview/orchestrator_reports/docs_health/<YYYYMMDD-HHMM>/{manifest.json,summary.md,telemetry.json}`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)
- Runtime: ~6-8 minutes (invokes 8 upstream scripts)

## Invoked Scripts

The orchestrator coordinates execution of the following upstream scripts:

| Order | Script | Path | Role | Topic |
| --- | --- | --- | --- | --- |
| 1 | `generate_doc_index.py` | `.repo_studios/scripts/producers/` | producer | doc_index |
| 2 | `generate_anchor_inventory.py` | `.repo_studios/scripts/producers/` | producer | anchor_inventory |
| 3 | `validate_markdown_anchors.py` | `.repo_studios/scripts/producers/` | producer | markdown_anchor_validation |
| 4 | `verify_docs_integrity.py` | `.repo_studios/scripts/producers/` | producer | docs_integrity_validation |
| 5 | `validate_metrics_anchor_stubs.py` | `.repo_studios/scripts/producers/` | producer | metrics_anchor_stub_validation |
| 6 | `generate_code_doc_churn_report.py` | `.repo_studios/scripts/producers/` | producer | code_doc_churn |
| 7 | `generate_undocumented_logic_report.py` | `.repo_studios/scripts/producers/` | producer | undocumented_logic |
| 8 | `aggregate_docs_health_signals.py` | `.repo_studios/scripts/aggregators/` | aggregator | docs_health_signals |

## CLI Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--repo-root` | (inferred) | Repository root override |
| `--doc-index-output-dir` | `.repo_studios/reports/healthview/producer_reports/doc_index` | Doc index output |
| `--anchor-inventory-output-dir` | `.repo_studios/reports/healthview/producer_reports/anchor_inventory` | Anchor inventory output |
| `--anchor-validation-output-dir` | `.repo_studios/reports/healthview/producer_reports/markdown_anchor_validation` | Anchor validation output |
| `--docs-integrity-output-dir` | `.repo_studios/reports/healthview/producer_reports/docs_integrity_validation` | Docs integrity output |
| `--metrics-stub-output-dir` | `.repo_studios/reports/healthview/producer_reports/metrics_anchor_stub_validation` | Metrics stub output |
| `--churn-output-dir` | `.repo_studios/reports/healthview/producer_reports/code_doc_churn` | Churn output |
| `--undocumented-output-dir` | `.repo_studios/reports/healthview/producer_reports/undocumented_logic` | Undocumented logic output |
| `--placeholder-output-dir` | `.repo_studios/reports/healthview/producer_reports/code_placeholders` | Placeholder output |
| `--monkey-patch-output-dir` | `.repo_studios/reports/healthview/producer_reports/monkey_patches` | Monkey patch output |
| `--aggregator-output-dir` | `.repo_studios/reports/healthview/aggregator_reports/docs_health_signals` | Aggregator output |
| `--healthview-root` | `.repo_studios/reports/healthview` | Healthview root |
| `--artifacts-to-keep` | `5` | Orchestrator topic artifacts to retain |
| `--doc-index-artifacts-to-keep` | `1` | Doc index retention |
| `--anchor-inventory-artifacts-to-keep` | `5` | Anchor inventory retention |
| `--anchor-validation-artifacts-to-keep` | `5` | Anchor validation retention |
| `--docs-integrity-artifacts-to-keep` | `5` | Docs integrity retention |
| `--metrics-stub-artifacts-to-keep` | `5` | Metrics stub retention |
| `--churn-artifacts-to-keep` | `5` | Churn retention |
| `--undocumented-artifacts-to-keep` | `5` | Undocumented retention |
| `--aggregator-artifacts-to-keep` | `5` | Aggregator retention |
| `--skip-doc-index` | `false` | Skip doc index step |
| `--skip-anchor-inventory` | `false` | Skip anchor inventory step |
| `--skip-anchor-validation` | `false` | Skip anchor validation step |
| `--skip-docs-integrity` | `false` | Skip docs integrity step |
| `--skip-metrics-stub` | `false` | Skip metrics stub step |
| `--skip-churn` | `false` | Skip churn step |
| `--skip-undocumented` | `false` | Skip undocumented step |
| `--skip-aggregator` | `false` | Skip aggregator step |
| `--skip-hygiene-signals` | `false` | Skip hygiene signal blending in aggregator |
| `--timestamp` | (current UTC) | ISO-8601 timestamp for run slug |
| `--log-level` | `INFO` | Logging verbosity |

## Agent Instructions

<!-- agents:begin:db_integration_docs_health_overview -->
```yaml
orchestrator:
  viewer_slug: orchestrator_reports
  topic: docs_health
  topic_slug: docs-health
artifacts:
  - manifest.json
  - summary.md
  - telemetry.json
markers:
  - description: Persist orchestrator manifest (report_runs + report_artifacts + orchestration_catalog)
    method: storage.write_manifest
  - description: Persist human-readable summary (report_artifacts)
    method: storage.write_summary
  - description: Persist telemetry payload (report_artifacts + telemetry_metrics)
    method: storage.write_telemetry
catalog_entries:
  - script_path: .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py
    topic: docs-health
    role: orchestrator
  - script_path: .repo_studios/scripts/producers/generate_doc_index.py
    topic: docs-health
    role: producer
  - script_path: .repo_studios/scripts/producers/generate_anchor_inventory.py
    topic: docs-health
    role: producer
  - script_path: .repo_studios/scripts/producers/validate_markdown_anchors.py
    topic: docs-health
    role: producer
  - script_path: .repo_studios/scripts/producers/verify_docs_integrity.py
    topic: docs-health
    role: producer
  - script_path: .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py
    topic: docs-health
    role: producer
  - script_path: .repo_studios/scripts/producers/generate_code_doc_churn_report.py
    topic: docs-health
    role: producer
  - script_path: .repo_studios/scripts/producers/generate_undocumented_logic_report.py
    topic: docs-health
    role: producer
  - script_path: .repo_studios/scripts/aggregators/aggregate_docs_health_signals.py
    topic: docs-health
    role: aggregator
```
<!-- agents:end:db_integration_docs_health_overview -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `manifest.json`
  - Key fields: `viewer`, `topic`, `run_slug`, `generated_at`, `schema_version`

- `report_artifacts`
  - Source: `manifest.json`, `summary.md`, `telemetry.json`
  - Roles:
    - `manifest_json` (JSON — orchestrator manifest with artifact refs)
    - `summary_md` (Markdown — consolidated docs health summary)
    - `telemetry_json` (JSON — full pipeline telemetry payload)

- `orchestration_catalog`
  - Source: `manifest.json` → `catalog` array
  - Key fields: `script_path`, `topic`, `role`
  - Purpose: Track which scripts were registered for this orchestrator run

- `telemetry_metrics`
  - Source: `telemetry.json` → `metrics`
  - Suggested metrics:
    - `doc_index_documents`
    - `anchor_inventory_slugs`
    - `anchor_validation_issues`
    - `docs_integrity_mismatches`
    - `metrics_stub_missing`
    - `churn_modules`
    - `undocumented_modules`
    - `overall_health_score`

- `artifact_references`
  - Source: `manifest.json` → `artifacts`
  - Links to all upstream producer and aggregator bundles

## Human Notes

- This is the Stage 2.1 orchestrator that coordinates all docs health gathering, validation, and aggregation.
- The pipeline runs 8 scripts in sequence, each with optional skip flags for incremental runs.
- Script registration uses `CatalogRegistry` to record all 9 scripts (1 orchestrator + 8 invoked) in the manifest.
- Retention is controlled per-script via dedicated `--*-artifacts-to-keep` flags plus the orchestrator-level `--artifacts-to-keep`.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.
- Runtime is typically 6-8 minutes depending on anchor validation and churn aggregation time.

## Reference Prompts

- "Run marker audit and confirm run_docs_health_overview.py appears with 3 markers"
- "Execute the docs health overview orchestrator and show the summary"
- "List all catalog entries registered by the orchestrator"
- "Show docs health score trend over last 5 runs"

## Update Log

| Date | Author | Changes |
| --- | --- | --- |
| 2025-01-02 | repo_studios_ai | Initial creation from code inspection during Stage 2.1 Pass 3 |
