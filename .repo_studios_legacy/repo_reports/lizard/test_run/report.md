# Lizard Complexity Report — test_run

- status: issues- targets: /home/founder/jarvis2/agents /home/founder/jarvis2/api /home/founder/jarvis2/scripts- max cyclomatic complexity: 15- max function length: 80- offenders: 223
## Top Offenders
| Function | File | CCN | Length |
|---|---|---:|---:|
| `enrich_plan_with_commit_window` | `/home/founder/jarvis2/agents/repair/agent.py` | 15 | 82 |
| `subscribe` | `/home/founder/jarvis2/agents/core/messaging/compat_event_bus.py` | 4 | 117 |
| `stream_llama` | `/home/founder/jarvis2/agents/core/ws_backends/llama.py` | 45 | 197 |
| `_pump_loop` | `/home/founder/jarvis2/agents/core/utils/subproc_stream.py` | 17 | 51 |
| `create_test_database` | `/home/founder/jarvis2/agents/core/monitoring/tests/fixtures/db_builder.py` | 9 | 115 |
| `create_html_page` | `/home/founder/jarvis2/agents/core/monitoring/visualization/utils/html_generators.py` | 4 | 245 |
| `create_system_section` | `/home/founder/jarvis2/agents/core/monitoring/visualization/dashboard_sections.py` | 17 | 97 |
| `_compute_series` | `/home/founder/jarvis2/agents/core/monitoring/visualization/resource_charts.py` | 18 | 54 |
| `generate_model_trend_data` | `/home/founder/jarvis2/agents/core/monitoring/visualization/model_performance.py` | 8 | 101 |
| `generate_data` | `/home/founder/jarvis2/agents/core/monitoring/visualization/error_analytics.py` | 9 | 125 |
| `generate_data` | `/home/founder/jarvis2/agents/core/monitoring/visualization/error_analytics.py` | 13 | 131 |
| `_build_template_context` | `/home/founder/jarvis2/agents/core/monitoring/visualization/dashboard.py` | 16 | 41 |
| `_generate_chart_scripts` | `/home/founder/jarvis2/agents/core/monitoring/visualization/dashboard.py` | 22 | 72 |
| `_create_system_section` | `/home/founder/jarvis2/agents/core/monitoring/visualization/dashboard.py` | 16 | 108 |
| `compute_next_run` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/backup/operations_mod/schedule.py` | 18 | 78 |
| `test_cleanup` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/tests/storage/test_db_storage.py` | 3 | 87 |
| `test_file_io_single_and_batch_and_errors` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/tests/retention/test_cli.py` | 10 | 81 |
| `get_time_series_collection` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/db_storage/time_series.py` | 11 | 87 |
| `_setup_aggregation_tables` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/db_storage/aggregation.py` | 1 | 172 |
| `aggregate_model_metrics` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/db_storage/aggregation.py` | 7 | 118 |
| `aggregate_system_metrics` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/db_storage/aggregation.py` | 7 | 114 |
| `aggregate_time_series` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/db_storage/aggregation.py` | 9 | 175 |
| `_cleanup_aggregated_data` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/db_storage/aggregation.py` | 3 | 104 |
| `build_error_query` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/db_storage/query_builder.py` | 9 | 83 |
| `build_time_series_query` | `/home/founder/jarvis2/agents/core/monitoring/metrics_storage/db_storage/query_builder.py` | 8 | 81 |

## How to Reproduce
```bash/home/founder/miniconda3/bin/python -m lizard -C 15 -L 80 /home/founder/jarvis2/agents /home/founder/jarvis2/api /home/founder/jarvis2/scripts``
