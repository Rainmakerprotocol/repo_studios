# generate_dependency_hygiene_report.py

**Last updated:** 2025-10-22

## Purpose

`generate_dependency_hygiene_report.py` scans pinned dependency manifests, flags risky specifications, and emits structured artifacts so agents can track hygiene regressions. Reports consolidate requirement files (and optionally `pyproject.toml`) into JSON/Markdown/log outputs with pruning and latest pointers.

## Invocation

```bash
python .repo_studios/scripts/producers/generate_dependency_hygiene_report.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports/dependency_hygiene_reports \
  --requirements-pattern requirements.txt \
  --requirements-pattern requirements/*.txt \
  --artifacts-to-keep 10
```

### Key arguments

- `--repo-root` (default `.`): repository root used to resolve requirement file globs.
- `--output-dir` (default `.repo_studios/reports/producer_reports/dependency_hygiene_reports`): destination for timestamped runs and `latest_*` aliases.
- `--requirements-pattern` (repeatable): glob(s) appended to the default trio `("requirements.txt", "requirements-dev.txt", "requirements/*.txt")` when provided.
- `--skip-pyproject`: omit `pyproject.toml` scanning (enabled by default when the file is present and `tomllib` is available).
- `--artifacts-to-keep` (default `10`): retention window applied after each run.
- `--timestamp`: ISO-8601 string to seed the run directory name (falls back to UTC `now`).
- `--log-level` (default `INFO`): Python logging verbosity.

Exit codes: `0` when no hygiene issues are detected, `1` when any issue is recorded.

## Outputs

Each execution produces `.repo_studios/reports/producer_reports/dependency_hygiene_reports/dependency_hygiene-<timestamp>/` containing:

- `report.json`: canonical payload with fields
  - `schema_version`: currently `1`.
  - `generated_utc`: ISO timestamp of execution.
  - `repo_root`: absolute root scanned.
  - `summary`: `{status, issue_count, requirements_scanned, pyproject_scanned}`.
  - `issue_counts`: list of `{kind, count}` sorted by prevalence.
  - `requirements_patterns`: patterns evaluated.
  - `requirements_files`: resolved requirement file paths (repo-relative when possible).
  - `pyproject_path`: repo-relative path when `pyproject.toml` was scanned else `null`.
  - `issues`: list of `{kind, file, line, spec}` entries.
- `report.md`: human-readable summary with sections for summary metrics, issue counts, and a bullet list of offending specs.
- `log.txt`: key/value digest for automation (`status`, counts, and enumerated issues).

`latest_report.json`, `latest_report.md`, and `latest_report.log` at the output root mirror the most recent run. Historical directories are pruned to the configured retention (minimum 1) after each execution.

## Status semantics

- `passed`: no hygiene issues discovered.
- `failed`: any issue detected (`issue_count > 0`).

Hygiene issue kinds currently emitted:

- `duplicate`: dependency declared more than once across the same requirement file.
- `editable_install`: editable installs (`-e/--editable`).
- `local_path`: local filesystem references (relative or absolute).
- `unpinned`: specs without exact `==` pins.
- `vcs_ref`: VCS references (`git+`, `hg+`, `svn+`, `bzr+`).

## Testing

`pytest .repo_studios/tests/tests_producers/test_generate_dependency_hygiene_report.py`
exercises artifact creation, pruning behaviour, and issue serialization scenarios.

## Operational notes

- When `tomllib` is absent, the script silently skips `pyproject.toml` inspection; install Python 3.11+ to re-enable TOML parsing.
- Requirement pattern globbing is repo-relative. Ensure custom patterns include subdirectories (e.g. `deps/*.txt`).
- Downstream pipelines should interpret `status` or `summary.issue_count` instead of CLI exit codes when running in tolerant contexts.
