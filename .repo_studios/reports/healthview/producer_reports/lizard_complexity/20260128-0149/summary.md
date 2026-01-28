# Lizard Complexity Report

- generated_utc: 2026-01-28T01:49:13.122896+00:00
- status: issues
- targets: C:\Users\genet\repo_studios\.repo_studios\scripts\producers
- max cyclomatic complexity: 15
- max function length: 80
- offenders: 10

## Top Offenders

| Rank | Function | Location | CCN (Δ) | Length (Δ) | Recommendation |
|---:|---|---|---:|---:|---|
| 1 | `run` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_lizard_report.py:626` | 27 (Δ+12) | 248 (Δ+168) | Split into smaller functions and simplify branching. |
| 2 | `run` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_test_coverage_inventory.py:805` | 34 (Δ+19) | 226 (Δ+146) | Split into smaller functions and simplify branching. |
| 3 | `main` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_typecheck_report.py:881` | 32 (Δ+17) | 217 (Δ+137) | Split into smaller functions and simplify branching. |
| 4 | `_write_artifacts` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\collect_test_log_reports.py:424` | 28 (Δ+13) | 190 (Δ+110) | Split into smaller functions and simplify branching. |
| 5 | `run` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_anchor_inventory.py:915` | 25 (Δ+10) | 175 (Δ+95) | Split into smaller functions and simplify branching. |
| 6 | `render_summary_markdown` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\scan_monkey_patches.py:1414` | 32 (Δ+17) | 157 (Δ+77) | Split into smaller functions and simplify branching. |
| 7 | `render_markdown` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_anchor_inventory.py:623` | 32 (Δ+17) | 134 (Δ+54) | Split into smaller functions and simplify branching. |
| 8 | `run` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_doc_index.py:1108` | 7 | 159 (Δ+79) | Break the function into smaller units to shorten length. |
| 9 | `main` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_import_graph_report.py:601` | 6 | 157 (Δ+77) | Break the function into smaller units to shorten length. |
| 10 | `run` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_undocumented_logic_report.py:833` | 13 | 156 (Δ+76) | Break the function into smaller units to shorten length. |

Additional offenders not shown: 36 (see `telemetry.json` for full list).

## How to Reproduce

```bash
'C:\Users\genet\repo_studios\.venv\Scripts\python.exe' -m lizard -C 15 -L 80 -Ejson -i -1 'C:\Users\genet\repo_studios\.repo_studios\scripts\producers'
```

