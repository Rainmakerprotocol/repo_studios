# generate_test_coverage_inventory.py

**Last updated:** 2025-11-23

## Purpose

`generate_test_coverage_inventory.py` ingests a Coverage.py XML report and produces a per-file inventory showing how many functions exist, how many are exercised by tests, and which remain uncovered. The producer emits JSON, Markdown, CSV, and log artifacts so agents can monitor coverage trends, highlight low-coverage modules, and gate automation via minimum coverage thresholds.

## Invocation

```bash
python .repo_studios/scripts/producers/generate_test_coverage_inventory.py \
  --repo-root . \
  --coverage-xml .repo_studios/reports/producer_reports/test_run_coverage/coverage.xml \
  --output-dir .repo_studios/reports/producer_reports/test_coverage_reports \
  --min-coverage 75 \
  --artifacts-to-keep 10
```

Generate the XML input with Coverage.py, for example:

```bash
pytest --cov --cov-report=xml:.repo_studios/reports/producer_reports/test_run_coverage/coverage.xml
```

### Key arguments

- `--repo-root` (default inferred): repository root used to resolve all relative paths.
- `--coverage-xml` (default `.repo_studios/reports/producer_reports/test_run_coverage/coverage.xml`): Coverage.py XML report to analyse.
- `--output-dir` (default `.repo_studios/reports/producer_reports/test_coverage_reports`): destination for timestamped run folders and `latest_*` pointers.
- `--min-coverage`: optional minimum overall percentage; the script exits `1` and marks the run as `threshold_failed` when overall coverage is below the supplied value.
- `--artifacts-to-keep` (default `10`): retention window applied post-run.
- `--include-empty`: list files that appear in the coverage XML but contain no functions (defaults to filtering them out).
- `--timestamp`: ISO-8601 value for deterministic run folder names (defaults to current UTC).
- `--log-level` (default `INFO`): logging verbosity.

## Outputs

Each execution creates `.repo_studios/reports/producer_reports/test_coverage_reports/test_coverage-<timestamp>/` containing:

- `report.json`: schema version 1 payload with fields
  - `generated_utc`, `coverage_source`, `repo_root`.
  - `summary`: `{status, total_files, total_functions, covered_functions, overall_coverage_pct, files_below_threshold, threshold, include_empty}`.
  - `files`: list of `{path, absolute_path, function_count, functions_covered, coverage_pct, uncovered_functions}` sorted from lowest coverage upwards.
- `report.md`: Markdown table of the same data for quick reviews.
- `report.csv`: spreadsheet-friendly export mirroring the JSON file list.
- `log.txt`: key/value digest for automation hooks (`status`, totals, threshold preview).

`latest_report.json`, `latest_report.md`, `latest_report.csv`, and `latest_report.log` at the output root mirror the newest run. Historical directories are pruned to the configured retention (minimum 1).

## Status semantics

- `ok`: overall function coverage meets or exceeds the configured threshold (or no threshold supplied).
- `threshold_failed`: overall coverage fell below `--min-coverage`; the CLI exits with status `1`.
- `no_functions`: the coverage XML mapped to zero functions (often meaning tests never executed any tracked modules); exit code is `0`.

`files_below_threshold` records repo-relative paths whose individual coverage percentages are below the configured threshold (when present).

## Testing

`pytest .repo_studios/tests/tests_producers/test_generate_test_coverage_inventory.py`
exercises artifact creation, threshold enforcement, and retention behaviour using fixture coverage XML files.

## Operational notes

- The script only analyses files present in the Coverage.py XML. Ensure upstream test runs generate the XML before invoking the producer.
- Function coverage is determined by matching executed line numbers to AST-defined function spans, including class and async methods.
- Combine this producer with `--min-coverage` inside orchestrators or CI jobs to fail early when coverage regresses.
- Large XML files are parsed once per run; storing them under `.repo_studios/reports/producer_reports/test_run_coverage/` keeps inputs discoverable for future audits.
