---
title: Automation — collect_faulthandler_reports
audience: [Copilot, Agents, Developers]
role: [Documentation, Automation]
owners: [repo_studios]
status: active
version: 2
updated_at: 2025-12-15
tags: [automation, rawview, faulthandler, fault-diagnostics, positional-encoding, canonical-artifacts, db-integration]
related_files:
  - .repo_studios/scripts/producers/collect_faulthandler_reports.py
  - .repo_studios/scripts/consumers/generate_fault_artifacts.py
  - .repo_studios/tests/tests_producers/test_collect_faulthandler_reports.py
  - .repo_studios/tests/tests_consumers/test_generate_fault_artifacts.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/libraries/prune_logs.py
---

# Automation — collect_faulthandler_reports

See `.github/instructions/markdown.instructions.md` for repo-wide Markdown rules (last reviewed 2025-12-15).

## Goals

- Convert raw faulthandler run directories into positional-encoded, canonical artifacts.
- Produce stable inputs for fault triage consumers without relying on mutable `latest_*` pointers.
- Keep historical runs pruned while protecting the current run and `.keep` sentinels.

## System Context

- Script: `.repo_studios/scripts/producers/collect_faulthandler_reports.py`
- Viewer/topic: `rawview / fault_artifacts_producer`
- Default runs root: `.repo_studios/command_center/reports/rawview/fault_diagnostics_runs`
- Default reports root: `.repo_studios/command_center/reports`

Output layout (positional encoding):

```text
<reports_root>/rawview/fault_artifacts_producer/<YYYYMMDD-HHMM>/
  manifest.json
  summary.md
  telemetry.json
```

Legacy fallback (optional): when `FAULT_LOGS_ALLOW_LEGACY` is enabled, the producer may fall back to
`.repo_studios/faulthandler/` if the default runs root is missing.

## Agent Instructions

<!-- agents:begin:automation_collect_faulthandler_reports -->
```yaml
viewer_slug: rawview
topic: fault_artifacts_producer
inputs:
  runs_dir_default: .repo_studios/command_center/reports/rawview/fault_diagnostics_runs
outputs:
  layout: positional
  artifacts:
    - role: manifest
      path: rawview/fault_artifacts_producer/<YYYYMMDD-HHMM>/manifest.json
    - role: summary
      path: rawview/fault_artifacts_producer/<YYYYMMDD-HHMM>/summary.md
    - role: telemetry
      path: rawview/fault_artifacts_producer/<YYYYMMDD-HHMM>/telemetry.json
notes:
  - No producer `latest_*` pointers are written.
  - Pruning uses the shared helper and respects `.keep` sentinels.
  - DB dual-write is routed through `create_storage` and marked with DB_INTEGRATION_MARKER comments.
```
<!-- agents:end:automation_collect_faulthandler_reports -->

## Human Notes

### Invocation

```bash
python .repo_studios/scripts/producers/collect_faulthandler_reports.py \
  --runs-dir .repo_studios/command_center/reports/rawview/fault_diagnostics_runs \
  --output-dir .repo_studios/command_center/reports \
  --artifacts-to-keep 10 \
  --log-level INFO
```

From `.repo_studios/`, run `make studio-collect-faulthandler-reports` to execute the producer with repository defaults.

### Key arguments

* `--runs-dir`: Directory containing timestamped faulthandler capture folders.
* `--run-dir`: Explicit run directory to process; when omitted the producer selects the newest run under `--runs-dir`.
* `--output-dir`: Reports root for positional bundles (defaults to `.repo_studios/command_center/reports`).
* `--artifacts-to-keep`: Number of historical run directories retained after pruning (minimum 1).
* `--timestamp`: Override run timestamp (ISO-8601 or `YYYYMMDD-HHMM`).
* `--top-frames`: Override frames captured per signature.
* `--validate-only`: Validate the latest positional bundle exists and contains the canonical trio.

### Outputs

Each execution writes the canonical trio only:

* `manifest.json`: Run metadata, paths, inputs, and catalog entries.
* `summary.md`: Human-readable markdown summary.
* `telemetry.json`: Metrics and structured components for downstream automation.

### Testing

`pytest .repo_studios/tests/tests_producers/test_collect_faulthandler_reports.py`

The suite validates canonical artifact emission, no-run behavior, validate-only behavior, and confirms no producer `latest_*` pointers exist.

## Reference Prompts

- "Load the latest rawview/fault_artifacts_producer telemetry and summarize signature_count and repeat_offender_signatures."
- "Show the most recent faulthandler producer run directory and the artifact paths."

## Update Log

- 2025-12-15 — Updated to canonical positional artifacts (`manifest.json`, `summary.md`, `telemetry.json`), removed `latest_*` references, and aligned Make invocation with `.repo_studios/command_center/reports`.
