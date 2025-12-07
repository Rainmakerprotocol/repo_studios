# Monkey Patch Scan Report

- Status: `ok`
- Timestamp: `2025-12-07T02:39:35.371864+00:00`
- Scan Root: `.`
- Files Scanned: 228
- Files With Findings: 66
- Total Findings: 130
- Parse Errors: 0

## Findings by Category

| Category | Count |
| --- | ---: |
| attribute_reassignment_on_import | 4 |
| global_env_mutation | 1 |
| setattr_on_import_or_class | 65 |
| sys_modules_assignment | 60 |

## Patched Import Bases

| Package | Count |
| --- | ---: |
| tomllib | 2 |
| fcntl | 1 |
| yaml | 1 |

## Files With Highest Patch Counts

| File | Count |
| --- | ---: |
| .repo_studios\tests\tests_command_center\dependency_import_hygiene\test_run_dependency_import_hygiene.py | 13 |
| .repo_studios\tests\tests_orchestrators\test_run_batch_cleanup.py | 13 |
| .repo_studios\tests\tests_orchestrators\test_run_standards_gap_suite.py | 11 |
| .repo_studios\tests\tests_command_center\orchestrators\test_run_test_execution_telemetry.py | 7 |
| .repo_studios\tests\tests_command_center\viewer\test_refresh.py | 5 |
| .repo_studios\tests\tests_orchestrators\test_run_pytest_log_capture.py | 5 |
| .repo_studios\tests\tests_utilities\test_refresh_mypy_baselines.py | 4 |
| .repo_studios\tests\tests_producers\test_generate_typecheck_report.py | 3 |
| .repo_studios\tests\tests_consumers\test_generate_anchor_health_report.py | 2 |
| .repo_studios\tests\tests_consumers\test_generate_fault_artifacts.py | 2 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
