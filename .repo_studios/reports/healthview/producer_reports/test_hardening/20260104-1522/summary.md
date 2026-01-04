# Test Hardening Report

- Status: **issues-found**
- Timestamp: 2026-01-04T15:22:58.302725+00:00
- Test files analyzed: 146
- Test functions: 547
- Total issues: 287
- High severity issues: 188
- High-priority files: 110
- Clean files: 19

## Top Priority Files

### `.repo_studios/tests/tests_library_integration/libraries/test_report_paths.py`

- Priority score: 68
- Issues by severity: high=5, medium=6, low=0
- Key findings:
  - [HIGH] Test 'test_invalid_class_raises_value_error' has no assertions. (line 128)
  - [HIGH] Test 'test_empty_topic_raises_value_error' has no assertions. (line 165)
  - [HIGH] Test 'test_none_topic_raises_value_error' has no assertions. (line 170)
  - [HIGH] Test 'test_invalid_tier_class_propagates_error' has no assertions. (line 175)
  - [HIGH] Test 'test_unknown_path_raises_value_error' has no assertions. (line 274)

### `.repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`

- Priority score: 63
- Issues by severity: high=6, medium=1, low=0
- Key findings:
  - [HIGH] Test 'test_parse_timestamp_invalid_raises' has no assertions. (line 43)
  - [HIGH] Test 'test_load_run_callable_errors_when_missing_run' has no assertions. (line 92)
  - [HIGH] Test 'test_execute_coverage_finds_run_dir' is 58 lines long. Consider decomposing. (line 113)
  - [HIGH] Test 'test_execute_hardening_passes_tests_dir' is 58 lines long. Consider decomposing. (line 173)
  - [MEDIUM] Test 'test_section_coverage_prefers_telemetry_metrics_even_when_zero' is 35 lines. Consider splitting for clarity. (line 258)
- Long tests:
  - `test_execute_coverage_finds_run_dir` — 58 lines (starts at 113)
  - `test_execute_hardening_passes_tests_dir` — 58 lines (starts at 173)
  - `test_run_generates_healthview_bundle` — 235 lines (starts at 295)

### `.repo_studios/tests/tests_producers/test_generate_function_inventory.py`

- Priority score: 55
- Issues by severity: high=4, medium=5, low=0
- Key findings:
  - [HIGH] Test 'test_inventory_generates_structured_output' is 106 lines long. Consider decomposing. (line 64)
  - [HIGH] Test 'test_inventory_merges_coverage_reports' is 62 lines long. Consider decomposing. (line 172)
  - [MEDIUM] Test 'test_inventory_includes_git_churn_summary' is 42 lines. Consider splitting for clarity. (line 236)
  - [MEDIUM] Test 'test_inventory_removes_preexisting_outputs' is 45 lines. Consider splitting for clarity. (line 322)
  - [MEDIUM] Test 'test_screening_score_history_accumulates_across_runs' is 45 lines. Consider splitting for clarity. (line 369)
- Long tests:
  - `test_inventory_generates_structured_output` — 106 lines (starts at 64)
  - `test_inventory_merges_coverage_reports` — 62 lines (starts at 172)
  - `test_call_graph_resolves_local_and_imported_calls` — 90 lines (starts at 416)

### `.repo_studios/tests/tests_producers/test_generate_test_coverage_inventory.py`

- Priority score: 50
- Issues by severity: high=5, medium=0, low=0
- Key findings:
  - [HIGH] Test 'test_generates_structured_artifacts' is 74 lines long. Consider decomposing. (line 52)
  - [HIGH] Test 'test_threshold_enforcement_and_pruning' is 62 lines long. Consider decomposing. (line 128)
  - [HIGH] Test 'test_refresh_coverage_xml_continue_on_error_emits_bundle' is 116 lines long. Consider decomposing. (line 213)
  - [HIGH] Test 'test_refresh_coverage_xml_without_continue_on_error_exits_nonzero' is 58 lines long. Consider decomposing. (line 331)
  - [HIGH] Test 'test_refresh_omit_tests_creates_and_removes_cov_config' is 93 lines long. Consider decomposing. (line 391)
- Long tests:
  - `test_generates_structured_artifacts` — 74 lines (starts at 52)
  - `test_threshold_enforcement_and_pruning` — 62 lines (starts at 128)
  - `test_refresh_coverage_xml_continue_on_error_emits_bundle` — 116 lines (starts at 213)

### `.repo_studios/tests/tests_producers/test_scan_monkey_patches.py`

- Priority score: 43
- Issues by severity: high=4, medium=1, low=0
- Key findings:
  - [HIGH] Test 'test_structured_artifacts' is 77 lines long. Consider decomposing. (line 14)
  - [MEDIUM] Test 'test_prune_history' is 47 lines. Consider splitting for clarity. (line 93)
  - [HIGH] Test 'test_scan_file_detects_multiple_categories_and_git_blame' is 81 lines long. Consider decomposing. (line 153)
  - [HIGH] Test 'test_scan_file_strict_mode_raises_on_parse_error' has no assertions. (line 236)
  - [HIGH] Test 'test_compose_manifest_telemetry_and_summary_round_trip' is 56 lines long. Consider decomposing. (line 256)
- Long tests:
  - `test_structured_artifacts` — 77 lines (starts at 14)
  - `test_scan_file_detects_multiple_categories_and_git_blame` — 81 lines (starts at 153)
  - `test_compose_manifest_telemetry_and_summary_round_trip` — 56 lines (starts at 256)

### `.repo_studios/tests/tests_command_center/viewer/test_layer_architecture_data_normalization.py`

