# Monkey Patch Trend Summary

Generated: 2025-10-17T11:14:06Z

## Scans Overview

Showing last 5 scans (most recent last):

| Timestamp | Total | Δ vs prev |
|---|---:|---:|
| 2025-10-09_0842 | 179 | +0 |
| 2025-10-10_0622 | 182 | +3 |
| 2025-10-13_0533 | 187 | +5 |
| 2025-10-13_1047 | 189 | +2 |
| 2025-10-15_0600 | 190 | +1 |

- 2025-10-04_1511: total=159
- 2025-10-04_1827: total=162
- 2025-10-09_0624: total=179
- 2025-10-09_0701: total=179
- 2025-10-09_0718: total=179
- 2025-10-09_0842: total=179
- 2025-10-10_0622: total=182
- 2025-10-13_0533: total=187
- 2025-10-13_1047: total=189
- 2025-10-15_0600: total=190

## Latest vs Previous

- prev: 2025-10-13_1047
- curr: 2025-10-15_0600

### By Category
| Category | Prev | Curr | Δ |
|---|---:|---:|---:|
| import_time_side_effect | 7 | 4 | -3 |
| attribute_reassignment_on_import | 158 | 160 | +2 |
| builtins_mutation | 0 | 2 | +2 |
| global_env_mutation | 15 | 15 | 0 |
| setattr_on_import_or_class | 1 | 1 | 0 |
| sys_modules_assignment | 8 | 8 | 0 |

### Policy (non-test only) — By Category
| Category | Prev | Curr | Δ |
|---|---:|---:|---:|
| attribute_reassignment_on_import | 146 | 148 | +2 |
| builtins_mutation | 0 | 2 | +2 |
| global_env_mutation | 7 | 7 | 0 |
| import_time_side_effect | 6 | 3 | -3 |
| setattr_on_import_or_class | 1 | 1 | 0 |
| sys_modules_assignment | 6 | 6 | 0 |

### Top import_base increases
| import_base | Prev | Curr | Δ |
|---|---:|---:|---:|
| importance | 0 | 2 | +2 |
| jobs | 1 | 2 | +1 |
| utils | 0 | 1 | +1 |
| tombstone | 0 | 1 | +1 |
| builtins | 8 | 4 | -4 |

### Files with largest increases
| file | Prev | Curr | Δ |
|---|---:|---:|---:|
| agents/core/monitoring/metrics_storage/retention/cleanup.py | 0 | 2 | +2 |
| agents/core/monitoring/metrics_storage/retention/recovery/integrations.py | 0 | 2 | +2 |
| agents/core/monitoring/metrics_storage/retention/data_query.py | 0 | 2 | +2 |
| agents/core/monitoring/metrics_storage/retention/metadata/api.py | 0 | 2 | +2 |
| agents/core/monitoring/metrics_storage/retention/scheduler_components/worker_pool.py | 0 | 1 | +1 |
| agents/core/monitoring/metrics_storage/model_metrics/batch_metrics/repository.py | 0 | 1 | +1 |
| agents/core/monitoring/metrics_storage/model_metrics/batch_metrics.py | 1 | 0 | -1 |
| agents/core/monitoring/metrics_storage/retention/recovery.py | 2 | 0 | -2 |
| agents/core/monitoring/metrics_storage/retention/scheduler.py | 3 | 1 | -2 |
| agents/core/monitoring/metrics_storage/retention/metadata.py | 4 | 0 | -4 |

