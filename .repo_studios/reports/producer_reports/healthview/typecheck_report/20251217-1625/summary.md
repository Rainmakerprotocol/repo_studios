# Typecheck Report

- generated_utc: 2025-12-17T16:25:38.474969+00:00
- status: error
- mypy_version: mypy 1.11.1 (compiled: no)
- bundle_dir: C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\healthview\typecheck_report\20251217-1625

## Summary

| Metric | Value |
|---|---:|
| error_count | 765 |
| files_with_issues | 145 |
| files_checked | 250 |
| files_checked_command_center | 44 |
| files_checked_repo_studios | 206 |
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
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:78 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:79 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:80 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:93 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:127 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:128 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:166 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\orchestrators\test_orchestrate_full_diagnostic.py:167 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\tests\tests_command_center\monkey_patch\helpers.py:51 — [arg-type] Argument 1 to "module_from_spec" has incompatible type "ModuleSpec | None"; expected "ModuleSpec"
- .repo_studios\tests\tests_aggregators\test_generate_churn_complexity_heatmap.py:18 — [arg-type] Argument 1 to "module_from_spec" has incompatible type "ModuleSpec | None"; expected "ModuleSpec"
- .repo_studios\tests\tests_aggregators\test_generate_churn_complexity_heatmap.py:19 — [union-attr] Item "None" of "ModuleSpec | None" has no attribute "loader"
- .repo_studios\tests\tests_aggregators\test_generate_churn_complexity_heatmap.py:21 — [union-attr] Item "None" of "ModuleSpec | None" has no attribute "loader"

## Invocation

`C:\Python313\python.exe -m mypy --show-error-codes --no-color-output --hide-error-context "<all python files (batched)>"`
