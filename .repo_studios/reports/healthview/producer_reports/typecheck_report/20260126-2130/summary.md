# Typecheck Report

- generated_utc: 2026-01-26T21:30:19.631088+00:00
- status: error
- mypy_version: mypy 1.11.1 (compiled: no)
- bundle_dir: C:\Users\genet\repo_studios\.repo_studios\reports\healthview\producer_reports\typecheck_report\20260126-2130

## Summary

| Metric | Value |
|---|---:|
| error_count | 465 |
| files_with_issues | 84 |
| files_checked | 260 |
| files_checked_command_center | 48 |
| files_checked_repo_studios | 212 |
| paths_checked | 1 |

## Sample Errors

- .repo_studios\tests\tests_producers\test_verify_docs_integrity.py:23 — [name-defined] Name "module.dt.tzinfo" is not defined
- .repo_studios\tests\tests_producers\test_verify_docs_integrity.py:23 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_producers\test_verify_docs_integrity.py:56 — [arg-type] Argument 2 to "_render_json_block" has incompatible type "dict[str, list[dict[str, object]]]"; expected "dict[str, object]"
- .repo_studios\tests\tests_producers\test_validate_metrics_anchor_stubs.py:23 — [name-defined] Name "module.dt.tzinfo" is not defined
- .repo_studios\tests\tests_producers\test_validate_metrics_anchor_stubs.py:23 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_producers\test_validate_inventory.py:22 — [unused-ignore] Unused "type: ignore" comment
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
- .repo_studios\tests\tests_producers\test_generate_function_analysis.py:75 — [no-any-return] Returning Any from function declared to return "dict[Any, Any]"
- .repo_studios\tests\tests_producers\test_generate_code_doc_churn_report.py:17 — [arg-type] Argument 1 to "module_from_spec" has incompatible type "ModuleSpec | None"; expected "ModuleSpec"
- .repo_studios\tests\tests_producers\test_generate_code_doc_churn_report.py:18 — [union-attr] Item "None" of "ModuleSpec | None" has no attribute "loader"

## Invocation

`C:\Users\genet\repo_studios\.venv\Scripts\python.exe -m mypy --show-error-codes --no-color-output --hide-error-context "<all python files (batched)>"`
