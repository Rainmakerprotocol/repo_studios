# Docs Health Signals

Generated (UTC): 2026-02-03T21:25:23+00:00

## Summary

- Overall score: 62.34
- Status tally: warning=2, critical=1, healthy=2
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

### Coverage — Warning (64.09)

Notes:

- 36% of scanned entities lack docstrings.

| Metric | Value |
| --- | --- |
| modules_scanned | 43 |
| modules_with_findings | 16 |
| entities_scanned | 479 |
| entities_missing_docs | 172 |
| docstring_coverage_percent | 64.09 |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"coverage_percent": 14.71, "doc_candidates": [], "missing_entities": 29, "module_path": ".repo_studios/scripts/producers/validate_inventory.py"}
- {"coverage_percent": 4.55, "doc_candidates": [], "missing_entities": 21, "module_path": ".repo_studios/scripts/producers/seed_standards_prompts.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 16, "module_path": ".repo_studios/scripts/orchestrators/healthview/run_healthview_agent_loop.py"}
- {"coverage_percent": 11.11, "doc_candidates": [], "missing_entities": 16, "module_path": ".repo_studios/scripts/producers/render_inventory_views.py"}
- {"coverage_percent": 6.25, "doc_candidates": [], "missing_entities": 15, "module_path": ".repo_studios/scripts/producers/check_inventory_health.py"}
<!-- markdownlint-enable MD013 -->

### Structure — Critical (10.47)

Notes:

- Markdown anchor validator reported 28 issues.

| Metric | Value |
| --- | --- |
| total_documents | 189 |
| documents_missing_h1 | 7 |
| documents_missing_h2 | 3 |
| documents_with_cross_file_duplicates | 158 |
| documents_with_repeated_anchors | 3 |
| cross_file_duplicates | 194 |
| total_slugs | 1070 |
| anchor_validation_issue_count | 28 |
| anchor_validation_status | fail |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"documents": 165, "root": ".repo_studios"}
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
