# Test Coverage Inventory

- run_timestamp: 20260124-1346
- generated_utc: 2026-01-24T13:46:42.263207+00:00
- coverage_source: coverage.xml
- status: ok
- total_files: 31
- total_functions: 523
- covered_functions: 452
- overall_coverage_pct: 86.42

## Files by Coverage

| File | Functions | Covered | Coverage % | Uncovered Functions |
| --- | ---:| ---:| ---:| --- |
| `.repo_studios/command_center/scripts/orchestrators/run_inventory_update.py` | 5 | 0 | 0.00 | build_parser, configure_logging, _ensure_target_allowed, run, main |
| `tmp_generate_lizard_report_new.py` | 21 | 0 | 0.00 | Offender.to_payload, _current_utc, _parse_timestamp, _timestamp_slug, _ensure_lizard_json_extension, _has_flag, _apply_default_extra_args, _build_command, _sanitize_command, _resolve_targets, _extract_file_path, _as_int, _collect_offenders, _render_markdown, _render_log, _format_raw_output, _compose_report, _append_note, _build_parser, configure_logging, main |
| `.repo_studios/command_center/scripts/libraries/prune_logs.py` | 3 | 1 | 33.33 | _is_current, _sort_key |
| `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` | 27 | 20 | 74.07 | _is_run_slug, _coerce_payload, index_step, gap_step, diff_step, prompt_step, summary_step |
| `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py` | 46 | 37 | 80.43 | _metric_int, doc_index_step, anchor_inventory_step, anchor_validation_step, docs_integrity_step, metrics_stub_step, churn_step, undocumented_step, aggregator_step |
| `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` | 22 | 18 | 81.82 | render_step_section, producer_step, consumer_step, summarizer_step |
| `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py` | 24 | 20 | 83.33 | producer_step, consumer_step, aggregator_step, summarizer_step |
| `.repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py` | 17 | 15 | 88.24 | _dir_timestamp, _format_pct |
| `.repo_studios/command_center/scripts/summarizers/generate_function_analysis.py` | 18 | 16 | 88.89 | _append, _write_analysis |
| `.repo_studios/command_center/scripts/cc_producers/generate_commandview_inventory.py` | 108 | 98 | 90.74 | CoverageIndex.__bool__, _names, _dedupe, _iter_entries, _record_local, _iter_entries, _finalize, _append, _ingest, _capture_function |
| `.repo_studios/command_center/scripts/aggregators/scan_duplicates.py` | 48 | 44 | 91.67 | record_occurrence, _write_matrix, _write_summary, main |
| `.repo_studios/command_center/scripts/libraries/test_log_analysis.py` | 16 | 15 | 93.75 | _totals_and_internal_only |
| `.repo_studios/command_center/scripts/libraries/artifacts.py` | 6 | 6 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/build_commandview_selector.py` | 7 | 7 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/catalog_registry.py` | 8 | 8 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/cli.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/guardrails.py` | 4 | 4 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/manifest.py` | 8 | 8 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/metrics.py` | 7 | 7 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/pathing.py` | 1 | 1 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/report_paths.py` | 7 | 7 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/retention_policy.py` | 14 | 14 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/summarizer_runner.py` | 2 | 2 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/telemetry_emitters.py` | 4 | 4 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/libraries/topic_pipeline.py` | 9 | 9 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py` | 13 | 13 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py` | 18 | 18 | 100.00 | (none) |
| `.repo_studios/command_center/scripts/utilities/reports_naming_audit.py` | 14 | 14 | 100.00 | (none) |
| `.repo_studios/command_center/viewer/refresh.py` | 6 | 6 | 100.00 | (none) |
| `.repo_studios/command_center/viewer/update_service.py` | 9 | 9 | 100.00 | (none) |
