# Legacy Orchestrator Cleanup Checklist

**Last updated:** 2025-12-10

## Purpose

Provide a single traceable checklist for retiring the legacy orchestration entry points once topic
orchestrators and the meta runner become the default. Use this document to coordinate doc updates,
Makefile changes, test rewrites, and CI/agent adjustments before removing legacy code.

## How to Use This Checklist

- Track each outstanding reference to the legacy runners listed below.
- Link verification evidence (commit hash, PR number, pytest command) in the "Verification" column
  as items are cleared.
- Keep this file with the orchestrator plan until Phase 8 decommissioning completes; archive it in
  the decision log afterward.

## Documentation References

| Item | Legacy Entry Point | Replacement Pointer | Verification |
| --- | --- | --- | --- |
| [ ] Update `docs/automation/run_fault_pipeline.md` to describe the Fault Diagnostics topic runner or archive the page. | `python .repo_studios/scripts/orchestrators/run_fault_pipeline.py` | `python .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` / `make -C .repo_studios studio-orchestrate-fault-diagnostics` | |
| [ ] Update `docs/automation/run_pytest_log_capture.md` with redirect guidance or retire the file. | `python .repo_studios/scripts/orchestrators/run_pytest_log_capture.py` | `python .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` / `make -C .repo_studios studio-orchestrate-test-execution-telemetry` | |
| [ ] Update `docs/automation/run_batch_cleanup.md` to reference Dependency & Import Hygiene orchestration and batch cleanup triggers. | `python .repo_studios/scripts/orchestrators/run_batch_cleanup.py` / `make studio-run-batch-cleanup` | `python .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py` / `make -C .repo_studios studio-orchestrate-dependency-import-hygiene --trigger-batch-cleanup` | |
| [ ] Update any README references under `.repo_studios/scripts/README.md` or related docs that still cite legacy orchestrators. | Mixed | Update to topic orchestrators and `orchestrate_full_diagnostic.py` | |
| [ ] Confirm `docs/automation/orchestrator_automation_hooks.md` no longer lists legacy shims after their removal. | Multiple | Topic orchestrator entries only | |

## Make Targets and CLI Shims

| Item | Legacy Surface | Replacement Surface | Verification |
| --- | --- | --- | --- |
| [ ] Remove `studio-run-fault-pipeline` alias from `.repo_studios/Makefile` once telemetry shows zero shim usage for two weeks. | `studio-run-fault-pipeline` | `studio-orchestrate-fault-diagnostics` | |
| [ ] Remove `studio-run-standards-gap-suite` alias from `.repo_studios/Makefile` after Standards Ops sign off. | `studio-run-standards-gap-suite` | `studio-orchestrate-standards` | |
| [ ] Verify no residual Make aliases reference `run_pytest_log_capture`, `run_batch_cleanup`, or `run_standards_index_cli`. | `.repo_studios/Makefile` | Topic/Meta orchestrator targets | |
| [ ] Delete shim modules (`run_fault_pipeline.py`, `run_pytest_log_capture.py`, `run_batch_cleanup.py`, `run_standards_gap_suite.py`, `run_standards_index_cli.py`, `orchestrate_health_suite.py`) once documentation and CI are clear. | `.repo_studios/scripts/orchestrators/*.py` | Command Center orchestrators and meta runner | |

## Tests and Fixtures

| Item | Legacy Test Suite | Replacement Coverage | Verification |
| --- | --- | --- | --- |
| [ ] Remove or rewrite `tests/tests_orchestrators/test_run_fault_pipeline.py` when the shim goes away. | Legacy orchestrator smoke tests | `tests/tests_command_center/fault_diagnostics/test_run_fault_diagnostics_overview.py` | |
| [ ] Remove or rewrite `tests/tests_orchestrators/test_run_pytest_log_capture.py` after shim deletion. | Pytest log capture legacy suite | `tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py` | |
| [ ] Remove or rewrite `tests/tests_orchestrators/test_run_batch_cleanup.py` once batch cleanup shim is retired. | Batch cleanup legacy suite | `tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py` | |
| [ ] Remove or rewrite `tests/tests_orchestrators/test_run_standards_gap_suite.py` after redirect sunset. | Standards gap legacy suite | `tests/tests_command_center/standards_integrity/test_run_standards_integrity.py` | |
| [ ] Remove or update `tests/tests_orchestrators/test_run_standards_index_cli.py` when the legacy CLI is removed. | Standards index CLI shim | Topic orchestrator CLI coverage | |

## CI, Automation, and Prompts

| Item | Legacy Reference | Replacement | Verification |
| --- | --- | --- | --- |
| [ ] Audit GitHub Actions workflows for `studio-run-*` or legacy script invocations. | `.github/workflows/**` | `studio-orchestrate-<topic>` / `studio-orchestrate-full-diagnostic` | |
| [ ] Confirm `repo_prompts.md` and command-center prompt bundles cite the migration announcement and omit deprecated commands after removal. | `repo_prompts.md`, `.repo_studios/command_center/docs/phase_6/**` | `docs/automation/orchestrator_migration_announcement.md`; topic targets | |
| [ ] Update agent onboarding or SOP documents referencing legacy bundles. | `.repo_studios/command_center/docs/**` | Healthview bundles & topic orchestrators | |

## Artifacts and Reports

| Item | Legacy Path | Replacement Path | Verification |
| --- | --- | --- | --- |
| [x] Remove legacy report directories (`.repo_studios/reports/orchestrator_runs/*`, `.repo_studios/reports/orchestrator_logs/*`) once topic bundles and Healthview mirrors are canonical. | Legacy `orchestrator_runs`, `orchestrator_logs` trees | `.repo_studios/command_center/reports/{commandview,healthview}/<topic>/<timestamp>/` | 2025-12-10: Removed legacy trees and added rawview placeholders for dependency hygiene cleanup + mypy baselines (see PR diff & pytest `tests/tests_utilities/test_refresh_mypy_baselines.py`). |
| [ ] Run `reports_naming_audit.py` to confirm no `latest_*` artifacts remain after deletions. | Various | Healthview/CommandView timestamped bundles only | |

## Tracking

- Update the verification column with commit hashes or PR links as cleanup tasks complete.
- File backlog tickets for any blockers uncovered during cleanup and reference them from this table.
- Archive this checklist alongside the governance evidence once Phase 8 closes.
