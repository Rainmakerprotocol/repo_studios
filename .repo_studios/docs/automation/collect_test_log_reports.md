# collect_test_log_reports.py

**Last updated:** 2025-11-28

## Purpose

`collect_test_log_reports.py` converts raw pytest log runs into structured artifacts that downstream consumers and dashboards can reuse without reparsing warning blocks or slow-test sections. The producer leverages `utilities.test_log_analysis` to normalize outputs, writes JSON/Markdown/CSV bundles, maintains `latest_*` pointers, and prunes historical runs via the shared `command_center` helper (`prune_run_directories`) so `.keep` sentinels stay honoured while retention remains configurable.

## Invocation

```bash
python .repo_studios/scripts/producers/collect_test_log_reports.py \
  --logs-dir .repo_studios/command_center/reports/rawview/test_execution_runs \
  --output-dir .repo_studios/reports/producer_reports/test_log_reports \
  --artifacts-to-keep 10 \
  --log-level INFO
```

From `.repo_studios/`, run `make studio-collect-test-log-reports` to execute the producer with repository defaults.

### Key arguments

- `--logs-dir`: Base directory containing pytest log runs (default `.repo_studios/command_center/reports/rawview/test_execution_runs`; falls back to `.repo_studios/pytest_logs` when the new tree is missing and `PYTEST_LOG_REPORTS_ALLOW_LEGACY` is not set to `0`).
- `--logs-run`: Explicit run directory; when omitted the newest candidate under `--logs-dir` is selected automatically.
- `--output-dir`: Destination for structured artifacts (default `.repo_studios/reports/producer_reports/test_log_reports`).
- `--artifacts-to-keep`: Number of historical run directories retained after pruning (minimum 1, default 10, enforced by the shared helper).
- `--log-level`: Logging verbosity (`INFO` default).

## Outputs

Each run produces `.repo_studios/reports/producer_reports/test_log_reports/test_log_report-<timestamp>/` containing:

- `report.json`: Canonical payload with summary metrics (totals, warnings, tracebacks) plus warning/file breakdowns and slow-test metadata.
- `report.md`: Human-readable summary mirroring the JSON report.
- `warnings_by_type.csv`: Table of warning classes and counts.
- `warnings_by_file.csv`: Table of files emitting warnings and their frequencies.
- `slow_tests.csv`: List of slowest pytest nodes with durations.
- `combined.log`: Copy of the selected pytest log file for direct inspection.

The producer also refreshes `latest_*` pointers (e.g., `latest_report.json`, `latest_warnings_by_type.csv`, `latest_slow_tests.csv`, `latest_combined.log`). Historical run directories are pruned to the configured retention threshold after each execution, and `.keep` sentinels are respected when present.

## Diagnostics

Key fields in `report.json`:

- `summary.total`, `summary.passed`, `summary.skipped`, `summary.xfailed`, `summary.failed`, `summary.errors` — direct totals from JUnit metadata.
- `summary.warnings_total` — total warnings counted across the run.
- `summary.tracebacks` — number of `Traceback (most recent call last)` occurrences in the log file.
- `warnings.by_type` — mapping of warning class → count.
- `warnings.by_file` — mapping of file path → warning count.
- `slow_tests` — list of `{seconds, nodeid}` entries derived from the pytest slowest durations block.
- `meta` — includes `generated_at`, selected log path (`full_log`), and the underlying logs directory examined.

`log` output enumerates the run directory, warning count, slow-test count, and artifact destination so CI callers can assert conditions without parsing JSON.

## Testing

`pytest .repo_studios/tests/tests_producers/test_collect_test_log_reports.py`

The suite verifies artifact emission, CSV contents, latest-pointer refresh, pruning behaviour, and graceful handling when no runs are available.

## Operational notes

- Ensure `orchestrators/run_pytest_log_capture.py` (or equivalent) populates `.repo_studios/command_center/reports/rawview/test_execution_runs/<slug>/<timestamp>/` prior to running the producer. Missing runs result in a no-op with an informational log entry. Legacy runs under `.repo_studios/pytest_logs` are still discovered when the environment variable `PYTEST_LOG_REPORTS_ALLOW_LEGACY` is not disabled.
- Downstream consumer `generate_test_log_health_report.py` will be updated to prefer these structured artifacts, keeping its on-demand parsing as fallback.
- Adjust `--artifacts-to-keep` based on storage budgets; CI jobs typically run with smaller retention windows (5–10 runs) to preserve auditability while limiting disk usage. The shared pruning helper keeps the current run plus any `.keep`-marked directories regardless of the configured limit to avoid accidental data loss.
- The producer tolerates absent JUnit or pytest log files by emitting empty tables with zeroed metrics so dashboards can differentiate between “no findings” and “no data.”
