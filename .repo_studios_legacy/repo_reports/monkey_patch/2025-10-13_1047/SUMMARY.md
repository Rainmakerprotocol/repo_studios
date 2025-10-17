# Monkey Patch Scan Summary

Date: 2025-10-13T10:47:35.755657


## Totals by Category

- attribute_reassignment_on_import: 158
- global_env_mutation: 15
- import_time_side_effect: 7
- setattr_on_import_or_class: 1
- sys_modules_assignment: 8

## Top Externals Patched

- agents: 17
- api: 17
- os: 15
- sys: 11
- api_cache_shared: 8
- av: 8
- backup: 8
- builtins: 8
- db_storage: 7
- ledger: 6

## Files with Highest Patch Count

- api/cache_impl.py: 17
- conftest.py: 11
- agents/system/diagnostic_agent/__init__.py: 10
- agents/core/monitoring/metrics_storage/backup/system_snapshots.py: 6
- agents/core/monitoring/metrics_storage/cli/backup_commands.py: 5
- scripts/service_start.py: 5
- agents/core/monitoring/metrics_storage/__init__.py: 4
- agents/core/monitoring/metrics_storage/retention/metadata.py: 4
- agents/core/monitoring/metrics_storage/tests/backup/test_step_a_matrix.py: 4
- api/cache/invalidation.py: 4

## Patches Grouped by Package

| Package | Count |
|---|---:|
| agents | 17 |
| api | 17 |
| os | 15 |
| sys | 11 |
| api_cache_shared | 8 |
| av | 8 |
| backup | 8 |
| builtins | 8 |
| db_storage | 7 |
| ledger | 6 |
| scripts | 5 |
| accimage | 4 |
| apscheduler | 4 |
| asyncio | 4 |
| constants | 4 |
| starlette | 4 |
| dashboard | 3 |
| datetime | 3 |
| operations_mod | 3 |
| psutil | 3 |
| storage | 3 |
| time_series | 3 |
| tomllib | 3 |
| PIL | 2 |
| _pytest | 2 |
| chainlit | 2 |
| compat_event_bus | 2 |
| faulthandler | 2 |
| schema | 2 |
| scipy | 2 |
| signal | 2 |
| sphinx | 2 |
| sphinx_gallery | 2 |
| urllib | 2 |
| _load_gpu_decoder | 1 |
| diagnostic_agent | 1 |
| error_metrics | 1 |
| fastapi | 1 |
| fcntl | 1 |
| file_storage | 1 |
| flashlight | 1 |
| jobs | 1 |
| logger | 1 |
| socket | 1 |
| subprocess | 1 |
| system_power | 1 |
| threading | 1 |
| widgets | 1 |
| yaml | 1 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
