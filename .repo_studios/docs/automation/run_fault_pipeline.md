# Fault Pipeline Orchestrator

## Overview

`run_fault_pipeline.py` coordinates the faulthandler producer (`collect_faulthandler_reports.py`) and
consumer (`generate_fault_artifacts.py`) so the stack capture flow can be refreshed through a single
command. The orchestrator writes timestamped run bundles, mirrors summaries into the Command Center tree,
and enforces retention across producer, consumer, and orchestrator tiers. Use this entry point when new
stack captures land under `.repo_studios/faulthandler/<ts>/` or when you need to rebuild consumer bundles
from an existing producer report.

## Invocation

```bash
python .repo_studios/scripts/orchestrators/run_fault_pipeline.py \
  --repo-root <path> \
  [--run-dir <path>] \
  [--skip-producer] \
  [--skip-consumer] \
  [--reuse-report <report.json>] \
  [--artifacts-to-keep <int>] \
  [--producer-artifacts-to-keep <int>] \
  [--consumer-artifacts-to-keep <int>] \
  [--log-level INFO|DEBUG|WARNING]
```

- `--repo-root`: Required outside the repo; defaults via library heuristics when omitted.
- `--run-dir`: Targets a specific faulthandler run. Without it, the producer selects the newest capture.
- `--skip-producer`: Reuses existing producer artifacts. Combine with `--reuse-report` to pin a report.
- `--skip-consumer`: Stops after the producer step, preserving the latest report pointers.
- `--reuse-report`: Path to a producer `report.json` when skipping the producer. The orchestrator
  derives the matching run directory when possible.
- `--artifacts-to-keep`: Retention for orchestrator bundles (defaults to five). Producer and consumer
  retention can be overridden independently.
- `--log-level`: Shared logging level passed to producer and consumer helpers (`INFO` by default).

## Outputs

Each run creates `.repo_studios/reports/orchestrator_runs/fault_pipeline/fault_pipeline-<ts>/` containing:

- `summary.json`: Structured payload summarising step outcomes, durations, and severity buckets.
- `SUMMARY.md`: Markdown brief with run context, producer/consumer notes, and per-step status.
- `bundle_summary.json`: Consumer-facing snapshot exported for quick inspection and downstream blends.
- `pipeline.log`: Aggregated log stream from both steps.

The orchestrator also maintains `latest_*` pointers beside the run bundles and mirrors the same files into
`.repo_studios/command_center/reports/fault_pipeline_orchestrator/`, pruning historical directories per the
configured retention window.

## Testing

Unit coverage lives in `tests/tests_orchestrators/test_run_fault_pipeline.py`. The suite exercises the
full flow, producer reuse with skip flags, and bundle pruning behaviour. Run the tests with:

```bash
.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_orchestrators/test_run_fault_pipeline.py
```

## Follow-Ups

- Wire a dedicated Make target (placeholder: `studio-run-fault-pipeline`) so health suites can refresh
  the stack artefacts without manual CLI invocation.
- Draft an aggregator blueprint for cross-run faulthandler trending once the orchestrator stabilises.
