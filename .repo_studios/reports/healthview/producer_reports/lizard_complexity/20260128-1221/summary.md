# Lizard Complexity Report

- generated_utc: 2026-01-28T12:21:57.422251+00:00
- status: issues
- targets: C:\Users\genet\repo_studios\.repo_studios
- max cyclomatic complexity: 15
- max function length: 80
- offenders: 10

## Top Offenders

| Rank | Function | Location | CCN (Δ) | Length (Δ) | Recommendation |
|---:|---|---|---:|---:|---|
| 1 | `findViewRequirementIssue` | `C:\Users\genet\repo_studios\.repo_studios\command_center\viewer\ui\viewer.js:610` | 121 (Δ+106) | 226 (Δ+146) | Split into smaller functions and simplify branching. |
| 2 | `run` | `C:\Users\genet\repo_studios\.repo_studios\command_center\scripts\orchestrators\run_docs_health_overview.py:1726` | 31 (Δ+16) | 489 (Δ+409) | Split into smaller functions and simplify branching. |
| 3 | `(anonymous)` | `C:\Users\genet\repo_studios\.repo_studios\command_center\viewer\ui\viewer.js:3163` | 78 (Δ+63) | 62 | Reduce branching or extract helpers to lower CCN. |
| 4 | `(anonymous)` | `C:\Users\genet\repo_studios\.repo_studios\command_center\viewer\ui\viewer.js:3938` | 74 (Δ+59) | 46 | Reduce branching or extract helpers to lower CCN. |
| 5 | `test_quality_metrics_views_coexist_without_state_reset` | `C:\Users\genet\repo_studios\.repo_studios\tests\tests_command_center\viewer\test_quality_metrics_multi_view_coexistence.py:68` | 1 | 382 (Δ+302) | Break the function into smaller units to shorten length. |
| 6 | `_resolve_call_target` | `C:\Users\genet\repo_studios\.repo_studios\command_center\scripts\cc_producers\generate_commandview_inventory.py:1874` | 63 (Δ+48) | 158 (Δ+78) | Split into smaller functions and simplify branching. |
| 7 | `_build_inputs_from_files` | `C:\Users\genet\repo_studios\.repo_studios\command_center\scripts\summarizers\summarize_test_execution_telemetry.py:683` | 57 (Δ+42) | 147 (Δ+67) | Split into smaller functions and simplify branching. |
| 8 | `run` | `C:\Users\genet\repo_studios\.repo_studios\scripts\aggregators\aggregate_docs_health_signals.py:885` | 22 (Δ+7) | 295 (Δ+215) | Split into smaller functions and simplify branching. |
| 9 | `analyze_python_file` | `C:\Users\genet\repo_studios\.repo_studios\command_center\scripts\cc_producers\generate_commandview_inventory.py:2204` | 54 (Δ+39) | 199 (Δ+119) | Split into smaller functions and simplify branching. |
| 10 | `test_code_flow_call_graph_coexists_with_health_overview` | `C:\Users\genet\repo_studios\.repo_studios\tests\tests_command_center\viewer\test_code_flow_multi_view_coexistence.py:57` | 1 | 265 (Δ+185) | Break the function into smaller units to shorten length. |

Additional offenders not shown: 258 (see `telemetry.json` for full list).

## How to Reproduce

```bash
'C:\Users\genet\repo_studios\.venv\Scripts\python.exe' -m lizard -C 15 -L 80 -Ejson -i -1 'C:\Users\genet\repo_studios\.repo_studios'
```

