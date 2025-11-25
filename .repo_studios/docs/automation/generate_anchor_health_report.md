# generate_anchor_health_report

## Purpose

- Produce a prioritized view of cross-file H1/H2 anchor collisions for documentation maintainers.
- Compare current duplicate counts against the committed baseline to highlight regressions.
- Emit operator-friendly artifacts (JSON, Markdown, TSV) while keeping history trimmed for easy review.

## Inputs

- Latest anchor inventory bundle
  (`.repo_studios/reports/producer_reports/anchor_inventory_reports/latest_report.json`)
  when present.
- Fallback Markdown scan of `docs/` when inventory artifacts are unavailable.
- Baseline file `tests/docs/anchor_slug_baseline.json` for regression deltas.

## Outputs

- Timestamped run directory under
  `.repo_studios/reports/consumer_reports/anchor_health_reports/` containing `anchor_report.json`,
  `anchor_report.md`, and `clusters.tsv`.
- Hard-linked pointers in the same directory: `anchor_report_latest.json`, `anchor_report_latest.md`,
  `clusters_latest.tsv`.
- `runs.log` entry with timestamped duplicate counts.
- Database integration placeholder in the JSON payload (`outputs.database`) for future sink wiring.

## Operation Notes

- Default retention keeps the latest five runs (`--artifacts-to-keep`).
- Honors `--inventory-report`, `--output-dir`, and `--log-level` for ad-hoc executions.
- Returns zero exit code even when duplicates remain; downstream policy determines enforcement.

## Usage Example

```shell
python -m .repo_studios.scripts.consumers.generate_anchor_health_report \
  --inventory-report .repo_studios/reports/producer_reports/anchor_inventory_reports/latest_report.json \
  --output-dir .repo_studios/reports/consumer_reports/anchor_health_reports \
  --artifacts-to-keep 5
```

## Testing

- `pytest .repo_studios/tests/tests_consumers/test_generate_anchor_health_report.py`

## Integration Checklist

- Run `generate_anchor_inventory.py` before this consumer to ensure fresh data.
- Review `generate_doc_index.py` output for owner metadata when planning follow-up edits.
- Attach rendered Markdown to remediation briefs for editor sign-off.
