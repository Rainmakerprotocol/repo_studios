# Docs Health Signals

Generated (UTC): 2026-02-03T23:33:37+00:00

## Summary

- Overall score: 60.41
- Status tally: warning=1, critical=2, healthy=2
- Signals scored: freshness, coverage, structure, integrity, hygiene

## Signal Details

### Freshness — Warning (66.67)

| Metric | Value |
| --- | --- |
| modules_with_code_churn | 3 |
| modules_with_doc_updates | 2 |
| modules_without_doc_updates | 1 |
| allowlisted_modules | [] |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"code_paths": [".repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py", ".repo_studios/tests/tests_command_center/producers/test_generate_function_inventory_command_center.py", ".repo_studios/tests/tests_command_center/test_artifacts.py", ".repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py", ".repo_studios/tests/tests_command_center/test_prune_logs.py", ".repo_studios/tests/tests_consumers/test_generate_anchor_health_report.py", ".repo_studios/tests/tests_consumers/test_generate_test_log_health_report.py", ".repo_studios/tests/tests_orchestrators/test_run_available_scripts_oversight.py", ".repo_studios/tests/tests_producers/test_analyze_standards_index_gaps.py", ".repo_studios/tests/tests_producers/test_audit_helper_adoption.py", ".repo_studios/tests/tests_producers/test_check_inventory_health.py", ".repo_studios/tests/tests_producers/test_function_inventory_integration.py", ".repo_studios/tests/tests_producers/test_generate_doc_index.py", ".repo_studios/tests/tests_producers/test_generate_function_analysis.py", ".repo_studios/tests/tests_producers/test_generate_function_inventory.py", ".repo_studios/tests/tests_producers/test_generate_lizard_report.py", ".repo_studios/tests/tests_producers/test_generate_test_coverage_inventory.py", ".repo_studios/tests/tests_producers/test_render_inventory_views.py", ".repo_studios/tests/tests_producers/test_validate_import_boundaries.py", ".repo_studios/tests/tests_producers/test_validate_inventory.py", ".repo_studios/tests/tests_summarizers/test_summarize_health_suite.py", ".repo_studios/tests/tests_summarizers/test_summarize_standards.py"], "doc_candidates": [], "last_commit_utc": "2026-01-30T14:26:56-05:00", "module": "tests"}
<!-- markdownlint-enable MD013 -->

### Coverage — Critical (58.72)

Notes:

- 41% of scanned entities lack docstrings.

| Metric | Value |
| --- | --- |
| modules_scanned | 85 |
| modules_with_findings | 39 |
| entities_scanned | 906 |
| entities_missing_docs | 374 |
| docstring_coverage_percent | 58.72 |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"coverage_percent": 14.71, "doc_candidates": [], "missing_entities": 29, "module_path": ".repo_studios/scripts/producers/validate_inventory.py"}
- {"coverage_percent": 25.81, "doc_candidates": [], "missing_entities": 23, "module_path": ".repo_studios/command_center/scripts/aggregators/scan_duplicates.py"}
- {"coverage_percent": 4.55, "doc_candidates": [], "missing_entities": 21, "module_path": ".repo_studios/scripts/producers/seed_standards_prompts.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 20, "module_path": ".repo_studios/command_center/scripts/cc_producers/generate_commandview_inventory.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 19, "module_path": ".repo_studios/command_center/scripts/cc_producers/analyze_standards_index_gaps.py"}
<!-- markdownlint-enable MD013 -->

### Structure — Critical (10.18)

Notes:

- Markdown anchor validator reported 84 issues.

| Metric | Value |
| --- | --- |
| total_documents | 200 |
| documents_missing_h1 | 7 |
| documents_missing_h2 | 3 |
| documents_with_cross_file_duplicates | 169 |
| documents_with_repeated_anchors | 7 |
| cross_file_duplicates | 167 |
| total_slugs | 1168 |
| anchor_validation_issue_count | 84 |
| anchor_validation_status | fail |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"documents": 176, "root": ".repo_studios"}
- {"documents": 12, "root": "standards"}
- {"documents": 6, "root": "automation"}
- {"documents": 4, "root": "templates"}
- {"documents": 1, "root": "db_integrations"}
<!-- markdownlint-enable MD013 -->

### Integrity — Healthy (100.00)

| Metric | Value |
| --- | --- |
| docs_integrity_status | ok |
| mismatched_blocks | 0 |
| json_blocks_checked | 2 |
| documents_processed | 1 |
| missing_metrics_stubs | 0 |
| anchors_referenced | 0 |

### Hygiene — Healthy (100.00)

| Metric | Value |
| --- | --- |
| placeholder_total_matches | 0 |
| placeholder_status | ok |
