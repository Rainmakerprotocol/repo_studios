# Docs Health Signals

Generated (UTC): 2025-11-25T19:33:21+00:00

## Summary

- Overall score: 38.76
- Status tally: critical=3, healthy=1, warning=1
- Signals scored: freshness, coverage, structure, integrity, hygiene

## Signal Details

### Freshness — Critical (50.00)

| Metric | Value |
| --- | --- |
| modules_with_code_churn | 4 |
| modules_with_doc_updates | 2 |
| modules_without_doc_updates | 2 |
| allowlisted_modules | [] |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"code_paths": [".codacy/temp_onboarding/generate_function_inventory.py"], "doc_candidates": [], "last_commit_utc": "2025-11-05T14:40:05-05:00", "module": "codacy"}
- {"code_paths": ["tmp_generate_lizard_report_new.py"], "doc_candidates": [], "last_commit_utc": "2025-11-24T18:02:45-05:00", "module": "tmp_generate_lizard_report_new.py"}
<!-- markdownlint-enable MD013 -->

### Coverage — Critical (7.11)

Notes:

- 93% of scanned entities lack docstrings.

| Metric | Value |
| --- | --- |
| modules_scanned | 61 |
| modules_with_findings | 54 |
| entities_scanned | 633 |
| entities_missing_docs | 588 |
| docstring_coverage_percent | 7.11 |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"coverage_percent": 5.66, "doc_candidates": [".repo_studios/docs/automation/scan_monkey_patches.md", ".copilot_todo.md", ".github/architect.chatmode.md", ".github/ask.chatmode.md", ".github/code.chatmode.md"], "missing_entities": 50, "module_path": ".repo_studios/scripts/producers/scan_monkey_patches.py"}
- {"coverage_percent": 2.94, "doc_candidates": [".repo_studios/docs/automation/validate_inventory.md", ".copilot_todo.md", ".github/architect.chatmode.md", ".github/ask.chatmode.md", ".github/code.chatmode.md"], "missing_entities": 33, "module_path": ".repo_studios/scripts/producers/validate_inventory.py"}
- {"coverage_percent": 0.0, "doc_candidates": [".copilot_todo.md", ".github/architect.chatmode.md", ".github/ask.chatmode.md", ".github/code.chatmode.md", ".github/copilot-instructions.md"], "missing_entities": 27, "module_path": ".repo_studios/scripts/producers/generate_anchor_inventory.py"}
- {"coverage_percent": 26.47, "doc_candidates": [".copilot_todo.md", ".github/architect.chatmode.md", ".github/ask.chatmode.md", ".github/code.chatmode.md", ".github/copilot-instructions.md"], "missing_entities": 25, "module_path": ".repo_studios/command_center/scripts/aggregators/scan_duplicates.py"}
- {"coverage_percent": 0.0, "doc_candidates": [".repo_studios/docs/automation/scan_code_placeholders.md", ".copilot_todo.md", ".github/architect.chatmode.md", ".github/ask.chatmode.md", ".github/code.chatmode.md"], "missing_entities": 22, "module_path": ".repo_studios/scripts/producers/scan_code_placeholders.py"}
<!-- markdownlint-enable MD013 -->

### Structure — Critical (38.47)

| Metric | Value |
| --- | --- |
| total_documents | 77 |
| documents_missing_h1 | 11 |
| documents_missing_h2 | 6 |
| documents_with_cross_file_duplicates | 51 |
| documents_with_repeated_anchors | 0 |
| cross_file_duplicates | 41 |
| total_slugs | 397 |
| anchor_validation_issue_count | 0 |
| anchor_validation_status | ok |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"documents": 66, "root": ".repo_studios"}
- {"documents": 11, "root": "standards"}
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

### Hygiene — Warning (60.00)

Notes:

- Monkey patch scan reported 56 findings.

| Metric | Value |
| --- | --- |
| placeholder_total_matches | 0 |
| placeholder_status | ok |
| monkey_patch_total_findings | 56 |
| monkey_patch_status | ok |

<!-- markdownlint-disable MD013 -->
Top findings:

- {"monkey_patch_by_category": {"attribute_reassignment_on_import": 3, "global_env_mutation": 1, "setattr_on_import_or_class": 15, "sys_modules_assignment": 37}}
<!-- markdownlint-enable MD013 -->
