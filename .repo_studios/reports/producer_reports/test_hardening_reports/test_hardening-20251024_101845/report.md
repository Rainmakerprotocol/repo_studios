# Test Hardening Report

* Status: **issues-found**
* Timestamp: 2025-10-24T10:18:45.934739+00:00
* Test files analyzed: 13
* Test functions: 32
* Total issues: 12
* High severity issues: 5
* High-priority files: 4
* Clean files: 4

## Top Priority Files

### `que_for_integration/refactor_library/phase_3/test_create_latest_link.py`

* Priority score: 20
* Issues by severity: high=2, medium=0, low=0
* Key findings:
  * [HIGH] Test 'test_raises_error_on_missing_source' has no assertions. (line 73)
  * [HIGH] Test 'test_raises_error_on_directory_source' has no assertions. (line 81)

### `legacy/repo_tests/test_lizard_report.py`

* Priority score: 13
* Issues by severity: high=1, medium=1, low=0
* Key findings:
  * [HIGH] Test 'test_lizard_report_records_offenders' is 63 lines long. Consider decomposing. (line 25)
  * [MEDIUM] Test 'test_lizard_report_handles_missing_module' is 34 lines. Consider splitting for clarity. (line 90)
* Long tests:
  * `test_lizard_report_records_offenders` — 63 lines (starts at 25)

### `legacy/repo_tests/test_health_suite_summary.py`

* Priority score: 10
* Issues by severity: high=1, medium=0, low=0
* Key findings:
  * [HIGH] Test 'test_summary_includes_typecheck_section' is 54 lines long. Consider decomposing. (line 7)
* Long tests:
  * `test_summary_includes_typecheck_section` — 54 lines (starts at 7)

### `legacy/repo_tests/test_typecheck_report_fast_mode.py`

* Priority score: 10
* Issues by severity: high=1, medium=0, low=0
* Key findings:
  * [HIGH] Test 'test_fast_mode_curates_targets' is 56 lines long. Consider decomposing. (line 18)
* Long tests:
  * `test_fast_mode_curates_targets` — 56 lines (starts at 18)

### `legacy/repo_tests/test_health_suite_orchestrator.py`

* Priority score: 3
* Issues by severity: high=0, medium=1, low=0
* Key findings:
  * [MEDIUM] Test 'test_orchestrator_includes_typecheck_step' is 39 lines. Consider splitting for clarity. (line 7)

### `legacy/repo_tests/test_pytest_log_runner_paths.py`

* Priority score: 3
* Issues by severity: high=0, medium=1, low=0
* Key findings:
  * [MEDIUM] Test 'test_logs_dir_defaults_to_workspace_root' is 35 lines. Consider splitting for clarity. (line 15)

### `legacy/repo_tests/test_test_log_health_report_pick_best.py`

* Priority score: 3
* Issues by severity: high=0, medium=1, low=0
* Key findings:
  * [MEDIUM] Test 'test_pick_best_junit_prefers_multi_test_over_internal' is 36 lines. Consider splitting for clarity. (line 20)

### `legacy/repo_tests/test_typecheck_report.py`

* Priority score: 3
* Issues by severity: high=0, medium=1, low=0
* Key findings:
  * [MEDIUM] Test 'test_typecheck_report_with_mocked_mypy_output' is 48 lines. Consider splitting for clarity. (line 20)

### `que_for_integration/test_analyzer_concept/test_analyzer.py`

* Priority score: 2
* Issues by severity: high=0, medium=0, low=2

## Clean Files

* `legacy/repo_tests/test_fault_aggregate_and_gate.py` (0 tests)
* `legacy/repo_tests/test_generate_fault_artifacts.py` (0 tests)
* `legacy/repo_tests/test_pytest_log_runner.py` (0 tests)
* `que_for_integration/refactor_library/phase_2/test_scan_code_duplicates.py` (13 tests)

## Recommendations

1. Address high severity issues before medium/low findings.
2. Decompose long tests into focused units.
3. Mock external dependencies and remove global state.
4. Replace time.sleep() with deterministic waits.
5. Use descriptive names following given-when-then style.
