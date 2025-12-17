# Typecheck Report

- generated_utc: 2025-12-17T14:32:45.286559+00:00
- status: error
- mypy_version: mypy 1.11.1 (compiled: no)
- bundle_dir: C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\healthview\typecheck_report\20251217-1432

## Summary

| Metric | Value |
|---|---:|
| error_count | 62 |
| files_with_issues | 22 |
| files_checked | 50 |
| paths_checked | 1 |

## Sample Errors

- .repo_studios\vendor\lizard_ext\lizardjson.py:8 — [import-untyped] Skipping analyzing "lizard": module is installed, but missing library stubs or py.typed marker
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
- .repo_studios\tests\tests_producers\test_generate_undocumented_logic_report.py:19 — [union-attr] Item "None" of "ModuleSpec | None" has no attribute "loader"
- .repo_studios\tests\tests_producers\test_generate_function_analysis.py:36 — [no-any-return] Returning Any from function declared to return "Callable[[Path], str]"
- .repo_studios\tests\tests_producers\test_generate_function_analysis.py:44 — [arg-type] Argument 1 to "module_from_spec" has incompatible type "ModuleSpec | None"; expected "ModuleSpec"
- .repo_studios\tests\tests_producers\test_generate_function_analysis.py:45 — [union-attr] Item "None" of "ModuleSpec | None" has no attribute "loader"
- .repo_studios\tests\tests_producers\test_generate_function_analysis.py:47 — [union-attr] Item "None" of "ModuleSpec | None" has no attribute "name"
- .repo_studios\tests\tests_producers\test_generate_function_analysis.py:57 — [no-any-return] Returning Any from function declared to return "int"
- .repo_studios\tests\tests_producers\test_generate_function_analysis.py:61 — [no-any-return] Returning Any from function declared to return "int"

## Invocation

`C:\Python313\python.exe -m mypy --show-error-codes --no-color-output --hide-error-context "<all python files (batched)>"`
