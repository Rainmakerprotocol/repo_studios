# Health Suite Summary

Date: 2025-10-09T08:35:05.639673

## Anchor Health — Top-Level Markdown Slugs

- strict duplicate count: 50
- baseline (cross_file_duplicates): 60
- delta vs baseline: -10

### Largest Remaining Duplicate Slugs (top 10)

- `references` — 9 files
- `open-questions` — 7 files
- `purpose` — 7 files
- `intent` — 5 files
- `rationale` — 5 files
- `see-also` — 5 files
- `alternatives-considered` — 4 files
- `context` — 4 files
- `decision` — 4 files
- `examples` — 4 files

[Full anchor report](/.repo_studios/anchor_health/anchor_health-2025-10-09_1118/anchor_report.md)

## Fault Handler — Trends

- fault_dumps_total: 0.0 →
- unique_signatures_count: 0.0 →
- top_signature_repeat_count: 0.0 →
- dump_rate_per_minute: 0.0 →

[All runs](/.repo_studios/health/faulthandler/trends.json)

## Repo Insight — Monkey Patch Trend (preview)

> # Monkey Patch Trend Summary
>
> Generated: 2025-10-09T11:18:48Z
>
> ## Scans Overview
>
> Showing last 5 scans (most recent last):
>
> | Timestamp | Total | Δ vs prev |
> |---|---:|---:|
> | 2025-10-04_1511 | 159 | +1 |
> | 2025-10-04_1827 | 162 | +3 |
> | 2025-10-09_0624 | 179 | +17 |
> | 2025-10-09_0701 | 179 | +0 |
> | 2025-10-09_0718 | 179 | +0 |
>
> - 2025-09-29_1620: total=156
> - 2025-10-02_1921: total=158
> - 2025-10-02_1930: total=158
> - 2025-10-04_1511: total=159
> - 2025-10-04_1827: total=162
> - 2025-10-09_0624: total=179
> - 2025-10-09_0701: total=179
> - 2025-10-09_0718: total=179
>
> ## Latest vs Previous
>
> - prev: 2025-10-09_0701
> - curr: 2025-10-09_0718
>
> ### By Category
> | Category | Prev | Curr | Δ |
> |---|---:|---:|---:|
> | attribute_reassignment_on_import | 150 | 150 | 0 |
> | global_env_mutation | 15 | 15 | 0 |
> | import_time_side_effect | 7 | 7 | 0 |
> | sys_modules_assignment | 7 | 7 | 0 |
>
> ### Policy (non-test only) — By Category
> | Category | Prev | Curr | Δ |

[Full trend](/.repo_studios/monkey_patch/trend_latest.md)

## Dependency Hygiene — Summary

- No issues detected.

[Full report](/.repo_studios/dep_health/2025-10-09_0718/report.md)

## Import Graph — Hotspots

### Top fan-in (modules most depended on)

- agents: 5
- api: 4
- scripts: 3
- jarvis2: 2
- metrics_storage: 2
- tests: 2

### Top fan-out (modules with many dependencies)

- agents: 5
- tests: 5
- api: 3
- scripts: 3
- metrics_storage: 2

### Cycles (first 10)

- None detected

[Full report](/.repo_studios/import_graph/2025-10-09_0718/report.md)

## Test Log Health — Summary

- total: 1260, passed: 1230, skipped: 27, xfailed: 0, failed: 3, errors: 0
- warnings_total: 2, tracebacks: 0

[Full report](/.repo_studios/test_health/2025-10-09_0718/report.md)

## Typecheck — Summary

- status: ERROR
- total errors: 1242
- files with issues: 166

### Top Issues (up to 10)

- api/cache/invalidation.py:110 — [attr-defined] Module "api_cache_shared" has no attribute "NEGATIVE_PATHS_SHARED"
- agents/core/monitoring/exceptions.py:164 — [union-attr] Item "None" of "FrameType | None" has no attribute "f_back"
- api/metrics_range.py:80 — [arg-type] Argument 1 to "int" has incompatible type "float | int | Any | dict[Any, Any]"; expected "str | Buffer | SupportsInt | SupportsIndex | SupportsTrunc"
- api/metrics_range.py:82 — [arg-type] Argument 1 to "append" of "list" has incompatible type "float | int | Any | dict[Any, Any]"; expected "float"
- api/chat_logging.py:258 — [assignment] Incompatible types in assignment (expression has type "dict[str, Any | None]", target has type "str")
- api/chat_logging.py:324 — [dict-item] Dict entry 0 has incompatible type "str": "Any | None"; expected "str": "str"
- api/chat_logging.py:325 — [dict-item] Dict entry 1 has incompatible type "str": "Any | None"; expected "str": "str"
- api/chat_logging.py:326 — [dict-item] Dict entry 2 has incompatible type "str": "Any | None"; expected "str": "str"
- agents/system/diagnostic_agent/__init__.py:62 — [misc] Cannot assign to a type
- agents/system/diagnostic_agent/__init__.py:63 — [misc] Cannot assign to a type

[Full report](/.repo_studios/typecheck/now/report.md)

## Lizard Complexity — Summary

- status: issues
- offenders: 223
- targets: agents api scripts
- thresholds: CCN ≤ 15, length ≤ 80

### Top Offenders (up to 10)

| Function | File | CCN | Length |
|---|---|---:|---:|
| `dispatch` | `api/cache/middleware.py` | 169 | 496 |
| `dispatch` | `api/cache_impl.py` | 140 | 420 |
| `build_cache_metrics_lines` | `api/metrics/exposition/cache.py` | 125 | 805 |
| `_cycle_sidebar` | `agents/interface/chainlit/refresh_loop.py` | 108 | 296 |
| `get_cache_stats` | `api/cache_impl.py` | 63 | 263 |
| `build_orchestrator_metrics_lines` | `api/metrics/exposition/orchestrator.py` | 54 | 250 |
| `_select_model` | `api/routers/chat.py` | 51 | 230 |
| `chat` | `api/routers/chat.py` | 46 | 327 |
| `main` | `scripts/health/faulthandler_pr_owner_signal.py` | 46 | 146 |
| `chat_retry` | `api/routers/chat.py` | 45 | 282 |

[Full report](/.repo_studios/lizard/test_run/report.md)

## Churn × Complexity — Top (up to 10)

| File | Churn | Complexity | Failures | Score |
|---|---:|---:|---:|---:|
| agents/interface/chainlit/main.py | 5 | 447 | 0 | 10.9383 |
| api/routers/ui/handlers.py | 8 | 101 | 0 | 10.1621 |
| api/ui_data.py | 8 | 81 | 0 | 9.6826 |
| api/cache_impl.py | 3 | 475 | 0 | 8.5471 |
| api/routers/events.py | 4 | 123 | 0 | 7.7579 |
| scripts/service_start/watchdog.py | 4 | 108 | 0 | 7.5504 |
| scripts/service_start/orchestrator_main.py | 4 | 97 | 0 | 7.3792 |
| api/cache/middleware.py | 3 | 190 | 0 | 7.2812 |
| scripts/service_start.py | 5 | 54 | 0 | 7.1802 |
| conftest.py | 3 | 168 | 0 | 7.1115 |

[Full heatmap](/.repo_studios/churn_complexity/2025-10-09_0718/heatmap.md)
