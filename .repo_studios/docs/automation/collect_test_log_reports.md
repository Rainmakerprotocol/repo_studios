---
title: collect_test_log_reports.py
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: active
version: 2.0.0
updated: 2025-12-15
tags:
  - producers
  - rawview
  - pytest
  - reports
related_files:
  - ../../scripts/producers/collect_test_log_reports.py
  - ../../tests/tests_producers/test_collect_test_log_reports.py
  - ../../command_center/docs/db_integrations/db_integration_test_log_reports.md
---

# collect_test_log_reports.py

## Purpose

`collect_test_log_reports.py` converts raw pytest log runs into a canonical report bundle so downstream consumers and dashboards can reuse summary metrics without reparsing warning blocks or slow-test sections. The producer leverages `libraries.test_log_analysis` to normalize outputs and writes the standard three artifacts via the shared artifact writer (`write_report_artifacts()`), with pruning handled by `prune_run_directories()`.

## Invocation

```bash
python .repo_studios/scripts/producers/collect_test_log_reports.py \
  --logs-dir .repo_studios/reports/healthview/rawview/test_execution_runs \
  --output-dir .repo_studios/reports/healthview/rawview/test_log_reports \
  --artifacts-to-keep 10 \
  --log-level INFO
```

From `.repo_studios/`, run `make studio-collect-test-log-reports` to execute the producer with repository defaults.

### Key arguments

- `--logs-dir`: Base directory containing pytest log runs (default `.repo_studios/reports/healthview/rawview/test_execution_runs`).
- `--logs-run`: Explicit run directory; when omitted the newest candidate under `--logs-dir` is selected automatically.
- `--output-dir`: Output directory containing timestamped bundles (default `.repo_studios/reports/healthview/rawview/test_log_reports`).
- `--summarize-existing`: Do not run pytest; summarize existing logs (newest under `--logs-dir`, or the explicit `--logs-run`).
- `--run-pytest` / `--no-run-pytest`: Explicitly control whether the producer runs pytest first. When omitted, the default is:
  - reuse newest existing run if available
  - otherwise run pytest to capture a new run
- `--run-timestamp`: Optional override for the run slug in UTC (`YYYYMMDD-HHMM`). Useful for deterministic CI/test runs.
- `--artifacts-to-keep`: Number of historical run directories retained after pruning (minimum 1, default 10, enforced by the shared helper).
- `--log-level`: Logging verbosity (`INFO` default).

## Outputs

Each run produces a bundle under positional encoding:

`<output_dir>/<YYYYMMDD-HHMM>/`

The bundle contains exactly:

- `manifest.json`
- `summary.md`
- `telemetry.json`

Historical run directories are pruned to the configured retention threshold after each execution, and `.keep` sentinels are respected when present.

## Diagnostics

Key fields:

- `manifest.json` records the run identity (`viewer_slug`, `topic`, `run_timestamp`), inputs, and artifact catalog.
- `telemetry.json` contains extracted metrics (`warnings_total`, `slow_tests_count`, `tracebacks`, test totals) plus a compact payload snapshot.
- `summary.md` is the human-readable digest for quick review.

When the producer runs pytest, both `manifest.json` and `telemetry.json` record `pytest_ran`, `pytest_exit_code`, and `pytest_command` under `inputs` so callers can confirm that the bundle reflects a fresh capture.

`log` output enumerates the run directory, warning count, slow-test count, and artifact destination so CI callers can assert conditions without parsing JSON.

## Testing

`pytest .repo_studios/tests/tests_producers/test_collect_test_log_reports.py`

The suite verifies canonical artifact emission, telemetry metric extraction, pruning behaviour, and graceful handling when no runs are available.

## Operational notes

- The default invocation (no `--logs-run`, no `--summarize-existing`) reuses the newest existing run under `--logs-dir` when present; otherwise it runs pytest to stage a new run directory under `--logs-dir`, then emits the canonical report bundle.
- Use `--summarize-existing` when you want to reuse existing logs (for example when another job already captured raw pytest output).
- Downstream consumer `generate_test_log_health_report.py` is expected to migrate to the canonical bundle (manifest/summary/telemetry). Do not rely on `latest_*` pointers.
- Adjust `--artifacts-to-keep` based on storage budgets; CI jobs typically run with smaller retention windows (5–10 runs) to preserve auditability while limiting disk usage. The shared pruning helper keeps the current run plus any `.keep`-marked directories regardless of the configured limit to avoid accidental data loss.
- The producer tolerates absent JUnit or pytest log files by emitting empty tables with zeroed metrics so dashboards can differentiate between “no findings” and “no data.”
