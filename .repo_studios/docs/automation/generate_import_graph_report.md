---
title: generate_import_graph_report.py
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: active
version: 2.0.0
updated: 2025-12-16
tags:
  - automation
  - healthview
  - import-graph
related_files:
  - ../../scripts/producers/generate_import_graph_report.py
  - ../../tests/tests_producers/test_generate_import_graph_report.py
  - ../../command_center/docs/db_integrations/db_integration_import_graph.md
  - ../../scripts/producers/validate_import_boundaries.py
---

# generate_import_graph_report.py

## Purpose

`generate_import_graph_report.py` scans owned Python packages inside the repository and emits an adjacency graph of
import relationships. The report highlights:

- Fan-in hotspots (modules depended on by many others)
- Fan-out hotspots (modules with many dependencies)
- Cycles (first 10)
- Isolated modules

The producer is aligned with the canonical positional bundle contract: each run writes a single
positional-encoded folder containing `manifest.json`, `summary.md`, and `telemetry.json`.

## Invocation

```bash
python .repo_studios/scripts/producers/generate_import_graph_report.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports \
  --owned agents api \
  --artifacts-to-keep 5 \
  --log-level INFO
```

From `.repo_studios/`, run `make studio-generate-import-graph` to execute the producer with repository defaults.

### Key arguments

- `--repo-root` (default `.`): repository root to scan.
- `--output-dir` (default `.repo_studios/reports/producer_reports`): base reports directory for positional bundles.
- `--owned` (repeatable list): top-level folders to treat as “owned”; defaults to `{.repo_studios, legacy}` and always
  includes `.repo_studios`.
- `--artifacts-to-keep` (default `5`): retention window applied after each run.
- `--timestamp`: ISO-8601 string to seed the run directory name (falls back to UTC `now`).
- `--log-level` (default `INFO`): Python logging verbosity.

## Outputs

Each execution produces a positional-encoded bundle at:

`.repo_studios/reports/producer_reports/healthview/import_graph/<YYYYMMDD-HHMM>/`

The run folder contains exactly:

- `manifest.json`: pipeline metadata (viewer/topic/timestamp, inputs, catalog).
- `summary.md`: human-readable digest of findings.
- `telemetry.json`: extracted metrics plus the full legacy payload under `payload`.

Historical run folders are pruned to the configured retention (minimum 1) after each execution.
No `latest_*` pointers are created.

## Consumer notes

- `validate_import_boundaries.py` defaults to loading the latest `telemetry.json` under
  `healthview/import_graph/` and extracts the `payload.graph` adjacency map.
- Orchestrators should load the latest run folder from
  `.repo_studios/reports/producer_reports/healthview/import_graph/` rather than relying on mutable pointers.

## Testing

`pytest .repo_studios/tests/tests_producers/test_generate_import_graph_report.py`
verifies positional bundle creation, telemetry payload contents, and pruning behaviour.

## Update Log

- 2025-12-16: Migrated to positional bundle contract (`manifest.json`, `summary.md`, `telemetry.json`) and removed
  legacy `latest_*` pointers.
