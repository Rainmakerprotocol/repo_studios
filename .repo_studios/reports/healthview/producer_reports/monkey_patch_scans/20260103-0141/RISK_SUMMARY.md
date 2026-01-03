# Monkey-Patch Risk Summary

- Total Findings: 119

## Counts by Risk

- HIGH: 14
- MODERATE: 52
- SAFE: 53

## Top Files

- .repo_studios\tests\tests_command_center\orchestrators\test_run_monkey_patch_oversight.py: 10
- .repo_studios\tests\tests_command_center\orchestrators\test_run_test_execution_telemetry.py: 7
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
- setattr_on_import_or_class: 53
- attribute_reassignment_on_import: 3
- global_env_mutation: 2
- builtins_mutation: 1

## High-Risk Focus

- sys_modules_assignment: 14
