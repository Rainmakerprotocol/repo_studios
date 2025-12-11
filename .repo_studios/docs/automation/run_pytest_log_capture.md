# run_pytest_log_capture.py (Legacy Shim)

**Last updated:** 2025-12-10

## Overview

`run_pytest_log_capture.py` previously executed the repository's pytest suite and wrote structured bundles
under `.repo_studios/reports/orchestrator_runs/pytest_log_capture/`. The Phase 8 cleanup retired that legacy
directory; the shim now delegates entirely to
`command_center/scripts/orchestrators/run_test_execution_telemetry.py`, which emits Healthview-compliant
bundles under `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<timestamp>/` while
capturing raw logs in `.repo_studios/command_center/reports/rawview/test_execution_runs/`.

> **Note**
> Since 2025-12-01 this entry point is a thin shim that delegates to
> `command_center/scripts/orchestrators/run_test_execution_telemetry.py`. All defaults documented
> here forward directly to the Test Execution Telemetry topic orchestrator, including the new
> rawview location and retention knobs.
The orchestrator threads standard Command Center helpers for path resolution, logging configuration,
and retention so downstream producers (for example `collect_test_log_reports.py`) can rely on
consistent payload shapes without reparsing raw console logs.

## Invocation

Typical full-suite invocation (runs the targets defined in `pytest.ini::testpaths`):

```bash
python .repo_studios/scripts/orchestrators/run_pytest_log_capture.py \
  --repo-root . \
  --logs-dir .repo_studios/command_center/reports/rawview/test_execution_runs \
  --log-level INFO
```

Subset example (extra arguments after `--` filter pytest to the given selection):

```bash
python .repo_studios/scripts/orchestrators/run_pytest_log_capture.py \
  --repo-root . \
  --logs-dir .repo_studios/command_center/reports/rawview/test_execution_runs \
  --log-level INFO \
  -- --maxfail=1 .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py
```

Key flags:

- `--repo-root`: Overrides repository root discovery when running outside the tree.
- `--logs-dir`: Directory containing timestamped pytest logs, JUnit XML, and summary text files
  (defaults to `.repo_studios/command_center/reports/rawview/test_execution_runs`).
- `--artifacts-to-keep`: Retention window for the Healthview manifest/summary/telemetry bundles; forwarded
  to the Test Execution Telemetry orchestrator (minimum 1, default 3).
- `--log-level`: Logging verbosity shared across helper routines (`INFO` default).
- `--from-log` / `--from-junit`: Skip test execution and summarize an existing log/JUnit pair.
- Extra pytest arguments follow `--`; providing them restricts collection to the addressed files or node ids.

## Outputs

Each execution now writes `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<timestamp>/`
with:

- `manifest.json`: Canonical payload capturing orchestrator inputs, retention budgets, and artifact pointers.
- `summary.md` / `summary.json`: Human-readable and machine-ingestible telemetry summaries.
- `telemetry.json`: Step-level telemetry mirrored from the manifest.

Producer/consumer artifacts (collector reports, health report, churn/complexity heatmap, coverage inventory,
test hardening analysis) remain in their respective `producer_reports` or `aggregator_reports` directories with
`latest_*` pointers. Raw pytest transcripts, failure/skip summaries, and junit artifacts live under
`.repo_studios/command_center/reports/rawview/test_execution_runs/`; override `--logs-dir` when you need to populate
an alternate tree.

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

Unit coverage for the topic orchestrator lives in
`.repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`.
The suite verifies structured artifact emission, skip handling, retention pruning, and manifest telemetry. Run with:

```bash
.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py
```

## Operational Notes

- The orchestrator accepts existing logs via `--from-log/--from-junit`, enabling fast
  re-summarization of CI artifacts without re-running pytest. Structured bundles are still produced
  (including latest pointers).
- When xdist terminates unexpectedly the runner retries in serial mode (when permitted by environment
  flags) and appends the second run to the existing log for traceability.
- Downstream producers (`collect_test_log_reports.py`, `generate_test_log_health_report.py`) should read the
  orchestrator-driven bundles referenced from the Healthview manifest rather than the removed legacy reports tree.
- Adjust `--artifacts-to-keep` if disk quotas demand tighter retention; the Command Center defaults
  keep three orchestrator runs to balance auditability and storage cost.
