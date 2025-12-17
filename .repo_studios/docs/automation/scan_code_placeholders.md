---
title: scan_code_placeholders.py
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: approved
version: 1.2.0
updated: 2025-12-17
tags:
  - automation
  - producers
  - placeholders
related_files:
  - ../../scripts/producers/scan_code_placeholders.py
  - ../../tests/tests_producers/test_scan_code_placeholders.py
  - ../../command_center/scripts/libraries/database_integration.py
---

# scan_code_placeholders.py

**Last updated:** 2025-11-23

## Purpose

`scan_code_placeholders.py` inventories debt markers such as TODO, FIXME, and NOTE across the repository. The producer emits structured artifacts so agents can track placeholder volume, identify hot files, and gate builds on unapproved entries. The modernized implementation replaces the legacy stdout-only helper with JSON/Markdown/log bundles, retention pruning, and allowlisting knobs.

## Invocation

```bash
python .repo_studios/scripts/producers/scan_code_placeholders.py \
  --repo-root . \
  --root src \
  --include-ext .py .md .yaml \
  --patterns TODO FIXME NOTE \
  --allowlist-file .repo_studios/config/placeholder_allowlist.txt \
  --artifacts-to-keep 5
```

From `.repo_studios/`, run `make studio-scan-code-placeholders` to execute the producer with repository defaults.

### Key arguments

- `--repo-root`: repository root used to resolve relative paths (defaults to three levels up from the script).
- `--root`: directory to scan. Accepts relative paths (resolved against `--repo-root`) or absolute paths. Defaults to the repo root.
- `--output-dir`: override for the *base* artifact directory (defaults to `.repo_studios/reports/producer_reports`).
- `--include-ext`: list of file extensions to include. Defaults to `.py`, `.md`, `.txt`, `.js`, `.ts`, `.yaml`, `.yml`, `.json`.
- `--patterns`: tokens to detect. Defaults to `TODO`, `FIXME`, `NOTE`, `XXX`, `OPTIMIZE`, `REVIEW`.
- `--allowlist-file`: optional file containing `<path>:<line>` entries (paths relative to repo root) that should be ignored.
- `--exclude-prefix`: directory prefixes to skip. Accepts multiple values; use `*/segment/` to skip any path containing `segment` as a directory. Defaults to `.venv/`, `node_modules/`, and any `site-packages/` path when scanning the repo root. Pass `--exclude-prefix` with no values to disable defaults.
- `--artifacts-to-keep`: number of historical runs to retain (default `5`).
- `--timestamp`: ISO8601 timestamp used to seed the run directory slug.
- `--log-level`: standard Python logging level (default `INFO`).

The script auto-creates output directories and normalizes extensions/patterns for case-insensitive matching.

## Outputs

Each run creates a canonical bundle under:

`.repo_studios/reports/producer_reports/healthview/code_placeholders/<YYYYMMDD-HHMM>/`

The bundle contains exactly three artifacts:

- `manifest.json`: full payload + scan settings + a sampled list of matches (truncated to a bounded limit).
- `summary.md`: human-readable report (totals + a small findings sample).
- `telemetry.json`: structured metrics and a copy of the summary payload for downstream automation.

Historical runs are pruned to the configured retention window after each execution.

## Diagnostics

- `allowlist_size` surfaces how many entries were ignored.
- `exclude_prefixes` and `exclude_segments` list the active directory filters, and `default_exclusions_applied` confirms whether repo-root defaults were used.
- `summary.by_pattern` and `summary.by_extension` help rank debt sources and languages.
- Tokens are only recorded when the matched marker is written in uppercase (for example `TODO`, `FIXME`, `NOTE`), which reduces noise from prose headings such as “Review” or “Note”.
- Empty runs still emit artifacts with `status: ok` and `total_matches: 0`, allowing CI to treat absence of placeholders as a success.

## Allowlist format

Allowlist files accept comment lines (prefixed with `#`) and entries formatted as `relative/path.py:42`. The scan ignores malformed lines. Provide paths relative to the repo root to keep entries stable across machines.

### Allowlist governance

- Every allowlist entry must include the path, line number, owning team/individual, justification, and a review date ≤30 days out.
- Store the allowlist at `.repo_studios/config/placeholder_allowlist.txt`; treat it as a required artifact in code reviews.
- Renewals older than 30 days require an updated justification logged in `.repo_studios/command_center/docs/decision_log.md`.
- After editing the allowlist, re-run `make studio-scan-code-placeholders` to confirm totals, pruning, and latest pointers remain healthy.
- Reference the remediation milestones in `.repo_studios/command_center/docs/phase_7/PLACEHOLDER_DEBT_PLAN.md` before approving new placeholders.

## Testing

`pytest .repo_studios/tests/tests_producers/test_scan_code_placeholders.py`

The suite validates structured artifact generation, summary counters, pruning behavior, and allowlist handling.

## Operational notes

- Placeholder detection is comment-oriented: only lines starting with common comment anchors (`#`, `//`, `<!--`, `/*`, `*`) are inspected, reducing false positives from string literals.
- When scanning the repo root, the producer omits `.venv/`, `node_modules/`, and intermediary `site-packages/` directories by default to avoid counting third-party artifacts. Provide explicit prefixes via `--exclude-prefix` to customize or bypass this behavior.
- Mixed-case markers (for example `Todo`, `Review`) are ignored by default; ensure placeholder annotations remain uppercase if they should be counted.
- CI integration plan (`placeholder-scan` stage) runs the producer in warning mode initially; jobs fail once `total_matches - allowlist_size > 0` or allowlist entries exceed governance caps. Weekly schedule fires Mondays at 12:00 UTC, with the kickoff run on 2025-11-23 logged in the CI rollout record. See `.repo_studios/command_center/docs/phase_7/PLACEHOLDER_DEBT_PLAN.md#ci-gating-proposal-draft-2025-11-23` for rollout details.
- Extend `_looks_like_comment` anchors if you introduce additional file types (e.g., SQL or shell scripts) that require different markers.
- For stricter filtering, enrich `_looks_like_comment` or wrap the producer with additional file-specific heuristics before consumption.
- Consider wiring a Make target (e.g., `studio-scan-code-placeholders`) and adding the producer to hygiene dashboards once baseline debt is tracked.
