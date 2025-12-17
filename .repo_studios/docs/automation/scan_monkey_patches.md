---
title: scan_monkey_patches — Monkey Patch Inventory Producer
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: approved
version: 2.0.0
updated: 2025-12-17
tags:
  - producers
  - healthview
  - monkey_patches
  - pruning
  - db
related_files:
  - ../../scripts/producers/scan_monkey_patches.py
  - ../../tests/tests_producers/test_scan_monkey_patches.py
  - ../../command_center/scripts/libraries/database_integration.py
  - ../../command_center/docs/db_integrations/db_integration_monkey_patches.md
---

# scan_monkey_patches.py

## Purpose

`scan_monkey_patches.py` inventories monkey patch activity across the repository. It identifies attribute reassignments, `sys.modules` rewrites, import-time side effects, and other high-risk behaviors so automation can monitor drift and teams can prioritize remediation.

The producer emits a positional-encoded canonical bundle (`manifest.json`, `summary.md`, `telemetry.json`) and includes `DB_INTEGRATION_MARKER:` tags at each persistence call site.

## Invocation

```bash
python .repo_studios/scripts/producers/scan_monkey_patches.py \
  --repo-root . \
  --root src \
  --exclude-dirs .git .venv build dist \
  --exclude-globs external/** libraries/** \
  --context-lines 2 \
  --keep 10
```

From `.repo_studios/`, run `make studio-scan-monkey-patches` to execute the producer with repository defaults.

### Key arguments

- `--repo-root`: repository root used to resolve relative paths (defaults to three levels up from the script).
- `--root`: directory to scan. Accepts relative paths (resolved against `--repo-root`) or absolute paths.
- `--output-dir`: override for the reports root (defaults to `.repo_studios/reports/producer_reports`).
- `--project-packages`: optional list of owned packages. Defaults to auto-detected top-level directories plus `tests`.
- `--exclude-dirs`: directory names to skip (defaults to repo-standard set including `.git`, `.venv`, `node_modules`, and build outputs).
- `--exclude-globs`: glob patterns to skip entire subtrees (defaults include vendor trees like `external/**`).
- `--context-lines`: number of source lines captured around each finding (default `2`).
- `--with-git`: include git blame metadata when available.
- `--strict`: mark runs as errors when parse failures occur (default soft-fail).
- `--keep` / `--artifacts-to-keep`: number of historical runs retained after pruning (default `5`).
- `--timestamp`: override the run timestamp slug (UTC) in `YYYYMMDD-HHMM` format (primarily for deterministic tests).
- `--log-level`: logging verbosity (default `INFO`).

The script auto-creates output directories, normalizes exclude lists, and records the exact configuration used for each scan in the summary payload.

## Outputs
Each run creates a positional-encoded canonical bundle under:

`.repo_studios/reports/producer_reports/healthview/monkey_patches/<YYYYMMDD-HHMM>/`

The bundle contains exactly:

- `manifest.json`: machine-readable metadata + structured findings payload.
- `summary.md`: human-readable synopsis with aggregate tables and next-step recommendations.
- `telemetry.json`: extracted metrics for time-series ingestion.

Historical runs are pruned to the configured retention window after each execution.

### Deprecated outputs (removed)

- No mutable `latest_*` pointers.
- No legacy compatibility mirror under `.repo_studios/monkey_patch/`.
- No `.tsv` exports; structured finding details live in `manifest.json`.

## Diagnostics

- `telemetry.json.metrics` captures run counts and category distributions.
- `manifest.json.payload.summary.by_category` surfaces high-risk patterns (e.g., `builtins_mutation`, `sys_modules_assignment`).
- `manifest.json.payload.summary.by_import_base` highlights popular third-party targets that may need dedicated strategies.
- `manifest.json.payload.summary.top_files` ranks files by finding count to focus follow-up reviews.
- `manifest.json.payload.parse_errors` tracks files that failed to parse; runs surface as `warn` when non-zero and `strict` is disabled.

## Testing

`pytest .repo_studios/tests/tests_producers/test_scan_monkey_patches.py`

The suite validates structured artifact generation, summary counters, retention pruning, and ensures the returned payload metadata reflects the run configuration.

## Operational notes

- Scans default to Python sources but honor exclusion lists for vendor directories, virtual environments, and generated assets.
- Findings capture two lines of context by default; increase `--context-lines` if richer snippets aid reviews.
- Use `--with-git` sparingly on very large repositories to avoid prolonged blame operations.
- Consider wiring a CI gate once baselines are established so import-time mutations or global overrides trigger alerts.
- Extend the heuristics in `scan_monkey_patches.py` if new categories of patches need tracking (e.g., SQL-level monkey patches or language-specific runtime tweaks).

## Update Log

- 2025-12-17 — Migrated producer to positional encoding + canonical 3-artifact bundle with DB integration markers; removed legacy alias + latest pointers.
