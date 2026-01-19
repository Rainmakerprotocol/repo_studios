# Monkey Patch Oversight Overview

Generated (UTC): 2026-01-17T12:10:49+00:00

## Portfolio Snapshot

- Total Findings: 122
- High Risk: 14
- Moderate Risk: 52
- Safe: 56
- Consumer Summary: `.repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/20260117-1210/summary.json`
- Trend JSON: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/20260117-1210/trend.json`

## Trend Signals

- Trend Markdown: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/20260117-1210/trend.md`
- Trend JSON: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/20260117-1210/trend.json`
- Delta Total: +0
- Delta HIGH/MODERATE/SAFE: +0 / +0 / +0
- Percent Total: +0.0%
- Changed: false
- Changed Levels: none
- Rolling(3) Total Avg: 122.00

## Top Drivers

### Top Files

| File | Findings |
|---|---:|
| .repo_studios\tests\tests_command_center\orchestrators\test_run_monkey_patch_oversight.py | 10 |
| .repo_studios\tests\tests_command_center\orchestrators\test_run_test_execution_telemetry.py | 10 |
| .repo_studios\tests\tests_producers\test_scan_monkey_patches.py | 6 |
| .repo_studios\tests\tests_command_center\orchestrators\test_run_command_center_pipeline.py | 5 |
| .repo_studios\tests\tests_command_center\viewer\test_refresh.py | 5 |

### Top Categories

| Category | Findings |
|---|---:|
| sys_modules_assignment | 60 |
| setattr_on_import_or_class | 56 |
| attribute_reassignment_on_import | 3 |
| global_env_mutation | 2 |
| builtins_mutation | 1 |

## Actions

- No risk deltas detected: spot-check HIGH findings and monitor trend.
- Provide a duplicate matrix to enable overlap cross-checking (optional).

## Duplicate Follow-up

- Duplicate Matrix: unavailable
- Overlapping Monkey Patch Files: none detected
