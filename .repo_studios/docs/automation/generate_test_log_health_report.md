# Generate Test Log Health Report

## Purpose

`generate_test_log_health_report.py` turns raw pytest output into a structured health bundle so
operators can track warning spikes, failure patterns, and slow tests without rereading entire logs.
The script prefers the curated JSON emitted by `collect_test_log_reports.py` and gracefully falls
back to scanning `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs/` (or the legacy
`.repo_studios/pytest_logs/` tree when allowed) when the producer bundle is missing.

## Inputs

- **Structured producer bundle (preferred):** `.repo_studios/reports/producer_reports/test_log_reports/latest_report.json`.
- **Fallback logs directory:** `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs/`
  by default; legacy `.repo_studios/pytest_logs/` runs are discovered when
  `TEST_LOG_HEALTH_ALLOW_LEGACY` is not set to `0`.
- **CLI flags:**
  - `--logs-dir`: Root directory containing pytest log runs (default
    `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs`; falls back to
    `.repo_studios/pytest_logs` when the new tree is missing and `TEST_LOG_HEALTH_ALLOW_LEGACY`
    remains enabled).
  - `--producer-report`: Path to the producer JSON bundle (default `.repo_studios/reports/producer_reports/test_log_reports/latest_report.json`).
  - `--output-base`: Target directory for timestamped consumer bundles (default `.repo_studios/reports/consumer_reports/test_log_health_reports`).
  - `--artifacts-to-keep`: Number of run directories to retain (default `5`).
  - `--log-level`: Standard logging verbosity control.

## Outputs

Each execution writes a timestamped folder under
`.repo_studios/reports/consumer_reports/test_log_health_reports/<ts>/` containing:

- `report.json` – summary metrics, warning breakdowns, slow-test listings, and
  `comparisons.previous_run.pass_rate` metadata.
- `report.md` – human-readable narrative with a "Pass Rate Delta" section and appended source
  references.
- `report.csv` – lightweight metrics table (totals, pass-rate signals, slow test rankings) for
  spreadsheet workflows.
- `bundle_summary.json` – provenance manifest with artifact paths, source type (`producer` or
  `logs`), retention details, and pass-rate comparison data.

Latest symlinks or mirrors are not used; downstream consumers should read `bundle_summary.json`
to locate the freshest bundle.

## Retention & Pruning

The consumer keeps the newest five runs by default. Adjust `--artifacts-to-keep` if you need
deeper history; `0` disables pruning.

## Typical Workflow

1. Capture logs with `run_pytest_log_capture.py` or existing CI suites (the orchestrator now
  defaults to `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs/`).
1. Run `collect_test_log_reports.py` to build the structured producer bundle.
1. Execute `generate_test_log_health_report.py` (or the Make target below) to emit consumer
  artifacts.
1. Inspect the markdown or CSV, then feed `bundle_summary.json` into downstream aggregators such as
  `generate_churn_complexity_heatmap.py`.

## Make Target

Invoke the consumer via Make to align with other automation:

```bash
make -C .repo_studios studio-generate-test-log-health-report PYTHON=.venv/Scripts/python.exe
```

The target uses the defaults noted above, including `--artifacts-to-keep 5`.

## Testing

Pytest coverage lives in `tests/tests_consumers/test_generate_test_log_health_report.py` and
exercises producer-first runs, fallback parsing, CSV exports, delta computations, and pruning
logic. Run the focused suite with:

```bash
pytest .repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py
```

## Notes

- When a previous run is available, `comparisons.previous_run.pass_rate.delta` reports the
  percentage-point change in pass rate relative to the latest retained bundle.
- CSV exports format numeric pass-rate fields to two decimals and include slow-test rows
  (`slow_test_<n>`) for quick triage.
- Markdown outputs append a "Source References" section pointing to the producer bundle, raw logs,
  and CSV export for easy drill-down as part of human reviews.
- Disable legacy log discovery by exporting `TEST_LOG_HEALTH_ALLOW_LEGACY=0` once CI callers fully
  migrate to the structured reports hierarchy.
