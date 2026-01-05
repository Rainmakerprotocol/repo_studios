# Docs Health Signals

Generated (UTC): 2026-01-04T17:31:44+00:00

## Summary

- Overall score: 49.08
- Status tally: critical=4, healthy=1
- Signals scored: freshness, coverage, structure, integrity, hygiene

## Signal Details

### Freshness — Critical (33.33)

| Metric | Value |
| --- | --- |
| modules_with_code_churn | 3 |
| modules_with_doc_updates | 1 |
| modules_without_doc_updates | 2 |
| allowlisted_modules | [] |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"code_paths": ["tmp_fix_lines.py"], "doc_candidates": [], "last_commit_utc": "2025-12-28T12:37:12-05:00", "module": "tmp_fix_lines.py"}
- {"code_paths": ["tmp_generate_lizard_report_new.py"], "doc_candidates": [], "last_commit_utc": "2025-12-26T13:22:21-05:00", "module": "tmp_generate_lizard_report_new.py"}
<!-- markdownlint-enable MD013 -->

### Coverage — Critical (56.20)

Notes:

- 44% of scanned entities lack docstrings.

| Metric | Value |
| --- | --- |
| modules_scanned | 84 |
| modules_with_findings | 40 |
| entities_scanned | 895 |
| entities_missing_docs | 392 |
| docstring_coverage_percent | 56.2 |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"coverage_percent": 3.03, "doc_candidates": [], "missing_entities": 32, "module_path": ".repo_studios/scripts/producers/validate_inventory.py"}
- {"coverage_percent": 25.81, "doc_candidates": [], "missing_entities": 23, "module_path": ".repo_studios/command_center/scripts/aggregators/scan_duplicates.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 21, "module_path": ".repo_studios/scripts/producers/seed_standards_prompts.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 20, "module_path": ".repo_studios/command_center/scripts/producers/generate_commandview_inventory.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 19, "module_path": ".repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py"}
<!-- markdownlint-enable MD013 -->

### Structure — Critical (36.62)

| Metric | Value |
| --- | --- |
| total_documents | 142 |
| documents_missing_h1 | 7 |
| documents_missing_h2 | 3 |
| documents_with_cross_file_duplicates | 113 |
| documents_with_repeated_anchors | 0 |
| cross_file_duplicates | 81 |
| total_slugs | 779 |
| anchor_validation_issue_count | 0 |
| anchor_validation_status | ok |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"documents": 120, "root": ".repo_studios"}
- {"documents": 12, "root": "standards"}
- {"documents": 5, "root": "automation"}
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

### Hygiene — Critical (45.00)

Notes:

- Placeholder scan surfaced 3 matches.
- Monkey patch scan reported 119 findings.

| Metric | Value |
| --- | --- |
| placeholder_total_matches | 3 |
| placeholder_status | ok |
| monkey_patch_total_findings | 119 |
| monkey_patch_status | ok |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"placeholder_by_pattern": {"XXX": 3}}
- {"monkey_patch_by_category": {"attribute_reassignment_on_import": 3, "builtins_mutation": 1, "global_env_mutation": 2, "setattr_on_import_or_class": 53, "sys_modules_assignment": 60}}
<!-- markdownlint-enable MD013 -->
