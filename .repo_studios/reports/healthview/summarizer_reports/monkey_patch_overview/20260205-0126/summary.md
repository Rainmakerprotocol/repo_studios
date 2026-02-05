# Monkey Patch Oversight Overview

Generated (UTC): 2026-02-05T01:26:34+00:00

## Portfolio Snapshot

- Total Findings: 10
- High Risk: 10
- Moderate Risk: 0
- Safe: 0
- Consumer Summary: `.repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/20260205-0126/summary.json`
- Trend JSON: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/20260205-0126/trend.json`

## Trend Signals

- Trend Markdown: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/20260205-0126/trend.md`
- Trend JSON: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/20260205-0126/trend.json`
- Delta Total: -112
- Delta HIGH/MODERATE/SAFE: -5 / -51 / -56
- Percent Total: -91.8%
- Changed: true
- Changed Levels: HIGH, MODERATE, SAFE
- Rolling(3) Total Avg: 84.67

## Top Drivers

### Top Files

| File | Findings |
|---|---:|
| .repo_studios\command_center\scripts\aggregators\scan_duplicates.py | 1 |
| .repo_studios\command_center\scripts\orchestrators\run_automation_dry_run.py | 1 |
| .repo_studios\command_center\scripts\orchestrators\run_available_scripts_oversight.py | 1 |
| .repo_studios\command_center\scripts\orchestrators\run_command_center_pipeline.py | 1 |
| .repo_studios\command_center\scripts\orchestrators\run_dependency_import_hygiene.py | 1 |

### Top Categories

| Category | Findings |
|---|---:|
| sys_modules_assignment | 10 |

## Actions

- Risk profile changed: review deltas and reconcile drivers listed above.
- Provide a duplicate matrix to enable overlap cross-checking (optional).

## Duplicate Follow-up

- Duplicate Matrix: unavailable
- Overlapping Monkey Patch Files: none detected
