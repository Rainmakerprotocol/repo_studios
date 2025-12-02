# run_standards_index_cli.py

**Last updated:** 2025-12-01

## Overview

`run_standards_index_cli.py` wraps the Repo Studios standards index in a modernized orchestrator surface. The CLI still prints
human-friendly results for `list`, `search`, `show`, and `stats`, while now emitting structured bundles so analysts and
automation can rely on retained history, provenance metadata, and standard Command Center helpers for path/option resolution.

## Invocation

### Automation (redirect enabled)

Allow the shim to redirect into the Standards Integrity topic orchestrator while still
emitting CLI artifacts:

```bash
python .repo_studios/scripts/orchestrators/run_standards_index_cli.py \
  --repo-root . \
  --output-dir .repo_studios/reports/orchestrator_runs/standards_index_cli \
  --artifacts-to-keep 5 \
  --log-level INFO \
  stats
```

For filtered automation runs (no legacy flag):

```bash
python .repo_studios/scripts/orchestrators/run_standards_index_cli.py \
  --repo-root . \
  --output-dir .repo_studios/reports/orchestrator_runs/standards_index_cli \
  --index-path .repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml \
  list \
  --severity error \
  --category security
```

### Interactive CLI (skip redirect)

Set `RUN_STANDARDS_INDEX_CLI_USE_LEGACY=1` only for ad-hoc queries when you want to
avoid the standards integrity redirect. Remember to clear the flag after use.

```powershell
$old = $env:RUN_STANDARDS_INDEX_CLI_USE_LEGACY
$env:RUN_STANDARDS_INDEX_CLI_USE_LEGACY = "1"
try {
    python .repo_studios/scripts/orchestrators/run_standards_index_cli.py stats
} finally {
    if ($null -eq $old) { Remove-Item Env:RUN_STANDARDS_INDEX_CLI_USE_LEGACY -ErrorAction SilentlyContinue }
    else { $env:RUN_STANDARDS_INDEX_CLI_USE_LEGACY = $old }
}
```

```bash
# bash/zsh interactive example
RUN_STANDARDS_INDEX_CLI_USE_LEGACY=1 \
  python .repo_studios/scripts/orchestrators/run_standards_index_cli.py list --severity warn
```

Key flags:

- `--repo-root`: Optional override when running outside of the repo checkout.
- `--output-dir`: Destination for structured run bundles (defaults to `.repo_studios/reports/orchestrator_runs/standards_index_cli`).
- `--index-path`: Alternate standards index path (defaults to `.repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml`).
- `--artifacts-to-keep`: Retention window for orchestrator bundles and latest pointers (minimum 1, default 5).
- `--log-level`: Logging verbosity across helpers (`INFO` default).
- Subcommands:
  - `list`: Prints rule IDs matching optional filters.
  - `search`: Prints `<id>: <summary>` rows for matches (requires `--text`).
  - `show`: Renders a single rule as YAML via `--id`.
  - `stats`: Outputs total count, severity distribution, and integrity hash.
- Filtering options (`list`/`search`): `--severity`, `--category`, `--category-multi` (repeatable), `--applies`, `--source-frag`, `--text` (`search` only).

## Outputs

Each execution writes `standards_index_cli-<timestamp>/` under the configured `--output-dir`, containing:

- `report.json`: Canonical payload describing command, filters, summary counts, provenance (index path, retention), stdout lines, and
  results payload (rule IDs, matches, rule document, or stats).
- `report.md`: Markdown summary mirroring the JSON core fields, filter set, and stdout snippet.
- `bundle_summary.json`: Lightweight digest (`command`, `overall_status`, `items_returned`, `exit_code`).
- `stdout.txt`: Captured stdout for the run, preserving interactive output for audit trails.

Pointer files (`latest_report.json`, `latest_report.md`, `latest_bundle_summary.json`, `latest_stdout.txt`) update alongside each run. History
is pruned to `--artifacts-to-keep` bundles.

## Diagnostics

Key fields in `report.json`:

- `summary.exit_code`, `summary.overall_status`, `summary.items_returned`, `summary.total_rules`, `summary.severity_counts`.
- `filters`: Canonical severity (aliases resolved), categories, text fragments, and rule IDs as applicable.
- `results`: Command-specific payload (rule IDs, match summaries, YAML rule body, or stats map).
- `error`: Present when exit code is non-zero (missing rule, invalid input, index failures).
- `paths.index_path`: Absolute path to the standards index used for the run.

Markdown reports embed filters and stdout output for quick review without opening JSON.

## Testing

Unit coverage lives in `.repo_studios/tests/tests_orchestrators/test_run_standards_index_cli.py` and exercises:

- `list` command filtering and artifact emission.
- `show` command error handling (missing rule) with structured summary propagation.
- `stats` command severity counts and stdout mirroring.

Run with:

```bash
.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_orchestrators/test_run_standards_index_cli.py
```

## Operational Notes

- The CLI remains stdout-first for interactive use; structured bundles are emitted in parallel for retention.
- Severity aliases (`low`, `medium`, `high`) are mapped with warnings; prefer canonical severities in scripts.
- `--index-path` simplifies testing and allows experimentation with alternate catalogs prior to committing updates.
- The canonical index pointer lives at `.repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml`; if that pointer is missing, regenerate the bundle via `python .repo_studios/scripts/producers/generate_standards_index.py` or supply an alternate archive path with `--index-path`.
- When wiring the command into broader orchestration, prefer calling the import-safe `run(argv=None)` helper instead of spawning a subprocess.