- Priority score: 40
- Issues by severity: high=4, medium=0, low=0
- Key findings:
  - [HIGH] Test 'test_create_module_record_classifies_script_layers' is 67 lines long. Consider decomposing. (line 38)
  - [HIGH] Test 'test_evaluate_layer_transition_applies_adjacency_defaults' is 73 lines long. Consider decomposing. (line 107)
  - [HIGH] Test 'test_layer_architecture_validation_view_surfaces_violations' is 175 lines long. Consider decomposing. (line 182)
  - [HIGH] Test 'test_layer_architecture_validation_view_falls_back_to_repository_scope' is 105 lines long. Consider decomposing. (line 359)
- Long tests:
  - `test_create_module_record_classifies_script_layers` — 67 lines (starts at 38)
  - `test_evaluate_layer_transition_applies_adjacency_defaults` — 73 lines (starts at 107)
  - `test_layer_architecture_validation_view_surfaces_violations` — 175 lines (starts at 182)

### `.repo_studios/tests/tests_producers/test_generate_standards_index.py`

- Priority score: 40
- Issues by severity: high=4, medium=0, low=0
- Key findings:
  - [HIGH] Test 'test_structured_artifacts_success' is 91 lines long. Consider decomposing. (line 29)
  - [HIGH] Test 'test_failure_path_writes_artifacts_and_prunes' is 51 lines long. Consider decomposing. (line 122)
  - [HIGH] Test 'test_missing_source_file_reports_error' is 69 lines long. Consider decomposing. (line 175)
  - [HIGH] Test 'test_extraction_enabled_writes_pending_file' is 106 lines long. Consider decomposing. (line 246)
- Long tests:
  - `test_structured_artifacts_success` — 91 lines (starts at 29)
  - `test_failure_path_writes_artifacts_and_prunes` — 51 lines (starts at 122)
  - `test_missing_source_file_reports_error` — 69 lines (starts at 175)

### `.repo_studios/tests/tests_command_center/orchestrators/test_run_command_center_pipeline.py`

- Priority score: 36
- Issues by severity: high=3, medium=2, low=0
- Key findings:
  - [MEDIUM] Test 'test_pipeline_propagates_analysis_failure' is 36 lines. Consider splitting for clarity. (line 139)
  - [MEDIUM] Test 'test_pipeline_detects_missing_scan_artifacts' is 44 lines. Consider splitting for clarity. (line 177)
  - [HIGH] Test 'test_build_paths_rejects_outside_repo' has no assertions. (line 238)
  - [HIGH] Test 'test_load_run_function_requires_existing_script' has no assertions. (line 262)
  - [HIGH] Test 'test_load_run_function_requires_callable_run' has no assertions. (line 269)

### `.repo_studios/tests/tests_command_center/viewer/test_dependency_pack_multi_view_coexistence.py`

- Priority score: 33
- Issues by severity: high=3, medium=1, low=0
- Key findings:
  - [HIGH] Test 'test_dependency_pack_view_coexists_with_function_call_graph' is 59 lines long. Consider decomposing. (line 62)
  - [HIGH] Test 'test_export_contract_matrix_coexists_with_dependency_view' is 75 lines long. Consider decomposing. (line 123)
  - [MEDIUM] Test 'test_external_dependency_map_coexists_with_dependency_view' is 50 lines. Consider splitting for clarity. (line 200)
  - [HIGH] Test 'test_layer_architecture_validation_coexists_with_dependency_view' is 140 lines long. Consider decomposing. (line 252)
- Long tests:
  - `test_dependency_pack_view_coexists_with_function_call_graph` — 59 lines (starts at 62)
  - `test_export_contract_matrix_coexists_with_dependency_view` — 75 lines (starts at 123)
  - `test_layer_architecture_validation_coexists_with_dependency_view` — 140 lines (starts at 252)

### `.repo_studios/tests/tests_consumers/test_generate_anchor_health_report.py`

- Priority score: 33
- Issues by severity: high=3, medium=1, low=0
- Key findings:
  - [HIGH] Test 'test_anchor_health_uses_inventory_artifacts' is 95 lines long. Consider decomposing. (line 26)
  - [MEDIUM] Test 'test_anchor_health_falls_back_to_docs_scan' is 43 lines. Consider splitting for clarity. (line 123)
  - [HIGH] Test 'test_anchor_health_prunes_history' is 61 lines long. Consider decomposing. (line 168)
  - [HIGH] Test 'test_anchor_health_prunes_history' mutates module-level state. (line 168)
- Long tests:
  - `test_anchor_health_uses_inventory_artifacts` — 95 lines (starts at 26)
  - `test_anchor_health_prunes_history` — 61 lines (starts at 168)

## Clean Files

- `.repo_studios/tests/tests_command_center/monkey_patch/test_orchestrator_contract.py` (1 tests)
- `.repo_studios/tests/tests_command_center/monkey_patch/test_summarizer_contract.py` (2 tests)
- `.repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity_helpers.py` (7 tests)
- `.repo_studios/tests/tests_command_center/test_artifacts.py` (4 tests)
- `.repo_studios/tests/tests_command_center/test_prune_logs.py` (2 tests)
- `.repo_studios/tests/tests_command_center/test_telemetry_emitters.py` (1 tests)
- `.repo_studios/tests/tests_command_center/test_topic_pipeline.py` (6 tests)
- `.repo_studios/tests/tests_command_center/viewer/test_class_inheritance_view_definition.py` (2 tests)
- `.repo_studios/tests/tests_command_center/viewer/test_complexity_heatmap_scope.py` (2 tests)
- `.repo_studios/tests/tests_command_center/viewer/test_decorator_usage_scope.py` (4 tests)

## Recommendations

1. Address high severity issues before medium/low findings.
2. Decompose long tests into focused units.
3. Mock external dependencies and remove global state.
4. Replace time.sleep() with deterministic waits.
5. Use descriptive names following given-when-then style.
