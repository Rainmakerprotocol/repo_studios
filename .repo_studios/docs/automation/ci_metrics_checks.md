# CI Metrics Checks for Inventory Reports

Last updated: 2025-10-18

This guide describes the proposed CI automation that consumes `.repo_studios/reports/<topic>/latest/` artifacts to guard Repo Studios health.

## Goals

- Fail early when inventory regressions (missing paths, unknown statuses) appear.
- Provide dashboards or summaries to maintainers without shipping a UI.
- Keep checks lightweight so they can run on every pull request.

## Proposed Pipeline Steps

1. **Generate Reports**
   - Run `python3 .repo_studios/scripts/render_inventory_views.py` to refresh the latest artifacts.
   - Cache the `.repo_studios/reports/` directory for downstream jobs.

2. **Validate Inventory**
   - Execute `make -C .repo_studios studio-validate-inventory`.
   - Treat any path-existence error or schema violation as a hard failure.

3. **Health Assertions**
   - Parse `.repo_studios/reports/summary/latest/summary.json` and fail if:
     - `by_status.unknown` > 0.
     - `by_asset_kind.document` drops below a configured floor (default: 20).
     - Any consumer count unexpectedly hits zero when previously tracked (configure allowlist).

4. **Change Detection**
   - Compare current summary against the main-branch baseline stored in `reports/summary/main_baseline.json` (to be generated after pipeline adoption).
   - Fail or warn when deltas exceed thresholds (for example, more than 5% drop in total assets).

5. **Reporting Output**
   - Publish the parsed metrics as job summary markdown for maintainers.
   - Optionally upload `dashboard.json` as a build artifact for downstream visualization.

## Implementation Notes

- Add a lightweight Python helper (`.repo_studios/scripts/check_inventory_health.py`) to evaluate thresholds and emit exit codes for CI.
- Store baseline thresholds under `.repo_studios/config/ci_inventory_thresholds.yaml` so adjustments do not require code edits.
- When new asset categories are introduced, update both the baseline file and thresholds.

## Next Actions

1. Extend thresholds or baseline when inventory scope grows (update `.repo_studios/config/ci_inventory_thresholds.json` and `reports/summary/main_baseline.json`).
2. Monitor CI results and adjust health check logic (`scripts/check_inventory_health.py`) as new metrics gain consumers.
