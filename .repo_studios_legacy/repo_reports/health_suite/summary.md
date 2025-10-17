# Health Suite Summary

Date: 2025-09-09T17:01:01.721052


## Repo Insight — Monkey Patch Trend (preview)

# Monkey Patch Trend Summary

Generated: 2025-09-09T21:01:00Z

## Scans Overview

Showing last 5 scans (most recent last):

| Timestamp | Total | Δ vs prev |
|---|---:|---:|
| 2025-09-09_1555 | 588 | -1262 |
| 2025-09-09_1615 | 588 | +0 |
| 2025-09-09_1637 | 150 | -438 |
| 2025-09-09_1638 | 150 | +0 |
| 2025-09-09_1700 | 152 | +2 |

- 2025-09-09_1537: total=1850
- 2025-09-09_1555: total=588
- 2025-09-09_1615: total=588
- 2025-09-09_1637: total=150
- 2025-09-09_1638: total=150
- 2025-09-09_1700: total=152

## Latest vs Previous

- prev: 2025-09-09_1638
- curr: 2025-09-09_1700

### By Category
| Category | Prev | Curr | Δ |
|---|---:|---:|---:|
| attribute_reassignment_on_import | 132 | 134 | +2 |
| global_env_mutation | 12 | 12 | 0 |
| import_time_side_effect | 4 | 4 | 0 |
| sys_modules_assignment | 2 | 2 | 0 |

### Top import_base increases
| import_base | Prev | Curr | Δ |
|---|---:|---:|---:|
| tomllib | 0 | 2 | +2 |


[Full trend](/.repo_studios/monkey_patch/trend_latest.md)


## Dependency Hygiene — Summary

- unpinned: 16

[Full report](/.repo_studios/dep_health/2025-09-09_1701/report.md)


## Import Graph — Hotspots

### Top fan-in (modules most depended on)
- agents: 5
- api: 4
- jarvis2: 2
- metrics_storage: 2
- tests: 2
- scripts: 1
### Top fan-out (modules with many dependencies)
- agents: 5
- tests: 5
- api: 2
- metrics_storage: 2
- scripts: 2

### Cycles (first 10)

- agents -> tests -> scripts -> api -> agents
- agents -> tests -> scripts -> agents
- agents -> tests -> agents
- agents -> api -> agents
- agents -> tests -> api -> agents
- agents -> metrics_storage -> agents

[Full report](/.repo_studios/import_graph/2025-09-09_1701/report.md)

