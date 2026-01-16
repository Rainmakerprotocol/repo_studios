# Monkey-Patch Risk Summary

Generated (UTC): 2026-01-16T17:17:47+00:00

- Total Findings: 122

## Counts by Risk

- HIGH: 14
- MODERATE: 52
- SAFE: 56

## Top Files

- .repo_studios\tests\tests_command_center\orchestrators\test_run_monkey_patch_oversight.py: 10
- .repo_studios\tests\tests_command_center\orchestrators\test_run_test_execution_telemetry.py: 10
- .repo_studios\tests\tests_producers\test_scan_monkey_patches.py: 6
- .repo_studios\tests\tests_command_center\orchestrators\test_run_command_center_pipeline.py: 5
- .repo_studios\tests\tests_command_center\viewer\test_refresh.py: 5
- .repo_studios\tests\tests_producers\test_generate_test_coverage_inventory.py: 4
- .repo_studios\tests\tests_utilities\test_refresh_mypy_baselines.py: 4
- .repo_studios\tests\tests_producers\test_generate_typecheck_report.py: 3
- .repo_studios\tests\tests_command_center\dependency_import_hygiene\test_run_dependency_import_hygiene.py: 3
- .repo_studios\tests\tests_aggregators\test_generate_churn_complexity_heatmap.py: 2

## Top Categories

- sys_modules_assignment: 60
- setattr_on_import_or_class: 56
- attribute_reassignment_on_import: 3
- global_env_mutation: 2
- builtins_mutation: 1

## High-Risk Focus

- sys_modules_assignment: 14

## Source References

- Source Type: structured
- Scan Directory: `C:\Users\genet\repo_studios\.repo_studios\reports\healthview\producer_reports\monkey_patch_scans\20260116-1717`
- Consumer Bundle: `C:\Users\genet\repo_studios\.repo_studios\reports\healthview\consumer_reports\monkey_patch_risk\20260116-1717`
