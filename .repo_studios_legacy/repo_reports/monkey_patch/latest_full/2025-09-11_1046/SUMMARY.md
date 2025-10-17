# Monkey Patch Scan Summary

Date: 2025-09-11T10:46:07.462809


## Totals by Category

- attribute_reassignment_on_import: 110
- global_env_mutation: 10
- import_time_side_effect: 2
- sys_modules_assignment: 2

## Top Externals Patched

- api: 12
- os: 10
- storage: 9
- api_cache_shared: 8
- av: 8
- backup: 8
- db_storage: 8
- ledger: 6
- accimage: 4
- apscheduler: 4

## Files with Highest Patch Count

- agents/core/monitoring/metrics_storage/database_metrics_storage.py: 13
- api/cache_impl.py: 13
- agents/core/monitoring/metrics_storage/backup/system_snapshots.py: 6
- agents/core/monitoring/metrics_storage/cli/backup_commands.py: 5
- agents/core/monitoring/metrics_storage/__init__.py: 4
- agents/core/monitoring/metrics_storage/tests/backup/test_step_a_matrix.py: 4
- scripts/maintenance_orchestrator.py: 4
- tests/api/test_events_sse.py: 4
- agents/core/monitoring/metrics_storage/base.py: 3
- agents/core/monitoring/visualization/__init__.py: 3

## Patches Grouped by Package

| Package | Count |
|---|---:|
| api | 12 |
| os | 10 |
| storage | 9 |
| api_cache_shared | 8 |
| av | 8 |
| backup | 8 |
| db_storage | 8 |
| ledger | 6 |
| accimage | 4 |
| apscheduler | 4 |
| constants | 4 |
| sys | 4 |
| dashboard | 3 |
| operations_mod | 3 |
| psutil | 3 |
| time_series | 3 |
| PIL | 2 |
| chainlit | 2 |
| scipy | 2 |
| sphinx | 2 |
| sphinx_gallery | 2 |
| tomllib | 2 |
| urllib | 2 |
| _load_gpu_decoder | 1 |
| _pytest | 1 |
| fastapi | 1 |
| faulthandler | 1 |
| fcntl | 1 |
| file_storage | 1 |
| flashlight | 1 |
| jobs | 1 |
| query | 1 |
| subprocess | 1 |
| system_power | 1 |
| websockets | 1 |
| widgets | 1 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
