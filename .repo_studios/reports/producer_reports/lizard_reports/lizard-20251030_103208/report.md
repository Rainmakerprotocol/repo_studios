# Lizard Complexity Report

- generated_utc: 2025-10-30T10:32:08.733281+00:00
- status: issues
- targets: C:\Users\genet\repo_studios\.repo_studios\scripts
- max cyclomatic complexity: 15
- max function length: 80
- offenders: 10

## Top Offenders

| Rank | Function | Location | CCN (Δ) | Length (Δ) | Recommendation |
|---:|---|---|---:|---:|---|
| 1 | `main` | `C:\Users\genet\repo_studios\.repo_studios\scripts\orchestrators\run_pytest_log_capture.py:376` | 54 (Δ+39) | 258 (Δ+178) | Split into smaller functions and simplify branching. |
| 2 | `make_steps` | `C:\Users\genet\repo_studios\.repo_studios\scripts\orchestrators\orchestrate_health_suite.py:78` | 21 (Δ+6) | 288 (Δ+208) | Split into smaller functions and simplify branching. |
| 3 | `run_step` | `C:\Users\genet\repo_studios\.repo_studios\scripts\orchestrators\orchestrate_health_suite.py:368` | 27 (Δ+12) | 181 (Δ+101) | Split into smaller functions and simplify branching. |
| 4 | `main` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_lizard_report.py:567` | 26 (Δ+11) | 179 (Δ+99) | Split into smaller functions and simplify branching. |
| 5 | `_handle_assignment` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\scan_monkey_patches.py:559` | 28 (Δ+13) | 91 (Δ+11) | Split into smaller functions and simplify branching. |
| 6 | `run_pytest_and_capture` | `C:\Users\genet\repo_studios\.repo_studios\scripts\orchestrators\run_pytest_log_capture.py:94` | 26 (Δ+11) | 116 (Δ+36) | Split into smaller functions and simplify branching. |
| 7 | `main` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\check_inventory_health.py:299` | 3 | 110 (Δ+30) | Break the function into smaller units to shorten length. |
| 8 | `visit_Call` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\scan_monkey_patches.py:449` | 20 (Δ+5) | 63 | Reduce branching or extract helpers to lower CCN. |
| 9 | `main` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_typecheck_report.py:378` | 9 | 105 (Δ+25) | Break the function into smaller units to shorten length. |
| 10 | `main` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\diff_standards_index.py:463` | 10 | 102 (Δ+22) | Break the function into smaller units to shorten length. |

Additional offenders not shown: 12 (see `report.json` for full list).

## How to Reproduce

```bash
'C:\Users\genet\repo_studios\.venv\Scripts\python.exe' -m lizard -C 15 -L 80 -Ejson -i -1 'C:\Users\genet\repo_studios\.repo_studios\scripts'
```
