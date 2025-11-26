# Monkey-Patch Risk Summary

Generated (UTC): 2025-11-26T01:40:25+00:00

- Total Findings: 56

## Counts by Risk

- HIGH: 4
- MODERATE: 37
- SAFE: 15

## Top Files

- .repo_studios\tests\tests_command_center\viewer\test_refresh.py: 5
- .repo_studios\tests\tests_producers\test_generate_typecheck_report.py: 3
- .repo_studios\tests\tests_consumers\test_generate_anchor_health_report.py: 2
- .repo_studios\tests\tests_consumers\test_generate_fault_artifacts.py: 2
- .repo_studios\tests\tests_consumers\test_generate_test_log_health_report.py: 2
- .repo_studios\tests\tests_producers\test_generate_lizard_report.py: 2
- .repo_studios\tests\tests_producers\test_scan_monkey_patches.py: 2
- .repo_studios\tests\tests_producers\test_seed_standards_prompts.py: 2
- .repo_studios\tests\tests_producers\test_validate_import_boundaries.py: 2
- .repo_studios\tests\tests_producers\test_validate_metrics_anchor_stubs.py: 2

## Top Categories

- sys_modules_assignment: 37
- setattr_on_import_or_class: 15
- attribute_reassignment_on_import: 3
- global_env_mutation: 1

## High-Risk Focus

- sys_modules_assignment: 4

## Source References

- Source Type: structured
- Scan Directory: `C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\monkey_patch_scans\monkey_patch_scan-20251124_175233`
- Producer Report: `C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\monkey_patch_scans\monkey_patch_scan-20251124_175233\report.json`
- Consumer Bundle: `C:\Users\genet\repo_studios\.repo_studios\reports\consumer_reports\monkey_patch_risk\monkey_patch_risk-2025-11-26_014025`
