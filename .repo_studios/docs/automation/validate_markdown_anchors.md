# validate_markdown_anchors.py

**Last updated:** 2025-11-23

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
  --output-dir .repo_studios/reports/producer_reports/markdown_anchor_validation_reports \
  --artifacts-to-keep 10
```

Key options:

- `--repo-root` (inferred): establishes the base path for relative link validation.
- `--root` (default `.`): directory whose Markdown files should be scanned.
- `--glob`: repeatable glob patterns (defaults to `README.md`, `docs/agents/config_quickstart.md`, `docs/agents/step5_agent_config_system.md`).
- `--output-dir` (default `.repo_studios/reports/producer_reports/markdown_anchor_validation_reports`):
  destination for run folders and `latest_*` pointers.
- `--artifacts-to-keep` (default `10`): retention window applied after each run.
- `--timestamp`: optional ISO-8601 override for deterministic run folder naming (used in tests).
- `--log-level`: logging verbosity (`INFO` default).

## Outputs

Each execution produces
`.repo_studios/reports/producer_reports/markdown_anchor_validation_reports/markdown_anchor_validation-<timestamp>/`
containing:

- `report.json`: schema version 1 payload capturing the scan root, patterns, issue list, and files examined.
- `report.md`: human-readable summary listing any missing anchors or files.

The script also refreshes `latest_report.json` and `latest_report.md` pointers to the newest run and
prunes older folders to the configured retention window.

## Status semantics

`report.json` includes `status` and `issue_count` fields:

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
