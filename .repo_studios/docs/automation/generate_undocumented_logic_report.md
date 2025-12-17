---
title: Undocumented Logic Producer
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: active
version: 1.0.0
updated: 2025-12-17
tags:
  - producers
  - docs-health
  - healthview
related_files:
  - ../../scripts/producers/generate_undocumented_logic_report.py
  - ../../scripts/aggregators/aggregate_docs_health_signals.py
  - ../../command_center/scripts/orchestrators/run_docs_health_overview.py
  - ../../tests/tests_producers/test_generate_undocumented_logic_report.py
---

# generate_undocumented_logic_report

## Goals

`generate_undocumented_logic_report.py` scans automation scripts for public
functions, classes, and methods that lack docstrings. The output feeds the Docs
Health workflow by highlighting missing documentation coverage in code.

## System Context

This producer writes canonical Healthview bundles under the Repo Studios
producer report root.

## Agent Instructions

* Preserve the canonical bundle contract: `manifest.json`, `summary.md`,
  `telemetry.json` only.
* Do not add `latest_*` pointer files.
* Use the shared storage factory + pruning helpers.

## Human Notes

### Inputs

* Repository root (`--repo-root`, defaults to auto-detected root)
* Output directory (`--output-dir`, defaults to `.repo_studios/reports/producer_reports`)
* Documentation index (`--doc-index`, defaults to `.repo_studios/reports/producer_reports/healthview/doc_index/`)
* Anchor inventory (`--anchor-inventory`, defaults to `.repo_studios/reports/producer_reports/healthview/anchor_inventory/`)
* Optional allowlist file (`--allowlist`) with `module` or `module::qualified-name` entries to skip
* Optional additional code roots (`--code-root` can be provided multiple times)
* Optional flag to include `.repo_studios/command_center/scripts` (`--include-command-center`)
* Retention cap (`--artifacts-to-keep`, default 5)
* Standard logging flag (`--log-level`)

### Outputs

Each run emits a canonical bundle directory:

* `.repo_studios/reports/producer_reports/healthview/undocumented_logic/YYYYMMDD-HHMM/`
  * `manifest.json` — inputs + summary metrics
  * `summary.md` — human-readable summary
  * `telemetry.json` — metrics + full payload in `payload`

The producer prunes old run directories according to `--artifacts-to-keep`.

## Reference Prompts

Run the producer directly:

```pwsh
$env:PYTHONPATH = ".repo_studios"
\.\.venv\Scripts\python.exe -u \
  .repo_studios\scripts\producers\generate_undocumented_logic_report.py \
  --repo-root . \
  --include-command-center \
  --output-dir .repo_studios/reports/producer_reports
```

Focused test run:

```pwsh
$env:PYTHONPATH = ".repo_studios"
\.\.venv\Scripts\python.exe -m pytest \
  .repo_studios/tests/tests_producers/test_generate_undocumented_logic_report.py
```

## Update Log

* 2025-12-17 — Migrated to canonical Healthview bundle layout (manifest/summary/telemetry) and removed legacy `latest_*` pointers.
