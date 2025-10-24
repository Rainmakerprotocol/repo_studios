# validate_metrics_anchor_stubs.py

**Last updated:** 2025-10-23

## Purpose

`validate_metrics_anchor_stubs.py` scans repository markdown for links into
`docs/api/metrics_orchestrator.md` and ensures each referenced anchor has a matching
legacy stub entry. The refactor emits structured artifacts (JSON/Markdown/log/missing
lists), manages pruning, and supports an anchor allowlist for transitional cases.

## Invocation

```bash
python .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py \
  --repo-root . \
  --artifacts-to-keep 5 \
  --log-level INFO
```

From `.repo_studios/`, run `make studio-validate-metrics-anchor-stubs` to execute with
repository defaults.

### Key arguments

- `--repo-root`: repository root used to resolve markdown files and legacy stub locations.
- `--output-dir`: override the artifact directory (defaults to
  `.repo_studios/reports/producer_reports/metrics_anchor_stub_reports`).
- `--legacy-file`: alternate path to the metrics orchestrator markdown file.
- `--allowlist-path`: JSON file containing `{"anchors": [...]}` for temporarily
  permitted missing anchors.
- `--artifacts-to-keep`: number of historical run directories retained after pruning
  (minimum 1, default 10).
- `--log-level`: logging verbosity (`INFO` default).

## Outputs

Each run creates `.repo_studios/reports/producer_reports/metrics_anchor_stub_reports/`
`metrics_anchor_stub_check-<timestamp>/` containing:

- `report.json`: canonical payload with inputs, summary counts, and missing anchor details.
- `report.md`: human-readable summary with tables for any uncovered anchors.
- `log.txt`: key-value diagnostics for CI ingestion.
- `missing.json`: compact list of missing anchors including referencing files.

The script also maintains `latest/` copies:

- `latest_report.json`
- `latest_report.md`
- `latest_log.txt`
- `latest_missing.json`

Historical run directories are pruned after each execution according to the
configured retention window.

## Diagnostics

- `summary.files_checked`: total markdown files scanned.
- `summary.anchors_referenced`: count of unique anchors encountered in links.
- `summary.missing_count`: anchors remaining after allowlist application.
- `summary.allowlisted_count`: anchors suppressed by the allowlist during the run.
- `missing[*]`: per-anchor records (name plus referencing files) for rapid remediation.

## Testing

`pytest .repo_studios/tests/tests_producers/test_validate_metrics_anchor_stubs.py`

The suite covers clean runs, missing anchor detection, allowlist handling, artifact
creation, and pruning when the retention window is constrained to a single run.

## Operational notes

- Ensure `docs/api/metrics_orchestrator.md` retains the "Legacy Anchor Compatibility"
  section structure; adjust `_normalize_anchor` if the anchor generation rules change.
- Document long-lived exceptions in the architecture log and track them in the
  allowlist JSON with justification.
- Downstream CI jobs should parse `report.json` to classify failures rather than relying
  on string matching in logs.
