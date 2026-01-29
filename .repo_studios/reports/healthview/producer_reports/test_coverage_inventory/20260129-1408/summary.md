# Test Coverage Inventory

- run_timestamp: 20260129-1408
- generated_utc: 2026-01-29T14:08:41.464713+00:00
- coverage_source: .repo_studios/tmp_cli_probe/coverage_repo.xml
- status: ok
- total_files: 84
- total_functions: 1581
- covered_functions: 1548
- overall_coverage_pct: 97.91

## Files by Coverage

| File | Functions | Covered | Coverage % | Uncovered Functions |
| --- | ---:| ---:| ---:| --- |
| `tmp_generate_lizard_report_new.py` | 21 | 0 | 0.00 | `Offender.to_payload`, `_current_utc`, `_parse_timestamp`, `_timestamp_slug`, `_ensure_lizard_json_extension`, `_has_flag`, `_apply_default_extra_args`, `_build_command`, `_sanitize_command`, `_resolve_targets`, `_extract_file_path`, `_as_int`, `_collect_offenders`, `_render_markdown`, `_render_log`, `_format_raw_output`, `_compose_report`, `_append_note`, `_build_parser`, `configure_logging`, `main` |
| `.repo_studios/scripts/consumers/generate_anchor_health_report.py` | 20 | 18 | 90.00 | `Cluster.file_count`, `main` |
| `.repo_studios/scripts/producers/generate_standards_index.py` | 32 | 29 | 90.62 | `_dynamic_import_extract`, `_absent`, `_empty` |
| `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` | 27 | 25 | 92.59 | `_is_run_slug`, `_coerce_payload` |
| `.repo_studios/scripts/producers/check_inventory_health.py` | 17 | 16 | 94.12 | `_is_timestamp_dir` |
| `.repo_studios/scripts/utilities/configure_faulthandler_runtime.py` | 17 | 16 | 94.12 | `_FcntlLike.flock` |
| `.repo_studios/scripts/producers/generate_typecheck_report.py` | 31 | 30 | 96.77 | `_allowed` |
| `.repo_studios/command_center/scripts/aggregators/scan_duplicates.py` | 48 | 47 | 97.92 | `main` |
| `.repo_studios/command_center/scripts/cc_producers/generate_commandview_inventory.py` | 108 | 107 | 99.07 | `CoverageIndex.__bool__` |
| `.repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py` | 8 | 8 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/cc_producers/analyze_standards_index_gaps.py` | 23 | 23 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/cc_producers/audit_helper_adoption.py` | 17 | 17 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/artifacts.py` | 6 | 6 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/build_commandview_selector.py` | 7 | 7 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/catalog_registry.py` | 8 | 8 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/cli.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/database_integration.py` | 26 | 26 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/guardrails.py` | 4 | 4 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/manifest.py` | 8 | 8 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/metrics.py` | 7 | 7 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/pathing.py` | 1 | 1 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/prune_logs.py` | 3 | 3 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/report_paths.py` | 7 | 7 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/retention_policy.py` | 14 | 14 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/summarizer_runner.py` | 2 | 2 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/telemetry_emitters.py` | 4 | 4 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/test_log_analysis.py` | 16 | 16 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/topic_pipeline.py` | 9 | 9 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py` | 15 | 15 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py` | 21 | 21 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py` | 30 | 30 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py` | 46 | 46 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` | 22 | 22 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_inventory_update.py` | 5 | 5 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py` | 24 | 24 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` | 37 | 37 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/summarizers/generate_function_analysis.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py` | 17 | 17 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/utilities/reports_naming_audit.py` | 14 | 14 | 100.00 | (none) |
| `.repo_studios/command_center/viewer/refresh.py` | 6 | 6 | 100.00 | (none) |
| `.repo_studios/command_center/viewer/update_service.py` | 9 | 9 | 100.00 | (none) |
| `.repo_studios/scripts/aggregators/aggregate_docs_health_signals.py` | 21 | 21 | 100.00 | (none) |
| `.repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py` | 20 | 20 | 100.00 | (none) |
| `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py` | 24 | 24 | 100.00 | (none) |
| `.repo_studios/scripts/consumers/classify_monkey_patches.py` | 17 | 17 | 100.00 | (none) |
| `.repo_studios/scripts/consumers/generate_fault_artifacts.py` | 19 | 19 | 100.00 | (none) |
| `.repo_studios/scripts/consumers/generate_test_log_health_report.py` | 24 | 24 | 100.00 | (none) |
| `.repo_studios/scripts/orchestrators/healthview/run_healthview_agent_loop.py` | 23 | 23 | 100.00 | (none) |
| `.repo_studios/scripts/producers/analyze_standards_index_gaps.py` | 1 | 1 | 100.00 | (none) |
| `.repo_studios/scripts/producers/analyze_test_hardening.py` | 29 | 29 | 100.00 | (none) |
| `.repo_studios/scripts/producers/collect_faulthandler_reports.py` | 19 | 19 | 100.00 | (none) |
| `.repo_studios/scripts/producers/collect_test_log_reports.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/scripts/producers/diff_standards_index.py` | 21 | 21 | 100.00 | (none) |
| `.repo_studios/scripts/producers/extract_standards_rules.py` | 10 | 10 | 100.00 | (none) |
| `.repo_studios/scripts/producers/generate_anchor_inventory.py` | 30 | 30 | 100.00 | (none) |
| `.repo_studios/scripts/producers/generate_code_doc_churn_report.py` | 20 | 20 | 100.00 | (none) |
| `.repo_studios/scripts/producers/generate_dependency_hygiene_report.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/scripts/producers/generate_doc_index.py` | 27 | 27 | 100.00 | (none) |
| `.repo_studios/scripts/producers/generate_import_graph_report.py` | 15 | 15 | 100.00 | (none) |
| `.repo_studios/scripts/producers/generate_lizard_report.py` | 30 | 30 | 100.00 | (none) |
| `.repo_studios/scripts/producers/generate_test_coverage_inventory.py` | 25 | 25 | 100.00 | (none) |
| `.repo_studios/scripts/producers/generate_undocumented_logic_report.py` | 25 | 25 | 100.00 | (none) |
| `.repo_studios/scripts/producers/render_inventory_views.py` | 22 | 22 | 100.00 | (none) |
| `.repo_studios/scripts/producers/scan_code_placeholders.py` | 23 | 23 | 100.00 | (none) |
| `.repo_studios/scripts/producers/scan_monkey_patches.py` | 59 | 59 | 100.00 | (none) |
| `.repo_studios/scripts/producers/seed_standards_prompts.py` | 19 | 19 | 100.00 | (none) |
| `.repo_studios/scripts/producers/validate_import_boundaries.py` | 20 | 20 | 100.00 | (none) |
| `.repo_studios/scripts/producers/validate_inventory.py` | 37 | 37 | 100.00 | (none) |
| `.repo_studios/scripts/producers/validate_markdown_anchors.py` | 15 | 15 | 100.00 | (none) |
| `.repo_studios/scripts/producers/validate_metrics_anchor_stubs.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/scripts/producers/verify_docs_integrity.py` | 24 | 24 | 100.00 | (none) |
| `.repo_studios/scripts/summarizers/summarize_standards.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/scripts/utilities/anchor_inventory_loader.py` | 4 | 4 | 100.00 | (none) |
| `.repo_studios/scripts/utilities/dump_faulthandler_snapshot.py` | 10 | 10 | 100.00 | (none) |
| `.repo_studios/scripts/utilities/fault_run_analysis.py` | 10 | 10 | 100.00 | (none) |
| `.repo_studios/scripts/utilities/monkey_patch_risk.py` | 1 | 1 | 100.00 | (none) |
| `.repo_studios/scripts/utilities/refresh_mypy_baselines.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/scripts/utilities/validate_healthview_agent_workflow_spec.py` | 10 | 10 | 100.00 | (none) |
| `.repo_studios/tools/validate_inventory.py` | 4 | 4 | 100.00 | (none) |
