---
title: validate_markdown_anchors.py
audience: [Copilot, Agents, Developer]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 1.1.0
updated: 2025-12-18
tags: [automation, markdown, anchors, links, producer, healthview]
related_files:
  - .repo_studios/scripts/producers/validate_markdown_anchors.py
  - .repo_studios/tests/tests_producers/test_validate_markdown_anchors.py
  - .repo_studios/Makefile
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - REPORT_NAMING_STANDARDS.md
---

# validate_markdown_anchors.py

## Purpose

`validate_markdown_anchors.py` scans curated Markdown files for internal anchor references and
cross-file links, verifying that every referenced document exists and that GitHub-style heading
slugs resolve. The producer emits JSON and Markdown artifacts so documentation owners can close
broken-link regressions quickly while preserving timestamped history.

## Invocation

```bash
python .repo_studios/scripts/producers/validate_markdown_anchors.py \
  --root . \
  --glob docs/**/*.md \
  --output-dir .repo_studios/reports/producer_reports \
  --artifacts-to-keep 10
```

Key options:

- `--repo-root` (inferred): establishes the base path for relative link validation.
- `--root` (default `.`): directory whose Markdown files should be scanned.
- `--glob`: repeatable glob patterns (defaults to `README.md`, `docs/agents/config_quickstart.md`, `docs/agents/step5_agent_config_system.md`).
- `--output-dir` (default `.repo_studios/reports/producer_reports`): destination for positional bundles.
- `--artifacts-to-keep` (default `10`): retention window applied after each run.
- `--timestamp`: optional ISO-8601 override for deterministic run folder naming (used in tests).
- `--log-level`: logging verbosity (`INFO` default).

## Outputs

Each execution produces a canonical bundle under:

`.repo_studios/reports/producer_reports/healthview/markdown_anchor_validation/<YYYYMMDD-HHMM>/`

Containing exactly:

- `manifest.json`: run metadata (viewer/topic/timestamp), catalog provenance, and a compact summary.
- `summary.md`: human-readable digest of findings.
- `telemetry.json`: extracted metrics plus the full issue payload retained under `payload.report`.

`latest_*` pointers are not written.

## Status semantics

`telemetry.json` retains the legacy issue list and includes `status` and `metrics.issue_count`:

- `ok`: all scanned links resolved successfully; exit status `0`.
- `fail`: at least one missing file or anchor was found; exit status `1`.

Issues are enumerated with `{file, line, kind, target, message}` tuples so downstream tooling can
surface precise remediation steps.

## Testing

Run the dedicated pytest module to exercise happy-path and failure scenarios, plus retention pruning:

```bash
pytest .repo_studios/tests/tests_producers/test_validate_markdown_anchors.py
```

## Operational notes

- External URLs (`http://`, `https://`, `mailto:`) are ignored to avoid unnecessary network checks.
- Anchor slugs follow GitHub normalization rules (lowercase, dash-separated headings with punctuation
  stripped), matching repo documentation conventions.
- Supply additional `--glob` values when auditing new documentation areas; repeats are deduplicated.
- For CI gating, combine this producer with Make target `studio-validate-markdown-anchors` so new
  documentation merges fail fast when anchors drift.

## Update Log

- 2025-12-18: Migrated to canonical positional bundle outputs (manifest/summary/telemetry), removed `latest_*` pointers,
  switched pruning to shared helper, and added DB dual-write markers.
