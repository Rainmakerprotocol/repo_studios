# Command Center Architecture

_Last updated: 2025-10-27_

## Overview

- The Command Center automation suite lives under `.repo_studios/command_center/` and mirrors the tiered script pattern we use across Repo Studios.
- Scripts are grouped into `producers/`, `summarizers/`, and `aggregators/`; orchestration stubs will land under `orchestrators/` as we expand entry points.
- Each run writes artifacts to two places: the target's slugged index directory and `.repo_studios/command_center/reports/` for consolidated review.
- Shared helpers now enforce slugged directory names, atomic writes, and configurable retention so reruns do not collide and old files age out predictably (default keep-runs = 3).

## Component Map

- **Producers** (`scripts/producers/`)
  - `generate_commandview_inventory.py` indexes a target folder and emits `<source>_index/<source>_index-YYYY-MM-DD.json` plus the screening report used in later phases.
  - Each producer exposes `run(argv)` so tests and aggregators can import them without spawning subprocesses.
- **Summarizers** (`scripts/summarizers/`)
  - `generate_function_analysis.py` consumes the inventory output, calculates duplicate group metrics, and stores `<source>_analysis-YYYY-MM-DD.json` beside the inventory history.
  - Mirrors to the reports directory follow the same slugging rules as the producers so aggregators have a stable location to read from.
- **Aggregators** (`scripts/aggregators/`)
  - `scan_duplicates.py` orchestrates the inventory and analysis steps (unless `--skip-upstream` is passed), runs the AST duplicate scan, and mirrors JSON + Markdown outputs to both the target index directory and `.repo_studios/command_center/reports/<slug>_duplicate_scan/`.
  - Atomic writes guard against partially written artifacts, and retention runs after each write. Integration coverage lives in `tests/tests_library_integration/duplicates/test_scan_duplicates.py`.
- **Orchestrators** (`scripts/orchestrators/`)
  - Placeholder directory reserved for suite entry points that will sequence producer → summarizer → aggregator operations once the Make targets are defined.

## Data Flow

1. `generate_commandview_inventory.py` builds the target inventory and screening report under `<target>/<target>_index/`.
2. `generate_function_analysis.py` derives duplicate and dependency metrics, persisting them alongside the inventory and the mirrored report tree.
3. `scan_duplicates.py` optionally re-runs the upstream producers, scans for duplicate functions, and writes machine-readable (`*_duplicate_matrix-YYYY-MM-DD.json`) and human-readable (`*_duplicate_summary-YYYY-MM-DD.md`) payloads.
4. Future orchestrators will wrap these steps in tiered Make targets so agents can trigger the full pipeline or individual stages without ad-hoc commands.

## Reporting & Retention

- All outputs are timestamped; there are no mutable `latest.json` pointers.
- Retention currently keeps the three newest matrices and summaries in both the run and index mirrors. The helper is configurable via `--keep-runs`.
- A silent `prune_logs` helper is planned for long-running scripts so they can trim historical runs without emitting extra noise once the new reports layout settles.

## Current State (2025-10-27 Run)

- Latest target: `.repo_studios/command_center/scripts`
- Inventory artifacts: `.repo_studios/command_center/scripts/scripts_index/`
- Duplicate reports: `.repo_studios/command_center/reports/duplicates_scan/repo-studios__command-center__scripts_duplicate_scan/`
- Scanner results: 4 Python files scanned, 99 functions analysed, 3 duplicate groups detected (2 matched to producer findings).

## Planned Enhancements

- Add an `if __name__ == "__main__"` guard to `scan_duplicates.py` so direct CLI invocations match the orchestration flow without requiring manual `run(...)` calls.
- Draft the first orchestrator entry point with tiered Make targets (`studio-*`) to run the full pipeline against known slugged targets.
- Introduce the shared `prune_logs` utility once the reports layout stabilises, keeping folders light without a separate database.
- Spin up the `alignment_protocol` blueprint document to capture our AI/developer collaboration process for future migrations.
- Document secret-handling patterns (`.env`, `.env.template`) alongside standards so agents avoid embedding credentials during automation tasks.