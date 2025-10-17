# Test Log Health Report

Generated: 2025-10-17T07:15:09.858502


## Summary

- total: 1446, passed: 1417, skipped: 26, xfailed: 0, failed: 3, errors: 0

- warnings_total: 2, tracebacks: 0


## Warnings by Type

| Type | Count |
|---|---:|

| PytestAssertRewriteWarning | 1 |

| RuntimeWarning | 1 |


## Top Warning Files

| File | Count |
|---|---:|

| /mnt/jarvis2/.venv/lib/python3.11/site-packages/_pytest/config/__init__.py | 1 |

| <frozen runpy> | 1 |


## Slowest Tests

| Seconds | Test |
|---:|---|

| 10.24 | .repo_studios/tests/test_health_suite_orchestrator.py::test_orchestrator_includes_typecheck_step |

| 9.42 | tests/api/test_model_selection_histogram_and_endpoint.py::test_model_selection_dedicated_endpoint_and_histogram_lines |

| 7.88 | tests/api/test_eventbus_metrics_exposure.py::test_eventbus_metrics_increments_with_publish_and_sse |

| 6.64 | tests/lint/test_no_cache_impl_imports.py::test_no_imports_of_api_cache_impl |

| 6.25 | tests/api/test_ws_chat.py::test_ws_chat_auth_enforced_when_api_key_set |

| 6.04 | tests/agents/service_management/test_service_start_metrics_tier.py::test_api_start_metrics_tier_probes_and_debug_logging |

| 6.02 | tests/agents/service_management/test_service_start_probe_metrics_exposition.py::test_api_start_probe_metrics_exposed |

| 5.72 | tests/agents/service_management/test_service_start_shutdown_snapshot.py::test_shutdown_timeout_warning |

| 4.06 | tests/agents/service_management/test_restart_wrapper.py::test_restart_giveup |

| 3.56 | tests/api/test_ws_chat.py::test_ws_chat_backpressure_many_small_deltas_when_low_threshold |

| 3.54 | tests/api/test_ws_chat.py::test_ws_chat_backpressure_fewer_deltas_when_large_threshold |

| 3.32 | tests/api/test_ws_chat_contract_fake.py::test_ws_fake_idle_soft_emits_once |

| 3.30 | tests/test_perf_thresholds.py::test_perf_thresholds |

| 3.20 | tests/api/test_ws_chat.py::test_ws_chat_stream_happy_path |

| 3.20 | tests/api/test_ws_chat_contract_fake.py::test_ws_fake_happy_path_ack_delta_done |

| 3.19 | tests/api/test_ws_chat_contract_fake.py::test_ws_fake_done_contains_elapsed_and_usage |

| 2.66 | tests/api/test_model_selection_metrics_exposure.py::test_model_selection_metrics_exposed_when_chat_autoselects |

| 2.65 | tests/api/test_model_selection_histogram_and_endpoint.py::test_model_selection_histogram_lines_present_in_metrics |

| 2.26 | tests/integration/test_storage_health_rules_hash.py::test_storage_health_exposes_rules_hash_and_detail |

| 2.18 | tests/agents/repair/test_repair_orchestrator_tight_loop.py::test_orchestrator_runs_repair_agent_and_updates_snapshot |

| 1.87 | tests/agents/service_management/test_service_start_misc_flags.py::test_api_start_timeout_simulated_delay |

| 1.82 | tests/api/test_ws_chat.py::test_ws_chat_idle_and_session_timeout_paths |

| 1.80 | tests/systemd/test_watchdog_status_updates.py::test_status_emits_periodically |

| 1.77 | tests/agents/service_management/test_service_start_shutdown_snapshot.py::test_shutdown_snapshot_written |

| 1.74 | tests/agents/service_management/test_restart_wrapper.py::test_restart_wrapper_recovers |
