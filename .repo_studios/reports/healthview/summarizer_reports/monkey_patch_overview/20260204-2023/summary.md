# Monkey Patch Oversight Overview

Generated (UTC): 2026-02-04T20:23:27+00:00

## Portfolio Snapshot

- Total Findings: 122
- High Risk: 15
- Moderate Risk: 51
- Safe: 56
- Consumer Summary: `.repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/20260204-1902/summary.json`
- Trend JSON: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/20260204-1937/trend.json`

## Trend Signals

- Trend Markdown: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/20260204-1937/trend.md`
- Trend JSON: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/20260204-1937/trend.json`
- Delta Total: +0
- Delta HIGH/MODERATE/SAFE: +1 / -1 / +0
- Percent Total: +0.0%
- Changed: true
- Changed Levels: HIGH, MODERATE
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
| sys_modules_assignment | 61 |
| setattr_on_import_or_class | 56 |
| global_env_mutation | 2 |
| attribute_reassignment_on_import | 2 |
| builtins_mutation | 1 |

## Actions

- HIGH risk increased: open the trend markdown and review top HIGH files.
- Provide a duplicate matrix to enable overlap cross-checking (optional).

## Duplicate Follow-up

- Duplicate Matrix: unavailable
- Overlapping Monkey Patch Files: none detected
