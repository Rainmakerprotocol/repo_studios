---
title: generate_dependency_hygiene_report.py
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: active
version: 1.1.0
updated: 2025-12-16
tags:
  - automation
  - healthview
  - dependency-hygiene
related_files:
  - ../../scripts/producers/generate_dependency_hygiene_report.py
  - ../../tests/tests_producers/test_generate_dependency_hygiene_report.py
  - ../../command_center/docs/db_integrations/dependency_hygiene.md
---

# generate_dependency_hygiene_report.py

## Purpose

`generate_dependency_hygiene_report.py` scans pinned dependency manifests, flags risky specifications, and emits structured artifacts so agents can track hygiene regressions. Reports consolidate requirement files (and optionally `pyproject.toml`) into a canonical 3-artifact bundle (`manifest.json`, `summary.md`, `telemetry.json`) with retention pruning.

This script is now aligned with the canonical producer bundle contract: each run writes a single
positional-encoded folder containing `manifest.json`, `summary.md`, and `telemetry.json`.

## Invocation

```bash
python .repo_studios/scripts/producers/generate_dependency_hygiene_report.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports \
  --requirements-pattern requirements.txt \
  --requirements-pattern requirements/*.txt \
  --artifacts-to-keep 10
```

### Key arguments

- `--repo-root` (default `.`): repository root used to resolve requirement file globs.
- `--output-dir` (default `.repo_studios/reports/producer_reports`): base reports directory for positional bundles.
- `--requirements-pattern` (repeatable): glob(s) appended to the default trio `("requirements.txt", "requirements-dev.txt", "requirements/*.txt")` when provided.
- `--skip-pyproject`: omit `pyproject.toml` scanning (enabled by default when the file is present and `tomllib` is available).
- `--artifacts-to-keep` (default `10`): retention window applied after each run.
- `--timestamp`: ISO-8601 string to seed the run directory name (falls back to UTC `now`).
- `--log-level` (default `INFO`): Python logging verbosity.

Exit codes: `0` when no hygiene issues are detected, `1` when any issue is recorded.

## Outputs

Each execution produces a positional-encoded bundle at:

`.repo_studios/reports/producer_reports/healthview/dependency_hygiene/<YYYYMMDD-HHMM>/`

The run folder contains exactly:

- `manifest.json`: pipeline metadata (viewer/topic/timestamp, inputs, catalog).
- `summary.md`: human-readable digest of findings.
- `telemetry.json`: extracted metrics plus the full legacy payload under `payload`.

Historical run folders are pruned to the configured retention (minimum 1) after each execution.
No `latest_*` pointers are created.

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
