# Monkey-Patch Risk Summary

Generated (UTC): 2025-12-01T11:55:42+00:00

- Total Findings: 104

## Counts by Risk

- HIGH: 10
- MODERATE: 48
- SAFE: 46

## Top Files

- .repo_studios\tests\tests_orchestrators\test_run_batch_cleanup.py: 12
- .repo_studios\tests\tests_orchestrators\test_run_standards_gap_suite.py: 8
- .repo_studios\tests\tests_command_center\orchestrators\test_run_test_execution_telemetry.py: 7
- .repo_studios\tests\tests_command_center\viewer\test_refresh.py: 5
- .repo_studios\tests\tests_orchestrators\test_run_pytest_log_capture.py: 4
- .repo_studios\tests\tests_utilities\test_refresh_mypy_baselines.py: 4
- .repo_studios\tests\tests_producers\test_generate_typecheck_report.py: 3
- .repo_studios\tests\tests_consumers\test_generate_anchor_health_report.py: 2
- .repo_studios\tests\tests_consumers\test_generate_fault_artifacts.py: 2
- .repo_studios\tests\tests_consumers\test_generate_test_log_health_report.py: 2

## Top Categories

- sys_modules_assignment: 54
- setattr_on_import_or_class: 46
- attribute_reassignment_on_import: 3
- global_env_mutation: 1

## High-Risk Focus

- sys_modules_assignment: 10

## Source References

- Source Type: structured
- Scan Directory: `C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\monkey_patch_scans\monkey_patch_scan-20251201_115542`
- Producer Report: `C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\monkey_patch_scans\monkey_patch_scan-20251201_115542\report.json`
- Consumer Bundle: `C:\Users\genet\repo_studios\.repo_studios\reports\consumer_reports\monkey_patch_risk\monkey_patch_risk-2025-12-01_115542`
