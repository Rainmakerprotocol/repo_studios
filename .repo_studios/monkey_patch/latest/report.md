# Monkey Patch Scan Report

- Status: `ok`
- Timestamp: `2025-11-24T17:52:33.904521+00:00`
- Scan Root: `.`
- Files Scanned: 170
- Files With Findings: 41
- Total Findings: 56
- Parse Errors: 0

## Findings by Category

| Category | Count |
| --- | ---: |
| attribute_reassignment_on_import | 3 |
| global_env_mutation | 1 |
| setattr_on_import_or_class | 15 |
| sys_modules_assignment | 37 |

## Patched Import Bases

| Package | Count |
| --- | ---: |
| tomllib | 2 |
| fcntl | 1 |

## Files With Highest Patch Counts

| File | Count |
| --- | ---: |
| .repo_studios\tests\tests_command_center\viewer\test_refresh.py | 5 |
| .repo_studios\tests\tests_producers\test_generate_typecheck_report.py | 3 |
| .repo_studios\tests\tests_consumers\test_generate_anchor_health_report.py | 2 |
| .repo_studios\tests\tests_consumers\test_generate_fault_artifacts.py | 2 |
| .repo_studios\tests\tests_consumers\test_generate_test_log_health_report.py | 2 |
| .repo_studios\tests\tests_producers\test_generate_lizard_report.py | 2 |
| .repo_studios\tests\tests_producers\test_scan_monkey_patches.py | 2 |
| .repo_studios\tests\tests_producers\test_seed_standards_prompts.py | 2 |
| .repo_studios\tests\tests_producers\test_validate_import_boundaries.py | 2 |
| .repo_studios\tests\tests_producers\test_validate_metrics_anchor_stubs.py | 2 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
