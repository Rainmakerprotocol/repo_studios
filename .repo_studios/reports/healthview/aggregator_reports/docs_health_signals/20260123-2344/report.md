# Docs Health Signals

Generated (UTC): 2026-01-23T23:44:20+00:00

## Summary

- Overall score: 62.52
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

- {"code_paths": [".repo_studios/tests/tests_aggregators/test_analyze_monkey_patch_trends.py", ".repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py", ".repo_studios/tests/tests_command_center/monkey_patch/helpers.py", ".repo_studios/tests/tests_command_center/monkey_patch/test_summarize_monkey_patch_overview_content.py", ".repo_studios/tests/tests_command_center/orchestrators/test_run_monkey_patch_oversight.py", ".repo_studios/tests/tests_command_center/test_artifacts.py", ".repo_studios/tests/tests_command_center/test_prune_logs.py", ".repo_studios/tests/tests_library_integration/duplicates/test_scan_duplicates.py", ".repo_studios/tests/tests_producers/test_analyze_standards_index_gaps.py", ".repo_studios/tests/tests_producers/test_scan_monkey_patches.py", ".repo_studios/tests/tests_summarizers/test_summarize_standards.py", ".repo_studios/tests/tests_utilities/test_refresh_mypy_baselines.py"], "doc_candidates": [], "last_commit_utc": "2026-01-22T10:10:49-05:00", "module": "tests"}
<!-- markdownlint-enable MD013 -->

### Coverage — Critical (56.30)

Notes:

- 44% of scanned entities lack docstrings.

| Metric | Value |
| --- | --- |
| modules_scanned | 84 |
| modules_with_findings | 40 |
| entities_scanned | 897 |
| entities_missing_docs | 392 |
| docstring_coverage_percent | 56.3 |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"coverage_percent": 3.03, "doc_candidates": [], "missing_entities": 32, "module_path": ".repo_studios/scripts/producers/validate_inventory.py"}
- {"coverage_percent": 25.81, "doc_candidates": [], "missing_entities": 23, "module_path": ".repo_studios/command_center/scripts/aggregators/scan_duplicates.py"}
- {"coverage_percent": 4.55, "doc_candidates": [], "missing_entities": 21, "module_path": ".repo_studios/scripts/producers/seed_standards_prompts.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 20, "module_path": ".repo_studios/command_center/scripts/producers/generate_commandview_inventory.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 19, "module_path": ".repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py"}
<!-- markdownlint-enable MD013 -->

### Structure — Critical (36.54)

| Metric | Value |
| --- | --- |
| total_documents | 144 |
| documents_missing_h1 | 7 |
| documents_missing_h2 | 3 |
| documents_with_cross_file_duplicates | 115 |
| documents_with_repeated_anchors | 0 |
| cross_file_duplicates | 81 |
| total_slugs | 794 |
| anchor_validation_issue_count | 0 |
| anchor_validation_status | ok |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"documents": 120, "root": ".repo_studios"}
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

### Hygiene — Healthy (80.00)

Notes:

- Placeholder scan surfaced 4 matches.

| Metric | Value |
| --- | --- |
| placeholder_total_matches | 4 |
| placeholder_status | ok |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"placeholder_by_pattern": {"NOTE": 1, "XXX": 3}}
<!-- markdownlint-enable MD013 -->
