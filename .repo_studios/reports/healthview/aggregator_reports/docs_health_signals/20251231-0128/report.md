# Docs Health Signals

Generated (UTC): 2025-12-31T01:28:30+00:00

## Summary

- Overall score: 34.14
- Status tally: critical=3, healthy=1, unknown=1
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

### Coverage — Critical (14.48)

Notes:

- 86% of scanned entities lack docstrings.

| Metric | Value |
| --- | --- |
| modules_scanned | 84 |
| modules_with_findings | 69 |
| entities_scanned | 891 |
| entities_missing_docs | 762 |
| docstring_coverage_percent | 14.48 |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"coverage_percent": 5.88, "doc_candidates": [], "missing_entities": 48, "module_path": ".repo_studios/scripts/producers/scan_monkey_patches.py"}
- {"coverage_percent": 2.94, "doc_candidates": [], "missing_entities": 33, "module_path": ".repo_studios/scripts/producers/validate_inventory.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 25, "module_path": ".repo_studios/scripts/producers/generate_anchor_inventory.py"}
- {"coverage_percent": 25.81, "doc_candidates": [], "missing_entities": 23, "module_path": ".repo_studios/command_center/scripts/aggregators/scan_duplicates.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 21, "module_path": ".repo_studios/scripts/producers/seed_standards_prompts.py"}
<!-- markdownlint-enable MD013 -->

### Structure — Critical (37.99)

| Metric | Value |
| --- | --- |
| total_documents | 133 |
| documents_missing_h1 | 7 |
| documents_missing_h2 | 3 |
| documents_with_cross_file_duplicates | 103 |
| documents_with_repeated_anchors | 0 |
| cross_file_duplicates | 73 |
| total_slugs | 722 |
| anchor_validation_issue_count | 0 |
| anchor_validation_status | ok |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"documents": 111, "root": ".repo_studios"}
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

### Hygiene — Unknown (n/a)

Notes:

- Hygiene signals unavailable.
