# Typecheck Report

- generated_utc: 2026-01-24T13:43:12.091780+00:00
- status: error
- mypy_version: mypy 1.11.1 (compiled: no)
- bundle_dir: C:\Users\genet\repo_studios\.repo_studios\reports\healthview\producer_reports\typecheck_report\20260124-1343

## Summary

| Metric | Value |
|---|---:|
| error_count | 149 |
| files_with_issues | 30 |
| files_checked | 85 |
| paths_checked | 2 |

## Sample Errors

- .repo_studios\command_center\scripts\libraries\summarizer_runner.py:31 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\command_center\scripts\libraries\summarizer_runner.py:31 — [no-any-return] Returning Any from function declared to return "Callable[[Iterable[str] | None], int]"
- .repo_studios\command_center\scripts\libraries\guardrails.py:10 — [import-untyped] Skipping analyzing "command_center.scripts.utilities": module is installed, but missing library stubs or py.typed marker
- .repo_studios\command_center\scripts\libraries\guardrails.py:198 — [no-any-return] Returning Any from function declared to return "dict[str, object]"
- .repo_studios\command_center\scripts\utilities\reports_naming_audit.py:344 — [attr-defined] "object" has no attribute "items"
- .repo_studios\command_center\scripts\utilities\reports_naming_audit.py:353 — [attr-defined] "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)
- .repo_studios\command_center\scripts\utilities\reports_naming_audit.py:366 — [attr-defined] "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)
- .repo_studios\command_center\scripts\utilities\reports_naming_audit.py:375 — [attr-defined] "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)
- .repo_studios\command_center\scripts\utilities\reports_naming_audit.py:428 — [attr-defined] "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable)
- .repo_studios\command_center\scripts\utilities\reports_naming_audit.py:430 — [call-overload] No overload variant of "int" matches argument type "object"
- .repo_studios\command_center\scripts\utilities\reports_naming_audit.py:441 — [call-overload] No overload variant of "int" matches argument type "object"
- .repo_studios\command_center\scripts\utilities\reports_naming_audit.py:442 — [call-overload] No overload variant of "int" matches argument type "object"
- .repo_studios\command_center\scripts\utilities\list_db_markers.py:63 — [var-annotated] Need type annotation for "markers" (hint: "markers: list[<type>] = ...")
- .repo_studios\command_center\scripts\libraries\retention_policy.py:180 — [no-any-return] Returning Any from function declared to return "int"
- .repo_studios\scripts\utilities\validate_healthview_agent_workflow_spec.py:21 — [import-untyped] Library stubs not installed for "jsonschema"
- .repo_studios\scripts\utilities\validate_healthview_agent_workflow_spec.py:30 — [unused-ignore] Unused "type: ignore" comment
- .repo_studios\scripts\utilities\fault_run_analysis.py:136 — [no-any-return] Returning Any from function declared to return "dict[str, object]"
- .repo_studios\scripts\utilities\fault_run_analysis.py:139 — [var-annotated] Need type annotation for "manifest"
- .repo_studios\scripts\utilities\fault_run_analysis.py:153 — [return-value] Incompatible return value type (got "dict[str, dict[Any, Any] | str | None]", expected "dict[str, object]")
- .repo_studios\scripts\utilities\fault_run_analysis.py:205 — [no-any-return] Returning Any from function declared to return "str"

## Invocation

`C:\Users\genet\repo_studios\.venv\Scripts\python.exe -m mypy --show-error-codes --no-color-output --hide-error-context .repo_studios/scripts .repo_studios/command_center/scripts`
