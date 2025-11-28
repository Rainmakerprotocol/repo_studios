# run_pytest_log_capture.py

**Last updated:** 2025-11-27

## Overview

`run_pytest_log_capture.py` executes the repository's pytest suite (or summarizes an existing run) and
emits a structured artifact bundle alongside timestamped raw outputs under
`.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs`.
The orchestrator threads standard Command Center helpers for path resolution, logging configuration,
and retention so downstream producers (for example `collect_test_log_reports.py`) can rely on
consistent payload shapes without reparsing raw console logs.

## Invocation

Typical full-suite invocation (runs the targets defined in `pytest.ini::testpaths`):

```bash
python .repo_studios/scripts/orchestrators/run_pytest_log_capture.py \
  --repo-root . \
  --logs-dir .repo_studios/reports/orchestrator_logs/pytest_log_capture_logs \
  --output-dir .repo_studios/reports/orchestrator_runs/pytest_log_capture \
  --artifacts-to-keep 5 \
  --log-level INFO
```

Subset example (extra arguments after `--` filter pytest to the given selection):

```bash
python .repo_studios/scripts/orchestrators/run_pytest_log_capture.py \
  --repo-root . \
  --logs-dir .repo_studios/reports/orchestrator_logs/pytest_log_capture_logs \
  --output-dir .repo_studios/reports/orchestrator_runs/pytest_log_capture \
  --log-level INFO \
  -- --maxfail=1 .repo_studios/tests/tests_orchestrators/test_run_pytest_log_capture.py
```

Key flags:

- `--repo-root`: Overrides repository root discovery when running outside the tree.
- `--logs-dir`: Directory containing timestamped pytest logs, JUnit XML, and summary text files
  (defaults to `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs`).
- `--output-dir`: Destination for structured bundles (default `.repo_studios/reports/orchestrator_runs/pytest_log_capture`).
- `--artifacts-to-keep`: Retention window for orchestrator bundles and pointer refresh (minimum 1,
  default 5).
- `--log-level`: Logging verbosity shared across helper routines (`INFO` default).
- `--from-log` / `--from-junit`: Skip test execution and summarize an existing log/JUnit pair.
- Extra pytest arguments follow `--`; providing them restricts collection to the addressed files or node ids.

## Outputs

Each execution writes `.repo_studios/reports/orchestrator_runs/pytest_log_capture/pytest_log_capture-<ts>/`
with:

- `report.json`: Canonical payload capturing summary counts, runtime metadata, environment details, and
  provenance pointers back to the legacy files.
- `report.md`: Markdown companion for quick human inspection.
- `bundle_summary.json`: Lightweight digest exported for dashboards and aggregators.
- `failures.tsv` / `failures.csv`: Failures grouped by node id with file context.
- `skips.tsv` / `skips.csv`: Skip entries with associated reasons when available.
- `failures.txt` / `skips.txt`: Grouped plain-text summaries mirroring the TSV content.
- `full_log.txt`: Complete console transcript from the run (or supplied log in summarize mode).
- `junit.xml`: Copy of the produced JUnit XML when available.

Pointer files such as `latest_report.json`, `latest_bundle_summary.json`, and `latest_full_log.txt` are
refreshed beside the bundle. Raw pytest transcripts, failure/skip summaries, and junit artifacts live
under `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs/` by default; override
`--logs-dir` when you need to populate an alternate tree (for example, the legacy
`.repo_studios/pytest_logs` layout during cutover).

Historical bundles beyond the configured retention threshold are pruned automatically.

## Diagnostics

Important fields in `report.json`:

- `summary.failures`, `summary.skips`, `summary.duration_seconds`, `summary.junit` — high-level suite
  metrics.
- `run.command`, `run.cwd`, `run.terminated`, `run.retried_serial`, `run.xdist_used` — execution
  context and fallback indicators (serial retry triggers when xdist hangs or terminates early).
- `environment` — Python version, platform, and discovered pytest plugin capabilities.
- `provenance.legacy` — absolute paths to the legacy log, summary text files, and optional coverage assets.

Markdown and TSV artifacts mirror the JSON content so dashboards or ad-hoc reviews can consume whichever
format is most convenient.

## Testing

Unit coverage lives in `.repo_studios/tests/tests_orchestrators/test_run_pytest_log_capture.py`.
The suite verifies structured artifact emission in summarize mode, end-to-end execution with a stubbed
pytest run, latest-pointer refresh, and caretaking of the legacy summaries. Run with:

```bash
.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_orchestrators/test_run_pytest_log_capture.py
```

## Operational Notes

- The orchestrator accepts existing logs via `--from-log/--from-junit`, enabling fast
  re-summarization of CI artifacts without re-running pytest. Structured bundles are still produced
  (including latest pointers).
- When xdist terminates unexpectedly the runner retries in serial mode (when permitted by environment
  flags) and appends the second run to the existing log for traceability.
- Downstream producers (`collect_test_log_reports.py`, `generate_test_log_health_report.py`) should prefer
  the structured bundle under `latest_report.json` while retaining fallbacks to the legacy summaries.
- Adjust `--artifacts-to-keep` if disk quotas demand tighter retention; the Command Center defaults
  keep five orchestrator runs to balance auditability and storage cost.
