# Topic Orchestrators

This directory contains the Healthview topic orchestrators that now replace the legacy CommandView
runners. Each entry coordinates the shared helper stack (`build_topic_pipeline`, catalog
registration, retention knobs) and mirrors artifacts into the slugged Healthview directories under
`.repo_studios/command_center/reports/healthview/`.

## Test Execution Telemetry (`run_test_execution_telemetry.py`)
- **Healthview bundle:** `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<timestamp>/`
- **Replaces:** `scripts/orchestrators/run_pytest_log_capture.py` plus the ad-hoc churn and hardening analyzers
- **Runtime:** roughly 5-6 minutes in CI depending on log volume; the churn heatmap step dominates the budget
- **Highlights:** Chains coverage inventory, log collector, health report consumer, churn heatmap, and hardening trend analysis before emitting manifest/summary/telemetry bundles

## Fault Diagnostics (`run_fault_diagnostics_overview.py`)
- **Healthview bundle:** `.repo_studios/command_center/reports/healthview/fault_diagnostics/<timestamp>/`
- **Replaces:** `scripts/orchestrators/run_fault_pipeline.py`
- **Runtime:** roughly 3-5 minutes driven by producer replay of faulthandler archives; summarizer step continues on warning
- **Highlights:** Preserves reuse flags (`--skip-producer`, `--skip-consumer`) while mirroring crash triage artifacts and catalog telemetry for Healthview dashboards

## Docs Health (`run_docs_health_overview.py`)
- **Healthview bundle:** `.repo_studios/command_center/reports/healthview/docs_health/<timestamp>/`
- **Replaces:** legacy docs inventory/anchor/analysis script chain documented in the automation guides
- **Runtime:** roughly 6-8 minutes depending on anchor validation and churn aggregation
- **Highlights:** Executes doc index regeneration, anchor validation, analysis aggregation, and summary publication with per-step retention knobs

## Dependency & Import Hygiene (`run_dependency_import_hygiene.py`)
- **Healthview bundle:** `.repo_studios/command_center/reports/healthview/dependency_import_hygiene/<timestamp>/`
- **Replaces:** `scripts/orchestrators/run_batch_cleanup.py` and its chained hygienic producers
- **Runtime:** roughly 7-11 minutes (lint plus mypy plus placeholder scan dominate); baseline refresh runs only when requested
- **Highlights:** Threads dependency hygiene, import graph, placeholder scan, batch cleanup dry run, typecheck, and optional baseline refresh while mirroring structured producer archives

## Monkey Patch Oversight (`run_monkey_patch_oversight.py`)
- **Healthview bundle:** `.repo_studios/command_center/reports/healthview/monkey_patch_oversight/<timestamp>/`
- **Replaces:** `orchestrate_health_suite.py` monkey patch stages (scan/classify/trend) plus standalone summarizer calls
- **Runtime:** roughly 4-7 minutes with Git history enabled; risk trend aggregation scales with the historical window
- **Highlights:** Captures scan, classification, aggregator, and summarizer outputs with duplicate matrix cross-references for CommandView and Healthview consumers

## Standards Integrity (`run_standards_integrity.py`)
- **Healthview bundle:** `.repo_studios/command_center/reports/healthview/standards_integrity/<timestamp>/`
- **Replaces:** `scripts/orchestrators/run_standards_gap_suite.py` and `scripts/orchestrators/run_standards_index_cli.py`
- **Runtime:** roughly 5-8 minutes depending on index diff scope; prompt generation adds a small fixed overhead
- **Highlights:** Regenerates standards index, gap analysis, prompt packs, and diff reports before emitting consolidated manifest/summary/telemetry payloads
