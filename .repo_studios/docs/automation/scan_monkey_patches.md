# scan_monkey_patches.py

**Last updated:** 2025-10-23

## Purpose

`scan_monkey_patches.py` inventories monkey patch activity across the repository. It identifies attribute reassignments, `sys.modules` rewrites, import-time side effects, and other high-risk behaviors so automation can monitor drift and teams can prioritize remediation. The refactored producer emits structured artifacts with pruning, latest pointers, and optional git blame enrichment.

## Invocation

```bash
python .repo_studios/scripts/producers/scan_monkey_patches.py \
  --repo-root . \
  --root src \
  --exclude-dirs .git .venv build dist \
  --exclude-globs external/** libraries/** \
  --context-lines 2 \
  --artifacts-to-keep 10
```

From `.repo_studios/`, run `make studio-scan-monkey-patches` to execute the producer with repository defaults.

### Key arguments

- `--repo-root`: repository root used to resolve relative paths (defaults to three levels up from the script).
- `--root`: directory to scan. Accepts relative paths (resolved against `--repo-root`) or absolute paths.
- `--output-dir`: override for the artifact directory (defaults to `.repo_studios/reports/producer_reports/monkey_patch_scans`).
- `--project-packages`: optional list of owned packages. Defaults to auto-detected top-level directories plus `tests`.
- `--exclude-dirs`: directory names to skip (defaults to repo-standard set including `.git`, `.venv`, `node_modules`, and build outputs).
- `--exclude-globs`: glob patterns to skip entire subtrees (defaults include vendor trees like `external/**`).
- `--context-lines`: number of source lines captured around each finding (default `2`).
- `--with-git`: include git blame metadata when available.
- `--strict`: mark runs as errors when parse failures occur (default soft-fail).
- `--artifacts-to-keep`: number of historical runs retained after pruning (default `10`).
- `--log-level`: logging verbosity (default `INFO`).

The script auto-creates output directories, normalizes exclude lists, and records the exact configuration used for each scan in the summary payload.

## Outputs

Each run creates `.repo_studios/reports/producer_reports/monkey_patch_scans/monkey_patch_scan-<timestamp>/` with:

- `report.json`: structured summary payload (schema version, configuration, counts by category/import base/file, parse error totals).
- `report.md`: human-readable synopsis with aggregate tables and next-step recommendations.
- `log.txt`: key-value diagnostics for CI parsing.
- `matches.json`: full list of findings (path, line, category, intent, context, optional git metadata).
- `matches.tsv`: tab-separated export for spreadsheet workflows (written when findings exist).

The producer also refreshes `.repo_studios/reports/producer_reports/monkey_patch_scans/latest/` with copies of the most recent artifacts:

- `latest_report.json`
- `latest_report.md`
- `latest_log.txt`
- `latest_matches.json`
- `latest_matches.tsv` (when applicable)

Historical runs are pruned to the configured retention window after each execution.

## Diagnostics

- `files_scanned`, `files_with_findings`, and `total_findings` quantify scan breadth and debt density.
- `summary.by_category` surfaces high-risk patterns (e.g., `builtins_mutation`, `sys_modules_assignment`).
- `summary.by_import_base` highlights popular third-party targets that may need dedicated strategies.
- `summary.top_files` ranks files by finding count to focus follow-up reviews.
- `parse_errors` tracks files that failed to parse; runs surface as `warn` when non-zero and `strict` is disabled.

## Testing

`pytest .repo_studios/tests/tests_producers/test_scan_monkey_patches.py`

The suite validates structured artifact generation, summary counters, retention pruning, and ensures the returned payload metadata reflects the run configuration.

## Operational notes

- Scans default to Python sources but honor exclusion lists for vendor directories, virtual environments, and generated assets.
- Findings capture two lines of context by default; increase `--context-lines` if richer snippets aid reviews.
- Use `--with-git` sparingly on very large repositories to avoid prolonged blame operations.
- Consider wiring a CI gate once baselines are established so import-time mutations or global overrides trigger alerts.
- Extend the heuristics in `scan_monkey_patches.py` if new categories of patches need tracking (e.g., SQL-level monkey patches or language-specific runtime tweaks).
