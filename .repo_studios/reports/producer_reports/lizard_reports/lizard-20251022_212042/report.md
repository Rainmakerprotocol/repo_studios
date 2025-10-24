# Lizard Complexity Report

- generated_utc: 2025-10-22T21:20:42.446269+00:00
- status: issues
- targets: C:\Users\genet\repo_studios\.repo_studios\scripts\producers
- max cyclomatic complexity: 15
- max function length: 80
- offenders: 7

## Top Offenders

| Function | File | CCN | Length |
|---|---|---:|---:|
| `main` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\generate_typecheck_report.py` | 13 | 82 |
| `visit_Call` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\scan_monkey_patches.py` | 20 | 63 |
| `_handle_assignment` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\scan_monkey_patches.py` | 28 | 91 |
| `write_reports` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\scan_monkey_patches.py` | 14 | 99 |
| `main` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\scan_monkey_patches.py` | 12 | 95 |
| `_scan_static_imports` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\validate_import_boundaries.py` | 17 | 71 |
| `main` | `C:\Users\genet\repo_studios\.repo_studios\scripts\producers\validate_markdown_anchors.py` | 8 | 83 |

## How to Reproduce

```bash
'C:\Users\genet\repo_studios\.venv\Scripts\python.exe' -m lizard -C 15 -L 80 -Ejson -i -1 'C:\Users\genet\repo_studios\.repo_studios\scripts\producers'
```
