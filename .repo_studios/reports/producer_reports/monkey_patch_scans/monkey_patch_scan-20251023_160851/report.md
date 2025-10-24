# Monkey Patch Scan Report

- Status: `ok`
- Timestamp: `2025-10-23T16:08:51.218994+00:00`
- Scan Root: `.`
- Files Scanned: 73
- Files With Findings: 19
- Total Findings: 29
- Parse Errors: 0

## Findings by Category

| Category | Count |
| --- | ---: |
| attribute_reassignment_on_import | 3 |
| global_env_mutation | 1 |
| setattr_on_import_or_class | 9 |
| sys_modules_assignment | 16 |

## Patched Import Bases

| Package | Count |
| --- | ---: |
| tomllib | 2 |
| fcntl | 1 |

## Files With Highest Patch Counts

| File | Count |
| --- | ---: |
| legacy\repo_tests\test_lizard_report.py | 5 |
| .repo_studios\tests\tests_producers\test_generate_typecheck_report.py | 3 |
| .repo_studios\tests\tests_producers\test_generate_lizard_report.py | 2 |
| .repo_studios\tests\tests_producers\test_scan_monkey_patches.py | 2 |
| legacy\repo_tests\test_typecheck_report.py | 2 |
| legacy\repo_tests\test_typecheck_report_fast_mode.py | 2 |
| .repo_studios\scripts\producers\generate_dependency_hygiene_report.py | 1 |
| .repo_studios\scripts\producers\generate_typecheck_report.py | 1 |
| .repo_studios\scripts\utilities\configure_faulthandler_runtime.py | 1 |
| .repo_studios\tests\tests_producers\test_analyze_standards_index_gaps.py | 1 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
