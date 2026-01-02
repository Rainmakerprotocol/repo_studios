# Test Coverage Inventory

- run_timestamp: 20260102-0423
- generated_utc: 2026-01-02T04:23:14.814099+00:00
- coverage_source: .repo_studios/tmp_cli_probe/coverage_repo.xml
- status: ok
- total_files: 52
- total_functions: 889
- covered_functions: 861
- overall_coverage_pct: 96.85

## Files by Coverage

| File | Functions | Covered | Coverage % | Uncovered Functions |
| --- | ---:| ---:| ---:| --- |
| `tmp_generate_lizard_report_new.py` | 21 | 0 | 0.00 | Offender.to_payload, _current_utc, _parse_timestamp, _timestamp_slug, _ensure_lizard_json_extension, _has_flag, _apply_default_extra_args, _build_command, _sanitize_command, _resolve_targets, _extract_file_path, _as_int, _collect_offenders, _render_markdown, _render_log, _format_raw_output, _compose_report, _append_note, _build_parser, configure_logging, main |
| `.repo_studios/command_center/scripts/summarizers/generate_function_analysis.py` | 18 | 16 | 88.89 | _append, _write_analysis |
| `.repo_studios/scripts/consumers/generate_anchor_health_report.py` | 20 | 18 | 90.00 | Cluster.file_count, main |
| `.repo_studios/command_center/scripts/aggregators/scan_duplicates.py` | 48 | 47 | 97.92 | main |
| `.repo_studios/command_center/scripts/producers/generate_commandview_inventory.py` | 108 | 106 | 98.15 | CoverageIndex.__bool__, _finalize |
| `.repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py` | 8 | 8 | 100.00 | (none) |
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
| `.repo_studios/command_center/scripts/libraries/test_log_analysis.py` | 14 | 14 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/topic_pipeline.py` | 9 | 9 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py` | 15 | 15 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py` | 21 | 21 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py` | 31 | 31 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py` | 38 | 38 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_inventory_update.py` | 5 | 5 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py` | 20 | 20 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` | 25 | 25 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` | 32 | 32 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py` | 16 | 16 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/utilities/reports_naming_audit.py` | 14 | 14 | 100.00 | (none) |
| `.repo_studios/command_center/viewer/refresh.py` | 6 | 6 | 100.00 | (none) |
| `.repo_studios/command_center/viewer/update_service.py` | 9 | 9 | 100.00 | (none) |
| `.repo_studios/scripts/aggregators/aggregate_docs_health_signals.py` | 21 | 21 | 100.00 | (none) |
| `.repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py` | 15 | 15 | 100.00 | (none) |
| `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py` | 25 | 25 | 100.00 | (none) |
| `.repo_studios/scripts/consumers/classify_monkey_patches.py` | 17 | 17 | 100.00 | (none) |
| `.repo_studios/scripts/consumers/generate_fault_artifacts.py` | 19 | 19 | 100.00 | (none) |
| `.repo_studios/scripts/consumers/generate_test_log_health_report.py` | 26 | 26 | 100.00 | (none) |
| `.repo_studios/scripts/producers/collect_test_log_reports.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/scripts/producers/generate_anchor_inventory.py` | 30 | 30 | 100.00 | (none) |
| `.repo_studios/scripts/producers/validate_inventory.py` | 36 | 36 | 100.00 | (none) |
| `.repo_studios/scripts/utilities/anchor_inventory_loader.py` | 4 | 4 | 100.00 | (none) |
| `.repo_studios/scripts/utilities/fault_run_analysis.py` | 10 | 10 | 100.00 | (none) |
| `.repo_studios/scripts/utilities/monkey_patch_risk.py` | 1 | 1 | 100.00 | (none) |
| `.repo_studios/tools/validate_inventory.py` | 4 | 4 | 100.00 | (none) |
