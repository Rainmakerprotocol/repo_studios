# Typecheck Report

- generated_utc: 2025-12-17T14:27:41.043482+00:00
- status: error
- mypy_version: mypy 1.11.1 (compiled: no)
- bundle_dir: C:\Users\genet\repo_studios\.repo_studios\reports\producer_reports\healthview\typecheck_report\20251217-1427

## Summary

| Metric | Value |
|---|---:|
| error_count | 3 |
| files_with_issues | 1 |
| paths_checked | 1 |

## Sample Errors

- tmp_generate_lizard_report_new.py:147 — [arg-type] Argument 1 to "Path" has incompatible type "str | None"; expected "str | PathLike[str]"
- tmp_generate_lizard_report_new.py:606 — [assignment] Incompatible types in assignment (expression has type "WriteReportArtifactsResult", variable has type "CompletedProcess[str]")
- tmp_generate_lizard_report_new.py:613 — [attr-defined] "CompletedProcess[str]" has no attribute "run_dir"

## Invocation

`C:\Python313\python.exe -m mypy --show-error-codes --no-color-output --hide-error-context .`
