# Typecheck Report

- generated_utc: 2025-10-23T01:45:00+00:00
- status: error
- mypy_version: mypy 1.18.2 (compiled: yes)
- output_dir: C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\typecheck_reports

## Summary

| Metric | Value |
|---|---:|
| error_count | 50 |
| files_with_issues | 18 |
| paths_checked | 1 |

## Sample Errors

- .repo_studios\scripts\summarizers\summarize_health_suite.py:104 — [call-overload] No overload variant of "int" matches argument type "object"
- .repo_studios\scripts\producers\validate_inventory.py:20 — [import-untyped] Library stubs not installed for "yaml"
- .repo_studios\scripts\producers\validate_inventory.py:196 — [arg-type] Argument 2 to "ensure" of "EnumRegistry" has incompatible type "list[Any | None]"; expected "Iterable[str]"
- .repo_studios\scripts\producers\validate_inventory.py:196 — [arg-type] Argument 5 to "ensure" of "EnumRegistry" has incompatible type "Any | None"; expected "str"
- .repo_studios\scripts\producers\validate_inventory.py:199 — [arg-type] Argument 5 to "ensure" of "EnumRegistry" has incompatible type "Any | None"; expected "str"
- .repo_studios\scripts\producers\validate_inventory.py:201 — [arg-type] Argument 5 to "ensure" of "EnumRegistry" has incompatible type "Any | None"; expected "str"
- .repo_studios\scripts\producers\render_inventory_views.py:12 — [import-untyped] Library stubs not installed for "yaml"
- .repo_studios\scripts\producers\extract_standards_rules.py:243 — [arg-type] Argument "summary" to "ParsedRule" has incompatible type "str | None"; expected "str"
- .repo_studios\scripts\producers\extract_standards_rules.py:244 — [arg-type] Argument "rationale" to "ParsedRule" has incompatible type "str | None"; expected "str"
- .repo_studios\scripts\producers\extract_standards_rules.py:245 — [union-attr] Item "None" of "str | None" has no attribute "lower"
- .repo_studios\scripts\producers\extract_standards_rules.py:246 — [list-item] List item 0 has incompatible type "str | None"; expected "str"
- .repo_studios\scripts\utilities\configure_faulthandler_runtime.py:115 — [attr-defined] Module has no attribute "flock"
- .repo_studios\scripts\utilities\configure_faulthandler_runtime.py:115 — [attr-defined] Module has no attribute "LOCK_EX"
- .repo_studios\scripts\utilities\configure_faulthandler_runtime.py:124 — [attr-defined] Module has no attribute "flock"
- .repo_studios\scripts\utilities\configure_faulthandler_runtime.py:124 — [attr-defined] Module has no attribute "LOCK_UN"
- .repo_studios\scripts\utilities\configure_faulthandler_runtime.py:179 — [attr-defined] Module has no attribute "register"
- .repo_studios\scripts\summarizers\summarize_standards.py:55 — [type-var] Value of type variable "SupportsRichComparisonT" of "sorted" cannot be "Any | None"
- .repo_studios\scripts\summarizers\summarize_standards.py:60 — [arg-type] Argument 1 to "join" of "str" has incompatible type "list[Any | None]"; expected "Iterable[str]"
- .repo_studios\scripts\producers\seed_standards_prompts.py:29 — [import-untyped] Library stubs not installed for "yaml"
- .repo_studios\scripts\producers\scan_monkey_patches.py:545 — [assignment] Incompatible types in assignment (expression has type "str | None", variable has type "str")

## Invocation

`C:\Users\genet\repo_studios\.venv\Scripts\python.exe -m mypy --show-error-codes --no-color-output --hide-error-context .repo_studios/scripts`
