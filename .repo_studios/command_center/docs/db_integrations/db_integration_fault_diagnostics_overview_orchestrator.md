---
title: DB Integration — run_fault_diagnostics_overview.py
audience: [Copilot, Agents, Developer]
role: [DBIntegrationDoc]
owners: [repo_studios_ai]
status: draft
version: 1
updated_at: 2025-01-02
tags: [db-integration, orchestrator, healthview, fault-diagnostics]
related_files:
  - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/utilities/list_db_markers.py
---

# DB Integration — run_fault_diagnostics_overview.py

<!-- markdownlint-disable MD013 -->
<!-- Technical doc; line length exempt -->

## Goals

- Document the database integration markers and intended table mappings for the Fault Diagnostics Overview orchestrator.
- Provide a consistent reference for marker audits (`list_db_markers.py`) during the dual-write migration.

## System Context

- Orchestrator script: `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py`
- Topic slug: `fault_diagnostics_overview`
- Output contract (file system): `.repo_studios/reports/healthview/orchestrator_reports/fault_diagnostics_overview/<YYYYMMDD-HHMM>/`
- Artifacts: `manifest.json`, `summary.md`, `telemetry.json`
- Storage layer: `.repo_studios/command_center/scripts/libraries/database_integration.py` (`create_storage` → `DualWriteStorage`)
- Runtime: ~3-5 minutes (producer log replay is the majority of execution time)

## Invoked Scripts

The orchestrator coordinates execution of the following upstream scripts:

| Order | Script | Path | Role | Topic |
| --- | --- | --- | --- | --- |
| 1 | `collect_faulthandler_reports.py` | `.repo_studios/scripts/producers/` | producer | faulthandler_reports |
| 2 | `generate_fault_artifacts.py` | `.repo_studios/scripts/consumers/` | consumer | fault_artifacts |
| 3 | `summarize_fault_diagnostics_overview.py` | `.repo_studios/command_center/scripts/summarizers/` | summarizer | fault_diagnostics_overview |

## CLI Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--repo-root` | (inferred) | Repository root override |
| `--runs-dir` | `.repo_studios/command_center/reports/rawview/fault_diagnostics_runs` | Faulthandler runs base |
| `--run-dir` | (none) | Explicit faulthandler run directory to process |
| `--producer-output-dir` | `.repo_studios/reports/healthview/producer_reports/faulthandler_reports` | Producer output |
| `--consumer-output-dir` | `.repo_studios/reports/healthview/consumer_reports/fault_artifacts` | Consumer output |
| `--summarizer-output-dir` | `.repo_studios/reports/healthview/summarizer_reports/fault_diagnostics_overview` | Summarizer output |
| `--orchestrator-output-dir` | `.repo_studios/reports/healthview/orchestrator_reports/fault_diagnostics_overview` | Orchestrator output |
| `--artifacts-to-keep` | `3` | Orchestrator retention budget |
| `--producer-artifacts-to-keep` | `5` | Producer retention |
| `--consumer-artifacts-to-keep` | `5` | Consumer retention |
| `--summarizer-artifacts-to-keep` | `5` | Summarizer retention |
| `--reuse-report` | (none) | Reuse an existing producer report JSON |
| `--producer-top-frames` | (none) | Override the producer top frame depth |
| `--skip-producer` | `false` | Skip producer step |
| `--skip-consumer` | `false` | Skip consumer step |
| `--skip-summarizer` | `false` | Skip summarizer step |
| `--timestamp` | (current UTC) | ISO-8601 timestamp for run slug |
| `--log-level` | `INFO` | Logging verbosity |

## Agent Instructions

<!-- agents:begin:db_integration_fault_diagnostics_overview_orchestrator -->
```yaml
orchestrator:
  viewer_slug: orchestrator_reports
  topic: fault_diagnostics_overview
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
  - script_path: .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py
    topic: fault_diagnostics_overview
    role: orchestrator
  - script_path: .repo_studios/scripts/producers/collect_faulthandler_reports.py
    topic: faulthandler_reports
    role: producer
  - script_path: .repo_studios/scripts/consumers/generate_fault_artifacts.py
    topic: fault_artifacts
    role: consumer
  - script_path: .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py
    topic: fault_diagnostics_overview
    role: summarizer
```
<!-- agents:end:db_integration_fault_diagnostics_overview_orchestrator -->

## Table Mapping (Intent)

- `report_runs`
  - Source: `manifest.json`
  - Key fields: `viewer`, `topic`, `run_slug`, `generated_at`, `schema_version`

- `report_artifacts`
  - Source: `manifest.json`, `summary.md`, `telemetry.json`
  - Roles:
    - `manifest_json` (JSON — orchestrator manifest with artifact refs)
    - `summary_md` (Markdown — consolidated fault diagnostics summary)
    - `telemetry_json` (JSON — full pipeline telemetry payload)

- `orchestration_catalog`
  - Source: `manifest.json` → `catalog` array
  - Key fields: `script_path`, `topic`, `role`
  - Purpose: Track which scripts were registered for this orchestrator run

- `telemetry_metrics`
  - Source: `telemetry.json` → `metrics`
  - Suggested metrics:
    - `signature_count`
    - `repeat_offender_count`
    - `new_signatures`
    - `resolved_signatures`
    - `artifact_count`
    - `total_bytes`

## Human Notes

- This is the Stage 3.1 orchestrator that coordinates faulthandler collection, artifact generation, and summary emission.
- The pipeline executes three steps: `produce` → `consume` → `summarize`.
- The summarizer step is tolerant so investigations continue even when only warnings are raised.
- Script registration uses `CatalogRegistry` to record all 4 scripts (1 orchestrator + 3 invoked) in the manifest.
- Retention is controlled per-script via dedicated `--*-artifacts-to-keep` flags.
- Database writes are dormant unless `REPO_STUDIOS_DB_URL` or `REPO_STUDIOS_DB_ENABLED=true` is configured.

## Reference Prompts

- "Run marker audit and confirm run_fault_diagnostics_overview.py appears with 3 markers"
- "Execute the fault diagnostics orchestrator and show the summary"
- "List all catalog entries registered by the orchestrator"

## Update Log

| Date | Author | Changes |
| --- | --- | --- |
| 2025-01-02 | repo_studios_ai | Initial creation from code inspection during Stage 3.1 Pass 3 |
