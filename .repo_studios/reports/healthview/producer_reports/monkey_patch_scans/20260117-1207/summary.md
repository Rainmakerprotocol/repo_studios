# Monkey Patch Scan Report

- Status: `ok`
- Run timestamp (UTC): `20260117-1207`
- Scan Root: `.`
- Files Scanned: 234
- Files With Findings: 69
- Total Findings: 122
- Findings (non-test): 17
- Findings (tests): 105
- Module-scope findings (non-test): 17
- Parse Errors: 0
- Retention (keep): 5

## Artifacts

- `manifest.json` (full findings + inputs)
- `telemetry.json` (thin metrics for dashboards)
- `summary.md` (this file)

## Risk Highlights

- Focus first on non-test module-scope findings and `sys_modules_assignment` outside tests.
- Test-only patches are often acceptable when scoped and justified.

## Findings by Category

| Category | Count |
| --- | ---: |
| attribute_reassignment_on_import | 3 |
| builtins_mutation | 1 |
| global_env_mutation | 2 |
| setattr_on_import_or_class | 56 |
| sys_modules_assignment | 60 |

## Findings by Category (Non-Test)

| Category | Count |
| --- | ---: |
| attribute_reassignment_on_import | 3 |
| sys_modules_assignment | 14 |

## Findings by Category (Tests)

| Category | Count |
| --- | ---: |
| builtins_mutation | 1 |
| global_env_mutation | 2 |
| setattr_on_import_or_class | 56 |
| sys_modules_assignment | 46 |

## Patched Import Bases

| Package | Count |
| --- | ---: |
| tomllib | 2 |
| fcntl | 1 |
| sys | 1 |

## Files With Highest Patch Counts

- Full file paths live in `manifest.json` under `payload.summary.top_files`.

| File | Count |
| --- | ---: |
| .repo_studios/tests/tests_command_c…s/test_run_monkey_patch_oversight.py | 10 |
| .repo_studios/tests/tests_command_c…test_run_test_execution_telemetry.py | 10 |
| .repo_studios/tests/tests_producers/test_scan_monkey_patches.py | 6 |
| .repo_studios/tests/tests_command_c…/test_run_command_center_pipeline.py | 5 |
| .repo_studios/tests/tests_command_center/viewer/test_refresh.py | 5 |
| .repo_studios/tests/tests_producers…_generate_test_coverage_inventory.py | 4 |
| .repo_studios/tests/tests_utilities/test_refresh_mypy_baselines.py | 4 |
| .repo_studios/tests/tests_command_c…est_run_dependency_import_hygiene.py | 3 |
| .repo_studios/tests/tests_producers/test_generate_typecheck_report.py | 3 |
| .repo_studios/tests/tests_aggregato…generate_churn_complexity_heatmap.py | 2 |

## Top Non-Test Files

- Full file paths live in `manifest.json` under `payload.summary.top_files_non_test`.

| File | Count |
| --- | ---: |
| .repo_studios/command_center/scripts/aggregators/scan_duplicates.py | 1 |
| .repo_studios/command_center/script…hestrators/run_automation_dry_run.py | 1 |
| .repo_studios/command_center/script…ators/run_command_center_pipeline.py | 1 |
| .repo_studios/command_center/script…ors/run_dependency_import_hygiene.py | 1 |
| .repo_studios/command_center/script…strators/run_docs_health_overview.py | 1 |
| .repo_studios/command_center/script…rs/run_fault_diagnostics_overview.py | 1 |
| .repo_studios/command_center/script…rators/run_monkey_patch_oversight.py | 1 |
| .repo_studios/command_center/script…estrators/run_standards_integrity.py | 1 |
| .repo_studios/command_center/script…tors/run_test_execution_telemetry.py | 1 |
| .repo_studios/docs/pipeline/checkbox_report/test_checkbox_report.py | 1 |

## Top Test Files

- Full file paths live in `manifest.json` under `payload.summary.top_files_test`.

| File | Count |
| --- | ---: |
| .repo_studios/tests/tests_command_c…s/test_run_monkey_patch_oversight.py | 10 |
| .repo_studios/tests/tests_command_c…test_run_test_execution_telemetry.py | 10 |
| .repo_studios/tests/tests_producers/test_scan_monkey_patches.py | 6 |
| .repo_studios/tests/tests_command_c…/test_run_command_center_pipeline.py | 5 |
| .repo_studios/tests/tests_command_center/viewer/test_refresh.py | 5 |
| .repo_studios/tests/tests_producers…_generate_test_coverage_inventory.py | 4 |
| .repo_studios/tests/tests_utilities/test_refresh_mypy_baselines.py | 4 |
| .repo_studios/tests/tests_command_c…est_run_dependency_import_hygiene.py | 3 |
| .repo_studios/tests/tests_producers/test_generate_typecheck_report.py | 3 |
| .repo_studios/tests/tests_aggregato…generate_churn_complexity_heatmap.py | 2 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
