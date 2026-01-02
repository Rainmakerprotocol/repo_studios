# Typecheck Report

- generated_utc: 2026-01-02T04:20:18.084866+00:00
- status: error
- mypy_version: mypy 1.11.1 (compiled: no)
- bundle_dir: C:\Users\genet\repo_studios\.repo_studios\reports\healthview\producer_reports\typecheck_report\20260102-0420

## Summary

| Metric | Value |
|---|---:|
| error_count | 713 |
| files_with_issues | 135 |
| files_checked | 258 |
| files_checked_command_center | 46 |
| files_checked_repo_studios | 212 |
| paths_checked | 1 |

## Sample Errors

- .repo_studios\docs\pipeline\checkbox_report\test_checkbox_report.py:12 — [arg-type] Argument 1 to "module_from_spec" has incompatible type "ModuleSpec | None"; expected "ModuleSpec"
- .repo_studios\docs\pipeline\checkbox_report\test_checkbox_report.py:14 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\docs\pipeline\checkbox_report\test_checkbox_report.py:14 — [union-attr] Item "None" of "ModuleSpec | None" has no attribute "loader"
- .repo_studios\docs\pipeline\checkbox_report\test_checkbox_report.py:14 — [union-attr] Item "None" of "Loader | Any | None" has no attribute "exec_module"
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:37 — [attr-defined] Module has no attribute "VIEWER_SLUG"
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:38 — [attr-defined] Module has no attribute "TOPIC_SLUG"
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:39 — [attr-defined] Module has no attribute "HEALTHVIEW_TOPIC"
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:40 — [attr-defined] Module has no attribute "_calls"
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:79 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:80 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:81 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:96 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:131 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:132 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:171 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:172 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\monkey_patch\helpers.py:51 — [arg-type] Argument 1 to "module_from_spec" has incompatible type "ModuleSpec | None"; expected "ModuleSpec"
- .repo_studios\tests\tests_aggregators\test_generate_churn_complexity_heatmap.py:18 — [arg-type] Argument 1 to "module_from_spec" has incompatible type "ModuleSpec | None"; expected "ModuleSpec"
- .repo_studios\tests\tests_aggregators\test_generate_churn_complexity_heatmap.py:19 — [union-attr] Item "None" of "ModuleSpec | None" has no attribute "loader"
- .repo_studios\tests\tests_aggregators\test_generate_churn_complexity_heatmap.py:21 — [union-attr] Item "None" of "ModuleSpec | None" has no attribute "loader"

## Invocation

`C:\Users\genet\repo_studios\.venv\Scripts\python.exe -m mypy --show-error-codes --no-color-output --hide-error-context "<all python files (batched)>"`
