---
title: Standards Index Diff Producer
audience:
  - Developers
  - Agents
role:
  - Automation
owners:
  - Repo Studios
status: active
version: 2
updated_at: 2025-12-15
tags:
  - producer
  - standards
  - reports
related_files:
  - .repo_studios/scripts/producers/diff_standards_index.py
  - .repo_studios/tests/tests_producers/test_diff_standards_index.py
  - .repo_studios/Makefile
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - .repo_studios/command_center/scripts/libraries/prune_logs.py
---

# diff_standards_index.py

See `.github/instructions/markdown.instructions.md` for repo-wide rules.

## Goals

- Compare two standards index YAML snapshots and classify per-rule deltas.
- Emit a canonical report bundle under positional encoding for automation and (future) DB ingestion.

## System Context

This producer writes reports into the Command Center reports root using positional encoding:

`<reports_root>/<viewer_slug>/<topic>/<YYYYMMDD-HHMM>/`

- `reports_root`: `.repo_studios/command_center/reports` (default)
- `viewer_slug`: `rawview`
- `topic`: `standards_index_diff`

## Agent Instructions

- Prefer consuming `telemetry.json` for structured diff details.
- Treat `manifest.json` as the authoritative inventory of artifacts and inputs.
- Do not rely on mutable `latest_*` pointers (they are intentionally not produced).

## Human Notes

### Invocation

```bash
python .repo_studios/scripts/producers/diff_standards_index.py \
  path/to/baseline_index.yaml \
  path/to/candidate_index.yaml \
  --repo-root . \
  --output-dir .repo_studios/command_center/reports \
  --fail-on severity_changed,added,removed \
  --artifacts-to-keep 10
```

### Key arguments

- `old`, `new` (positional): baseline and candidate standards index YAML files. Relative paths resolve against `--repo-root`.
- `--repo-root` (default `.`): repository root used for resolving relative inputs.
- `--output-dir` (default `.repo_studios/command_center/reports`): reports root used for positional encoding.
- `--run-timestamp`: override run folder slug (`YYYYMMDD-HHMM`, UTC). Use for deterministic runs/tests.
- `--timestamp`: deprecated ISO-8601 seed; prefer `--run-timestamp`.
- `--artifacts-to-keep` (default `10`): retention window (history mode, minimum 1).
- `--fail-on` (default `any`): comma-separated list of change kinds triggering exit code `1`. Supports:
  `{added, removed, severity_changed, rationale_changed, summary_changed, applies_changed, categories_changed, other_changed}`.
- `--json`: optional path to dump the raw diff JSON to a custom location (outside the bundle).
- `--log-level` (default `INFO`): logging verbosity.

### Exit codes

- `0`: no requested failure conditions are met.
- `1`: diff contains change kinds covered by `--fail-on`.
- `2`: inputs are missing or cannot be parsed.

## Outputs

Each run writes exactly three artifacts under:

`.repo_studios/command_center/reports/rawview/standards_index_diff/<YYYYMMDD-HHMM>/`

- `manifest.json`: bundle metadata (viewer/topic/timestamp/inputs/catalog).
- `summary.md`: human-readable report summary.
- `telemetry.json`: structured metrics plus `payload` containing the full diff details.

## Reference Prompts

- "Show me all change kinds and counts from the latest standards index diff telemetry."
- "List all rules with `severity_changed` in the most recent standards index diff."

## Testing

`pytest .repo_studios/tests/tests_producers/test_diff_standards_index.py`

## Update Log

- 2025-12-15 — Migrated to canonical bundle outputs (manifest/summary/telemetry), positional encoding under Command Center reports root, removed `latest_*` pointers and legacy multi-file artifacts.
