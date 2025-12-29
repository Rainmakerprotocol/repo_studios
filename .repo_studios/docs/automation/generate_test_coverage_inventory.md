---
title: generate_test_coverage_inventory.py
audience: [Copilot, Agents, Developer]
role: [AutomationDoc]
owners: [repo_studios_ai]
status: active
version: 2
updated_at: 2025-12-26
tags: [automation, producer, healthview, test-coverage]
related_files:
  - .repo_studios/scripts/producers/generate_test_coverage_inventory.py
  - .repo_studios/tests/tests_producers/test_generate_test_coverage_inventory.py
  - .repo_studios/command_center/docs/db_integrations/db_integration_generate_test_coverage_inventory.md
---

# generate_test_coverage_inventory.py

**Last updated:** 2025-12-17

## Purpose

`generate_test_coverage_inventory.py` ingests a Coverage.py XML report and produces a per-file
inventory showing how many functions exist, how many are exercised by tests, and which remain
uncovered.

The producer emits a positional-encoded bundle (`manifest.json`, `summary.md`, `telemetry.json`)
so agents can monitor coverage trends, highlight low-coverage modules, and gate automation via
minimum coverage thresholds.

## Invocation

```bash
python .repo_studios/scripts/producers/generate_test_coverage_inventory.py \
  --repo-root . \
  --coverage-xml .repo_studios/tests/fixtures/test_run_coverage/coverage.xml \
  --output-dir .repo_studios/reports/producer_reports \
  --min-coverage 75 \
  --artifacts-to-keep 10
```

### Agent-friendly one-shot mode (refresh coverage first)

When you need the producer to be self-contained for agent workflows, enable coverage refresh. This
regenerates the `--coverage-xml` file by running pytest with `pytest-cov`, then builds the inventory
from the freshly written XML.

```bash
python .repo_studios/scripts/producers/generate_test_coverage_inventory.py \
  --repo-root . \
  --coverage-xml coverage.xml \
  --refresh-coverage-xml \
  --refresh-tests .repo_studios/tests \
  --refresh-cov-target .repo_studios \
  --output-dir .repo_studios/reports/producer_reports \
  --artifacts-to-keep 10
```

Generate the XML input with Coverage.py (upstream of this producer), for example:

```bash
pytest --cov --cov-report=xml:.repo_studios/tests/fixtures/test_run_coverage/coverage.xml
```

### Key arguments

- `--repo-root` (default inferred): repository root used to resolve all relative paths.
- `--coverage-xml` (default `.repo_studios/tests/fixtures/test_run_coverage/coverage.xml`): Coverage.py
  XML report to analyse.
- `--output-dir` (default `.repo_studios/reports/producer_reports`): reports root for positional
  bundle outputs.
- `--min-coverage`: optional minimum overall percentage; the script exits `1` and marks the run as
  `threshold_failed` when overall coverage is below the supplied value.
- `--artifacts-to-keep` (default `10`): retention window applied post-run.
- `--include-empty`: list files that appear in the coverage XML but contain no functions (defaults
  to filtering them out).
- `--timestamp`: ISO-8601 value for deterministic run folder names (defaults to current UTC).
- `--log-level` (default `INFO`): logging verbosity.

Coverage refresh (optional):

- `--refresh-coverage-xml`: run pytest with coverage before generating the inventory; requires
  `pytest-cov`.
- `--refresh-tests` (default `.repo_studios/tests`): test paths passed to pytest during refresh.
- `--refresh-cov-target` (default `.repo_studios`): repeatable `--cov=<target>` inputs passed to
  pytest-cov.
- `--refresh-pytest-args`: pass-through args for pytest; this option must appear last.

## Outputs

Each execution creates
`.repo_studios/reports/producer_reports/healthview/test_coverage_inventory/<YYYYMMDD-HHMM>/`
containing:

- `manifest.json`: run metadata and provenance.
- `summary.md`: Markdown table of per-file function coverage.
- `telemetry.json`: extracted metrics plus a `payload` section that includes the per-file coverage list.

Historical directories are pruned to the configured retention (minimum 1). No `latest_*` pointers
are generated.

## Status semantics

- `ok`: overall function coverage meets or exceeds the configured threshold (or no threshold
  supplied).
- `threshold_failed`: overall coverage fell below `--min-coverage`; the CLI exits with status `1`.
- `no_functions`: the coverage XML mapped to zero functions (often meaning tests never executed any
  tracked modules); exit code is `0`.

`files_below_threshold` records repo-relative paths whose individual coverage percentages are below
the configured threshold (when present).

## Testing

`pytest .repo_studios/tests/tests_producers/test_generate_test_coverage_inventory.py`
exercises artifact creation, threshold enforcement, and retention behaviour using fixture coverage
XML files.

## Operational notes

- The script only analyses files present in the Coverage.py XML. Ensure upstream test runs generate
  the XML before invoking the producer.
- `--refresh-coverage-xml` is intended for agent workflows that need a single command to produce
  fresh coverage input.
- Function coverage is determined by matching executed line numbers to AST-defined function spans,
  including class and async methods.
- Combine this producer with `--min-coverage` inside orchestrators or CI jobs to fail early when
  coverage regresses.
- Large XML files are parsed once per run; store them alongside test fixtures (for example,
  `.repo_studios/tests/fixtures/test_run_coverage/`) so they are not confused with report outputs.

## References

See [../../../.github/instructions/markdown.instructions.md](../../../.github/instructions/markdown.instructions.md)
for repo-wide Markdown rules.
