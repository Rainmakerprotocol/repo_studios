# Fault Diagnostics Overview Orchestrator

## Overview

`command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` coordinates the faulthandler
producer (`collect_faulthandler_reports.py`), consumer (`generate_fault_artifacts.py`), and the overview
summarizer (`summarize_fault_diagnostics_overview.py`). The topic orchestrator standardises repo-root
resolution through the shared Command Center path/option builders, threads skip/retention flags across each
step, registers catalog metadata, and emits viewer/topic compliant bundles under
`.repo_studios/command_center/reports/commandview/fault_diagnostics/<slug>/`. Use this entry point whenever
new stack captures land under `.repo_studios/reports/orchestrator_logs/faulthandler_logs/<ts>/` (the default
output from `configure_faulthandler_runtime.py`) or when you need to rebuild consumer and summarizer assets
from an existing producer report.

## Invocation

```bash
python .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py \
  --repo-root <path> \
  [--runs-dir <path>] \
  [--run-dir <path>] \
  [--reuse-report <report.json>] \
  [--producer-top-frames <int>] \
  [--skip-producer] \
  [--skip-consumer] \
  [--skip-summarizer] \
  [--producer-artifacts-to-keep <int>] \
  [--consumer-artifacts-to-keep <int>] \
  [--summarizer-artifacts-to-keep <int>] \
  [--artifacts-to-keep <int>] \
  [--timestamp <iso8601>] \
  [--log-level INFO|DEBUG|WARNING]
```

From the repository root, run the Make target for the opinionated defaults (the legacy
`studio-run-fault-pipeline` alias still works):

```bash
make -C .repo_studios studio-orchestrate-fault-diagnostics
```

- `--repo-root`: Required outside the repo; defaults via helper heuristics when omitted.
- `--runs-dir`: Source directory for faulthandler runs; defaults to the orchestrator logs tree.
- `--run-dir`: Processes a specific run folder. Without it, the producer selects the newest capture.
- `--reuse-report`: Points the consumer at an existing `report.json`, enabling producer skips.
- `--producer-top-frames`: Overrides the producer’s captured frame count when deeper stacks are required.
- `--skip-producer` / `--skip-consumer` / `--skip-summarizer`: Reuses previous artifacts while leaving
  downstream steps intact.
- `--producer-artifacts-to-keep` / `--consumer-artifacts-to-keep` / `--summarizer-artifacts-to-keep`:
  Independent retention budgets for each tier (default five).
- `--artifacts-to-keep`: Retention budget for the Command Center manifest/summary/telemetry bundles.
- `--timestamp`: Locks the orchestrator slug to a specific ISO-8601 instant (UTC assumed when tzinfo is
  absent).
- `--log-level`: Shared logging level passed to every delegated script (`INFO` by default).

## Outputs

Each successful run writes `.repo_studios/command_center/reports/commandview/fault_diagnostics/<slug>/`
containing:

- `manifest.json`: Structured pipeline manifest listing step telemetry, inputs, and artifact pointers.
- `summary.md`: Markdown digest summarising per-step status and high-level metrics.
- `telemetry.json`: Machine-readable telemetry mirroring the manifest’s step status block.

The orchestrator also updates Command Center mirrors for the producer and consumer reports while preserving
their `--keep` budgets. When the summarizer succeeds, the overview JSON/Markdown bundle remains in
`.repo_studios/reports/summarizer_reports/fault_diagnostics_overview/<slug>/` and is referenced from the
manifest.

## Testing

Topic-level coverage lives in
`.repo_studios/tests/tests_command_center/fault_diagnostics/test_run_fault_diagnostics_overview.py`, which
exercises skip/reuse combinations, catalog registration, retention enforcement, and manifest emission. Run
the tests with:

```bash
.venv/Scripts/python.exe -m pytest \
  .repo_studios/tests/tests_command_center/fault_diagnostics/test_run_fault_diagnostics_overview.py
```

## Follow-Ups

- Monitor adoption of `make -C .repo_studios studio-orchestrate-fault-diagnostics` and capture feedback on
  default retention knobs or additional skip presets.
- Track the planned migration work to retire the legacy `run_fault_pipeline.py` smoke tests once the new
  orchestrator is fully adopted across automation.
