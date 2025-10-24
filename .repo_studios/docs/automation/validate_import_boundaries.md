# validate_import_boundaries.py

**Last updated:** 2025-10-23

## Purpose

`validate_import_boundaries.py` enforces the layering contract between the `agents` and `api` packages. It blends static source scanning with the latest import graph snapshot to highlight disallowed edges, cycles, and file-level violations, applying the transitional allowlist before emitting structured artifacts. The refactor introduces run bundles with pruning, `latest/` pointers, CI-friendly logs, and coverage via targeted pytest cases.

## Invocation

```bash
python .repo_studios/scripts/producers/validate_import_boundaries.py \
  --repo-root . \
  --artifacts-to-keep 5 \
  --log-level INFO
```

From `.repo_studios/`, run `make studio-validate-import-boundaries` to execute the producer with repository defaults.

### Key arguments

- `--repo-root`: repository root used for static scans and path resolution (defaults to four levels above the script).
- `--graph-path`: explicit import graph JSON to analyze; otherwise the latest snapshot under `import_graph_reports/` is used.
- `--output-dir`: destination for structured artifacts (defaults to `.repo_studios/reports/producer_reports/import_boundary_reports`).
- `--allowlist-path`: override the allowlist JSON path (defaults to `.repo_studios/scripts/producers/import_rules_allowlist.json`).
- `--artifacts-to-keep`: number of historical run directories retained after pruning (minimum 1, default 10).
- `--strict`: reserved switch for elevating discouraged edges (currently informational only).
- `--log-level`: logging verbosity (`INFO` default).

## Outputs

Each run creates `.repo_studios/reports/producer_reports/import_boundary_reports/import_boundary_check-<timestamp>/` containing:

- `report.json`: canonical payload with inputs, summary counts, and violation details post-allowlist.
- `report.md`: human-readable synopsis with a table of violations and actionable next steps.
- `log.txt`: key-value diagnostics suitable for CI parsing.
- `violations.json`: trimmed list of remaining violation records (kind, detail, file).

The script also refreshes `.repo_studios/reports/producer_reports/import_boundary_reports/latest/` with copies:

- `latest_report.json`
- `latest_report.md`
- `latest_log.txt`
- `latest_violations.json`

Historical run directories are pruned down to the configured retention window after each execution.

## Diagnostics

- `summary.violation_count` reports violations remaining after allowlist application.
- `summary.violations_by_kind` surfaces counts for `edge`, `cycle`, and `static-import` categories.
- `graph_path` records the import graph snapshot used for the evaluation (or `null` if unavailable).
- `violations[*]` entries capture the exact edge or file to remediate, enabling targeted pruning or code fixes.

## Testing

`pytest .repo_studios/tests/tests_producers/test_validate_import_boundaries.py`

The suite exercises clean runs, violation detection, allowlist exemptions, artifact creation, and historical pruning when the retention window is set to a single run.

## Operational notes

- Ensure `generate_import_graph_report.py` has been executed recently so the latest import graph reflects current topology before running this producer.
- The allowlist supports both top-level edges and specific files; document long-lived exceptions in the repo architecture log when extending it.
- CI integrations should gate on `report.json` rather than log parsing, enabling precise failure classification and easier auditing.
- The emitted Markdown report provides quick triage guidance for devs who encounter the failure locally.
