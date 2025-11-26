# classify_monkey_patches.py

**Last updated:** 2025-11-25

## Purpose

`classify_monkey_patches.py` ingests monkey-patch scan artifacts and assigns
HIGH/MODERATE/SAFE risk tiers so teams can triage the most dangerous runtime
modifications first. The consumer prefers structured bundles from
`scan_monkey_patches.py` (`matches.json` + `report.json`) and mirrors legacy
`RISK_SUMMARY.*` files for downstream compatibility while emitting refreshed
consumer bundles under
`.repo_studios/reports/consumer_reports/monkey_patch_risk/`.

Risk rules align with `docs/standards/global/std-global-monkey-patching.md`:

- High: import-time side effects, `sys.modules` rewrites, builtin/singleton
  mutations, and module-scope global environment changes outside tests.
- Moderate: production import overrides (`attribute_reassignment_on_import`,
  `setattr_on_import_or_class`), module-scope test patch misuse, and
  test-contained global environment mutations.
- Safe: test-scoped overrides that cleanly restore state plus uncategorised
  findings that still warrant reporting.

## Invocation

```bash
python .repo_studios/scripts/consumers/classify_monkey_patches.py \
  --base-dir .repo_studios/reports/producer_reports/monkey_patch_scans \
  --output-base .repo_studios/reports/consumer_reports/monkey_patch_risk \
  --artifacts-to-keep 10 \
  --log-level INFO
```

Run `make studio-classify-monkey-patches` if a Make target is registered, or
call the consumer directly after `scan_monkey_patches.py` completes.

### Key arguments

- `--scan-dir`: Explicit producer run directory; when omitted, the newest
  structured scan is selected automatically.
- `--base-dir`: Directory that holds timestamped scan runs (defaults to the
  structured producer output path).
- `--output-base`: Destination for consumer bundles, including
  `summary.json`, `SUMMARY.md`, and `bundle_summary.json` plus `latest_*`
  links for orchestrators.
- `--artifacts-to-keep`: Number of historical consumer bundles retained after
  pruning (minimum 1, default 10).
- `--log-level` / `--verbose`: Logging controls shared across the structured
  pipeline.

## Outputs

Each execution creates
`.repo_studios/reports/consumer_reports/monkey_patch_risk/monkey_patch_risk-<timestamp>/`
containing:

- `summary.json`: Canonical payload with counts by risk, top files, top
  categories, and a high-risk category focus block.
- `SUMMARY.md`: Human-readable summary including source references and a
  high-risk section for quick operator review.
- `bundle_summary.json`: Provenance metadata describing the producer source,
  bundle paths, and run configuration.

The consumer also updates `latest_summary.json`, `latest_SUMMARY.md`, and
`latest_bundle_summary.json` hard links (falling back to copies when the
filesystem does not support hard links). Legacy `RISK_SUMMARY.*` files are
mirrored into the originating scan directory for backwards compatibility.

## Testing

`pytest .repo_studios/tests/tests_consumers/test_classify_monkey_patches.py`

## Operational Notes

- Ensure `scan_monkey_patches.py` completes successfully before invoking the
  consumer so `matches.json` is present; the legacy fallback remains available
  for transitional runs but no longer drives trend analysis.
- Aggregator workflows (`analyze_monkey_patch_trends.py`) reuse the same
  shared risk helper, so classification changes should be validated end-to-end
  by rerunning both consumer and aggregator suites.
- Use the generated high-risk focus section to drive patch-removal sprints and
  keep the governance ledger current.
