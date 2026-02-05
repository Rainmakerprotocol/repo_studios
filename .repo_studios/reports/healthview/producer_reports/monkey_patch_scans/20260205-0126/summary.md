# Monkey Patch Scan Report

- Status: `ok`
- Run timestamp (UTC): `20260205-0126`
- Scan Root: `.repo_studios\command_center\scripts`
- Files Scanned: 25
- Files With Findings: 10
- Total Findings: 10
- Findings (non-test): 10
- Findings (tests): 0
- Module-scope findings (non-test): 10
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
| sys_modules_assignment | 10 |

## Findings by Category (Non-Test)

| Category | Count |
| --- | ---: |
| sys_modules_assignment | 10 |

## Files With Highest Patch Counts

- Full file paths live in `manifest.json` under `payload.summary.top_files`.

| File | Count |
| --- | ---: |
| .repo_studios/command_center/scripts/aggregators/scan_duplicates.py | 1 |
| .repo_studios/command_center/script…hestrators/run_automation_dry_run.py | 1 |
| .repo_studios/command_center/script…s/run_available_scripts_oversight.py | 1 |
| .repo_studios/command_center/script…ators/run_command_center_pipeline.py | 1 |
| .repo_studios/command_center/script…ors/run_dependency_import_hygiene.py | 1 |
| .repo_studios/command_center/script…strators/run_docs_health_overview.py | 1 |
| .repo_studios/command_center/script…rs/run_fault_diagnostics_overview.py | 1 |
| .repo_studios/command_center/script…rators/run_monkey_patch_oversight.py | 1 |
| .repo_studios/command_center/script…estrators/run_standards_integrity.py | 1 |
| .repo_studios/command_center/script…tors/run_test_execution_telemetry.py | 1 |

## Top Non-Test Files

- Full file paths live in `manifest.json` under `payload.summary.top_files_non_test`.

| File | Count |
| --- | ---: |
| .repo_studios/command_center/scripts/aggregators/scan_duplicates.py | 1 |
| .repo_studios/command_center/script…hestrators/run_automation_dry_run.py | 1 |
| .repo_studios/command_center/script…s/run_available_scripts_oversight.py | 1 |
| .repo_studios/command_center/script…ators/run_command_center_pipeline.py | 1 |
| .repo_studios/command_center/script…ors/run_dependency_import_hygiene.py | 1 |
| .repo_studios/command_center/script…strators/run_docs_health_overview.py | 1 |
| .repo_studios/command_center/script…rs/run_fault_diagnostics_overview.py | 1 |
| .repo_studios/command_center/script…rators/run_monkey_patch_oversight.py | 1 |
| .repo_studios/command_center/script…estrators/run_standards_integrity.py | 1 |
| .repo_studios/command_center/script…tors/run_test_execution_telemetry.py | 1 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
