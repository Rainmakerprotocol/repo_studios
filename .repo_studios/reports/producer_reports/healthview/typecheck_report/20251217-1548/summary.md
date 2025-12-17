# Typecheck Report

- generated_utc: 2025-12-17T15:48:58.981404+00:00
- status: error
- mypy_version: mypy 1.11.1 (compiled: no)
- bundle_dir: C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\healthview\typecheck_report\20251217-1548

## Summary

| Metric | Value |
|---|---:|
| error_count | 552 |
| files_with_issues | 105 |
| files_checked | 250 |
| paths_checked | 1 |

## Sample Errors

- .repo_studios\scripts\producers\generate_anchor_inventory.py:30 — [syntax] Invalid "type: ignore" comment
- .repo_studios\scripts\producers\generate_anchor_inventory.py:38 — [syntax] Invalid "type: ignore" comment
- .repo_studios\scripts\producers\generate_anchor_inventory.py:39 — [syntax] Invalid "type: ignore" comment
- .repo_studios\scripts\producers\generate_anchor_inventory.py:45 — [syntax] Invalid "type: ignore" comment
- .repo_studios\scripts\producers\generate_anchor_inventory.py:53 — [syntax] Invalid "type: ignore" comment
- .repo_studios\scripts\producers\generate_anchor_inventory.py:54 — [syntax] Invalid "type: ignore" comment
- .repo_studios\scripts\producers\generate_doc_index.py:58 — [syntax] Invalid "type: ignore" comment
- .repo_studios\scripts\producers\generate_doc_index.py:73 — [syntax] Invalid "type: ignore" comment
- .repo_studios\tests\tests_summarizers\test_summarize_standards.py:115 — [var-annotated] Need type annotation for "legacy_payload"
- .repo_studios\tests\tests_summarizers\test_summarize_standards.py:131 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_producers\test_verify_docs_integrity.py:23 — [name-defined] Name "module.dt.tzinfo" is not defined
- .repo_studios\tests\tests_producers\test_verify_docs_integrity.py:23 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_producers\test_verify_docs_integrity.py:56 — [arg-type] Argument 2 to "_render_json_block" has incompatible type "dict[str, list[dict[str, object]]]"; expected "dict[str, object]"
- .repo_studios\tests\tests_producers\test_validate_metrics_anchor_stubs.py:23 — [name-defined] Name "module.dt.tzinfo" is not defined
- .repo_studios\tests\tests_producers\test_validate_metrics_anchor_stubs.py:23 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_producers\test_validate_inventory.py:17 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_producers\test_validate_import_boundaries.py:31 — [name-defined] Name "module.dt.tzinfo" is not defined
- .repo_studios\tests\tests_producers\test_validate_import_boundaries.py:31 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_producers\test_generate_undocumented_logic_report.py:16 — [arg-type] Argument 1 to "module_from_spec" has incompatible type "ModuleSpec | None"; expected "ModuleSpec"
- .repo_studios\tests\tests_producers\test_generate_undocumented_logic_report.py:17 — [union-attr] Item "None" of "ModuleSpec | None" has no attribute "loader"

## Invocation

`C:\Python313\python.exe -m mypy --show-error-codes --no-color-output --hide-error-context "<all python files (batched)>"`
