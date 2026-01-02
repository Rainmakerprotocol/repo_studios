# Docs Health Signals

Generated (UTC): 2026-01-02T04:22:38+00:00

## Summary

- Overall score: 35.56
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

### Coverage — Critical (17.47)

Notes:

- 83% of scanned entities lack docstrings.

| Metric | Value |
| --- | --- |
| modules_scanned | 84 |
| modules_with_findings | 68 |
| entities_scanned | 893 |
| entities_missing_docs | 737 |
| docstring_coverage_percent | 17.47 |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"coverage_percent": 5.88, "doc_candidates": [], "missing_entities": 48, "module_path": ".repo_studios/scripts/producers/scan_monkey_patches.py"}
- {"coverage_percent": 3.03, "doc_candidates": [], "missing_entities": 32, "module_path": ".repo_studios/scripts/producers/validate_inventory.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 25, "module_path": ".repo_studios/scripts/producers/generate_anchor_inventory.py"}
- {"coverage_percent": 25.81, "doc_candidates": [], "missing_entities": 23, "module_path": ".repo_studios/command_center/scripts/aggregators/scan_duplicates.py"}
- {"coverage_percent": 0.0, "doc_candidates": [], "missing_entities": 21, "module_path": ".repo_studios/scripts/producers/seed_standards_prompts.py"}
<!-- markdownlint-enable MD013 -->

### Structure — Critical (36.84)

| Metric | Value |
| --- | --- |
| total_documents | 139 |
| documents_missing_h1 | 7 |
| documents_missing_h2 | 3 |
| documents_with_cross_file_duplicates | 110 |
| documents_with_repeated_anchors | 0 |
| cross_file_duplicates | 78 |
| total_slugs | 749 |
| anchor_validation_issue_count | 0 |
| anchor_validation_status | ok |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"documents": 117, "root": ".repo_studios"}
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
