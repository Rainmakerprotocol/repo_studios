# scan_code_placeholders.py

**Last updated:** 2025-10-23

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
  --artifacts-to-keep 10
```

From `.repo_studios/`, run `make studio-scan-code-placeholders` to execute the producer with repository defaults.

### Key arguments

- `--repo-root`: repository root used to resolve relative paths (defaults to three levels up from the script).
- `--root`: directory to scan. Accepts relative paths (resolved against `--repo-root`) or absolute paths. Defaults to the repo root.
- `--output-dir`: override for the artifact directory (defaults to `.repo_studios/reports/producer_reports/code_placeholder_scans`).
- `--include-ext`: list of file extensions to include. Defaults to `.py`, `.md`, `.txt`, `.js`, `.ts`, `.yaml`, `.yml`, `.json`.
- `--patterns`: tokens to detect. Defaults to `TODO`, `FIXME`, `NOTE`, `XXX`, `OPTIMIZE`, `REVIEW`.
- `--allowlist-file`: optional file containing `<path>:<line>` entries (paths relative to repo root) that should be ignored.
- `--artifacts-to-keep`: number of historical runs to retain (default `10`).
- `--log-level`: standard Python logging level (default `INFO`).

The script auto-creates output directories and normalizes extensions/patterns for case-insensitive matching.

## Outputs

Each run creates `.repo_studios/reports/producer_reports/code_placeholder_scans/placeholder_scan-<timestamp>/` with:

- `report.json`: summary payload with schema version, timestamp, patterns, counts by pattern/extension, allowlist stats, and total matches.
- `report.md`: human-readable summary and sample findings (top 20 entries).
- `log.txt`: key-value digest for CI consumption.
- `matches.json`: full list of findings (path, line, pattern, snippet).
- `matches.tsv`: tab-separated export (only written when matches exist).

The producer also refreshes `.repo_studios/reports/producer_reports/code_placeholder_scans/latest/` with copies of the most recent artifacts:

- `latest_report.json`
- `latest_report.md`
- `latest_log.txt`
- `latest_matches.json`
- `latest_matches.tsv` (when applicable)

Historical runs are pruned to the configured retention window after each execution.

## Diagnostics

- `allowlist_size` surfaces how many entries were ignored.
- `summary.by_pattern` and `summary.by_extension` help rank debt sources and languages.
- Empty runs still emit artifacts with `status: ok` and `total_matches: 0`, allowing CI to treat absence of placeholders as a success.

## Allowlist format

Allowlist files accept comment lines (prefixed with `#`) and entries formatted as `relative/path.py:42`. The scan ignores malformed lines. Provide paths relative to the repo root to keep entries stable across machines.

## Testing

`pytest .repo_studios/tests/tests_producers/test_scan_code_placeholders.py`

The suite validates structured artifact generation, summary counters, pruning behavior, and allowlist handling.

## Operational notes

- Placeholder detection is comment-oriented: only lines starting with common comment anchors (`#`, `//`, `<!--`, `/*`, `*`) are inspected, reducing false positives from string literals.
- Extend `_looks_like_comment` anchors if you introduce additional file types (e.g., SQL or shell scripts) that require different markers.
- For stricter filtering, enrich `_looks_like_comment` or wrap the producer with additional file-specific heuristics before consumption.
- Consider wiring a Make target (e.g., `studio-scan-code-placeholders`) and adding the producer to hygiene dashboards once baseline debt is tracked.
