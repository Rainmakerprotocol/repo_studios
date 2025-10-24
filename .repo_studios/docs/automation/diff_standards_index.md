# diff_standards_index.py

**Last updated:** 2025-10-22

## Purpose

`diff_standards_index.py` compares two standards index YAML snapshots (typically the baseline catalog and a regenerated proposal) and produces structured artifacts that highlight rule-level changes. Summaries classify per-rule deltas (added, removed, severity_changed, etc.) so downstream automation can gate merges or send notifications without reparsing YAML.

## Invocation

```bash
python .repo_studios/scripts/producers/diff_standards_index.py \
  legacy/repo_files/copilot_standards_index.yaml \
  .repo_studios/reports/producer_reports/standards_index_diff_reports/latest_report.json \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports/standards_index_diff_reports \
  --fail-on severity_changed,added,removed \
  --artifacts-to-keep 10
```

### Key arguments

- `old`, `new` (positional): paths to the baseline and candidate standards index YAML files. Relative paths resolve against `--repo-root`.
- `--repo-root` (default `.`): repository root used for resolving relative inputs and the default output directory.
- `--output-dir` (default `.repo_studios/reports/producer_reports/standards_index_diff_reports`): run directory parent; the script creates timestamped subfolders plus `latest_*` links.
- `--timestamp`: ISO-8601 timestamp to seed the run directory slug. When omitted the script snapshots current UTC.
- `--artifacts-to-keep` (default `10`): retention window applied after each run (minimum 1 retained run).
- `--fail-on` (default `any`): comma-separated list of change kinds that should flip the exit code to `1`. Accepts members of `{added, removed, severity_changed, rationale_changed, summary_changed, applies_changed, categories_changed, other_changed}`. Use `any` to fail on every change.
- `--json`: optional path to dump the raw diff object independent of the structured report payload.
- `--log-level` (default `INFO`): Python logging verbosity during execution.

Exit codes:

- `0` when no requested failure conditions are met.
- `1` when the diff contains change kinds covered by `--fail-on`.
- `2` when inputs are missing or cannot be parsed.

## Outputs

Each execution writes `.repo_studios/reports/producer_reports/standards_index_diff_reports/standards_index_diff-<timestamp>/` with:

- `report.json`: canonical payload (schema_version `1`) including `status`, `timestamp`, `generated_utc`, `repo_root`, `old_index`, `new_index`, `fail_policy`, `should_fail`, `change_count`, `summary`, `changes`, and integrity hash fields.
- `report.md`: human-readable summary with run parameters, a change summary table, the full change table, and a reproduction command snippet.
- `log.txt`: key/value digest (status, change_count, should_fail, fail_policy, index paths, integrity hashes, notes, summary entries).
- `raw.json`: full diff structure containing `summary`, `changes`, and integrity hash metadata.
- `raw.txt`: pretty-printed raw diff JSON (or notes) for quick inspection.

The output root maintains `latest_report.json`, `latest_report.md`, `latest_report.log`, `latest_raw.json`, and `latest_raw.txt` pointers to the most recent run. Historical run directories are pruned according to `--artifacts-to-keep` (minimum retention one run).

## Status semantics

- `changes`: at least one rule-level change detected.
- `no_changes`: the two indices match aside from tolerated keys (e.g., `last_updated`).
- `error`: inputs missing or unreadable; failure details land in `notes` and `raw.txt`.

The payload also records `should_fail` based on the configured fail policy; orchestrators typically use this flag to decide whether to halt a pipeline when high-severity change kinds appear.

## Testing

`pytest .repo_studios/tests/tests_producers/test_diff_standards_index.py` covers change detection, artifact serialization, pruning behaviour, and the failure policy wiring.

## Operational notes

- The diff tolerates metadata churn for keys listed in `TOLERATE_DIFF_KEYS` (currently `last_updated`) to reduce noise.
- When wiring into CI, prefer feeding the script the committed baseline index and a freshly generated candidate to ensure integrity hashes reflect actual content.
- Use the `--json` option when downstream tooling needs the raw diff but cannot locate the structured report directory.
