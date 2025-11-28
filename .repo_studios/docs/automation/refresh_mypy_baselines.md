# Refresh mypy baselines

## Purpose

`refresh_mypy_baselines.py` standardises the stored mypy output snapshots that agents and
soft gates consume. It runs mypy for each configured target, writes structured
artifacts into `.repo_studios/reports/orchestrator_runs/mypy_baselines/`, and maintains
`latest_*.txt` pointers only when the run succeeds.

## Invocation

```bash
python -m .repo_studios.scripts.utilities.refresh_mypy_baselines \
  --repo-root . \
  --log-level INFO
```

Key flags:

- `--target label=path[:filename]` to add or override a baseline target.
- `--output-dir` to direct artifacts elsewhere inside the repo.
- `--no-append-timestamp` to omit the trailing refreshed marker from each file.
- `--artifacts-to-keep` to cap the number of timestamped run directories.

## Outputs

Each run creates a timestamped folder (`mypy_baselines-YYYYMMDD_HHMMSS`) under
`.repo_studios/reports/orchestrator_runs/mypy_baselines/` that
contains:

- `bundle_summary.json` – structured metadata (status, commands, durations).
- `status.json` – compact status payload for quick triage.
- `SUMMARY.md` – human-readable report of target outcomes.
- `mypy_<label>.txt` – raw mypy output per target, with optional refreshed stamp.
- `<label>_error.txt` – only when the mypy invocation failed.

Successful runs refresh `latest_*.txt` pointers alongside `latest_bundle_summary.json`
and `latest_SUMMARY.md`. Failed targets leave existing pointers untouched.

## Retention

The script keeps the most recent five runs by default. Override with
`--artifacts-to-keep` when a deeper history is required. Runs that include a
`.keep` sentinel file are never pruned.

## Validation

```bash
pytest .repo_studios/tests/tests_utilities/test_refresh_mypy_baselines.py
```

This suite covers success paths, failure handling, and custom target overrides.
