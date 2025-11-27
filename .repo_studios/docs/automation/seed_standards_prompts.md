# seed_standards_prompts.py

**Last updated:** 2025-11-27

## Purpose

`seed_standards_prompts.py` distills the standards index into compact prompt seeds for AI workflows. It selects critical, error, and optionally warn rules, groups them by category, and publishes structured bundles so downstream agents can ingest the data without re-parsing the full index. The refactor introduces structured artifacts, historical pruning, latest pointers, and compatibility with the legacy stdout/file interface.

## Invocation

```bash
python .repo_studios/scripts/producers/seed_standards_prompts.py \
  --repo-root . \
  --include-warn \
  --artifact-formats text yaml json \
  --artifacts-to-keep 10
```

From `.repo_studios/`, run `make studio-seed-standards-prompts` to execute the producer with repository defaults.

### Key arguments

- `--repo-root`: repository root used to resolve relative paths (defaults to four levels up from the script location).
- `--index-path`: override path to the canonical standards index (defaults to `.repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml`).
- `--output-dir`: destination for structured artifacts (defaults to `.repo_studios/reports/producer_reports/standards_prompt_seeds`).
- `--include-warn`: include warn-severity rules in the seed (default is critical + error only).
- `--artifact-formats`: formats persisted in the run bundle (`text`, `yaml`, `json`; default emits all three).
- `--format` / `--out`: retain legacy behavior by streaming a single format to stdout or writing it to a specific path.
- `--artifacts-to-keep`: count of historical runs preserved after pruning (minimum 1, default 10).
- `--log-level`: logging verbosity (`INFO` by default).

## Outputs

Each run creates `.repo_studios/reports/producer_reports/standards_prompt_seeds/standards_prompt_seed-<timestamp>/` with:

- `report.json`: structured payload containing configuration, severity counts, and category summaries.
- `report.md`: human-readable synopsis with next-step guidance.
- `log.txt`: key-value diagnostics suitable for CI parsing.
- `seed.txt`, `seed.yaml`, `seed.json`: serialized prompt seed in the requested artifact formats.

The script also refreshes `.repo_studios/reports/producer_reports/standards_prompt_seeds/latest/` with copies:

- `latest_report.json`
- `latest_report.md`
- `latest_log.txt`
- `latest_seed.txt`
- `latest_seed.yaml`
- `latest_seed.json`

Historical run directories are pruned to the configured retention window after each execution.

## Diagnostics

- `summary.category_count` captures how many standards categories contribute to the seed.
- `summary.total_rules` records the number of rules exported.
- `summary.severity_counts` surfaces coverage across critical, error, and warn levels.
- `summary.categories` lists each category id/title pair with its rule count for quick spot checks.

## Testing

`pytest .repo_studios/tests/tests_producers/test_seed_standards_prompts.py`

The suite validates artifact creation, seed contents, latest pointers, legacy output compatibility, and pruning behavior under a single-run retention window.

## Operational notes

- The script always emits the canonical JSON representation, even when the legacy `--format` is set to text or yaml for stdout/file consumers.
- Use `--artifact-formats` to trim the bundle (e.g., keep JSON-only for minimal storage) while still writing a specific legacy format via `--out` when needed.
- The seed mirrors the integrity hash from the standards index, enabling quick drift detection if the index changes between runs.
- When integrating into CI, gate on the structured `report.json` payload to detect unexpected rule count drops or missing categories.
