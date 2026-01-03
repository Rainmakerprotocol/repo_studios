# Monkey Patch Scan Report

- Status: `ok`
- Run timestamp (UTC): `20260103-0141`
- Scan Root: `.`
- Files Scanned: 233
- Files With Findings: 69
- Total Findings: 119
- Parse Errors: 0

## Findings by Category

| Category | Count |
| --- | ---: |
| attribute_reassignment_on_import | 3 |
| builtins_mutation | 1 |
| global_env_mutation | 2 |
| setattr_on_import_or_class | 53 |
| sys_modules_assignment | 60 |

## Patched Import Bases

| Package | Count |
| --- | ---: |
| tomllib | 2 |
| fcntl | 1 |
| sys | 1 |

## Files With Highest Patch Counts

| File | Count |
| --- | ---: |
| .repo_studios\tests\tests_command_center\orchestrators\test_run_monkey_patch_oversight.py | 10 |
| .repo_studios\tests\tests_command_center\orchestrators\test_run_test_execution_telemetry.py | 7 |
| .repo_studios\tests\tests_producers\test_scan_monkey_patches.py | 6 |
| .repo_studios\tests\tests_command_center\orchestrators\test_run_command_center_pipeline.py | 5 |
| .repo_studios\tests\tests_command_center\viewer\test_refresh.py | 5 |
| .repo_studios\tests\tests_producers\test_generate_test_coverage_inventory.py | 4 |
| .repo_studios\tests\tests_utilities\test_refresh_mypy_baselines.py | 4 |
| .repo_studios\tests\tests_command_center\dependency_import_hygiene\test_run_dependency_import_hygiene.py | 3 |
| .repo_studios\tests\tests_producers\test_generate_typecheck_report.py | 3 |
| .repo_studios\tests\tests_aggregators\test_generate_churn_complexity_heatmap.py | 2 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
