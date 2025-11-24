# Project Tree Overview

This document is refreshed automatically by `run_batch_cleanup.py`. Edits outside the tree block are preserved, but avoid modifying the block between the markers.

<!-- tree:begin -->
Updated: 11/24/2025_22:53:25

```text
repo_studios/
├── pytest.ini
├── README.md
├── .repo_studios/
│   ├── agent_notes/
│   │   ├── _templates/
│   │   ├── automation/
│   │   ├── inventory/
│   │   ├── meta/
│   │   ├── scripts/
│   │   └── tests/
│   ├── command_center/
│   │   ├── checklists/
│   │   ├── docs/
│   │   │   ├── code_library/
│   │   │   ├── guardrails/
│   │   │   ├── mermaid/
│   │   │   ├── metrics/
│   │   │   ├── phase_4/
│   │   │   ├── phase_5/
│   │   │   ├── phase_6/
│   │   │   └── phase_7/
│   │   ├── reports/
│   │   │   ├── automation_metrics_demo/
│   │   │   ├── duplicates_scan/
│   │   │   ├── index_scan/
│   │   │   ├── index_scan_analysis/
│   │   │   └── repo-studios__command-center__automation_run/
│   │   ├── scripts/
│   │   │   ├── aggregators/
│   │   │   ├── libraries/
│   │   │   ├── orchestrators/
│   │   │   ├── producers/
│   │   │   ├── scripts_index/
│   │   │   └── summarizers/
│   │   └── viewer/
│   │       ├── cache/
│   │       └── ui/
│   ├── config/
│   ├── docs/
│   │   ├── automation/
│   │   │   └── traceability/
│   │   ├── governance/
│   │   ├── inventory/
│   │   ├── playbooks/
│   │   ├── schemas/
│   │   ├── standards/
│   │   │   ├── global/
│   │   │   └── project/
│   │   └── templates/
│   ├── inventory_schema/
│   │   ├── scripts/
│   │   ├── tests/
│   │   └── views/
│   ├── monkey_patch/
│   │   ├── 20251124_175233/
│   │   └── latest/
│   ├── reports/
│   │   ├── aggregator_reports/
│   │   │   ├── churn_complexity_heatmap/
│   │   │   ├── churn_complexity_heatmap_reports/
│   │   │   ├── monkey_patch_trends/
│   │   │   └── monkey_patch_trends_reports/
│   │   ├── consumer_reports/
│   │   │   ├── anchor_health_reports/
│   │   │   ├── fault_artifact_reports/
│   │   │   ├── monkey_patch_risk/
│   │   │   ├── monkey_patch_risk_reports/
│   │   │   └── test_log_health_reports/
│   │   ├── docs/
│   │   │   └── latest/
│   │   ├── manifest_reports/
│   │   │   ├── scripts_manifest_reports/
│   │   │   └── standards_manifest_reports/
│   │   ├── orchestrator_logs/
│   │   │   ├── batch_cleanup_logs/
│   │   │   ├── health_suite_logs/
│   │   │   ├── pytest_log_capture_logs/
│   │   │   └── standards_index_cli_logs/
│   │   ├── orchestrator_runs/
│   │   │   └── run_batch_cleanup/
│   │   ├── producer_reports/
│   │   │   ├── anchor_inventory_reports/
│   │   │   ├── code_placeholder_scans/
│   │   │   ├── dependency_hygiene_reports/
│   │   │   ├── docs_integrity_reports/
│   │   │   ├── import_boundary_reports/
│   │   │   ├── import_graph_reports/
│   │   │   ├── inventory_health_reports/
│   │   │   ├── inventory_validation_reports/
│   │   │   ├── inventory_view_reports/
│   │   │   ├── lizard_metrics_reports/
│   │   │   ├── lizard_reports/
│   │   │   ├── markdown_anchor_validation_reports/
│   │   │   ├── metrics_anchor_stub_reports/
│   │   │   ├── monkey_patch_scan_reports/
│   │   │   ├── monkey_patch_scans/
│   │   │   ├── placeholder_scan_reports/
│   │   │   ├── render_inventory_views/
│   │   │   ├── standards_diff_reports/
│   │   │   ├── standards_gap_reports/
│   │   │   ├── standards_index_diff_reports/
│   │   │   ├── standards_index_reports/
│   │   │   ├── standards_prompt_reports/
│   │   │   ├── standards_prompt_seeds/
│   │   │   ├── test_coverage_reports/
│   │   │   ├── test_hardening_reports/
│   │   │   ├── test_log_reports/
│   │   │   ├── test_run_coverage/
│   │   │   ├── typecheck_reports/
│   │   │   └── validate_inventory/
│   │   ├── scripts/
│   │   │   └── latest/
│   │   ├── summarizer_reports/
│   │   │   ├── health_suite_summary_reports/
│   │   │   └── standards_summary_reports/
│   │   ├── summary/
│   │   │   └── latest/
│   │   ├── tests/
│   │   │   └── latest/
│   │   └── utility_logs/
│   │       ├── faulthandler_runtime_logs/
│   │       ├── faulthandler_snapshot_logs/
│   │       └── mypy_baseline_reports/
│   ├── scripts/
│   │   ├── aggregators/
│   │   │   └── aggregators_index/
│   │   ├── consumers/
│   │   │   └── consumers_index/
│   │   ├── inventory_schema/
│   │   │   └── views/
│   │   ├── manifest/
│   │   ├── orchestrators/
│   │   │   └── orchestrators_index/
│   │   ├── producers/
│   │   │   └── producers_index/
│   │   ├── reports/
│   │   │   ├── docs/
│   │   │   ├── scripts/
│   │   │   ├── summary/
│   │   │   └── tests/
│   │   ├── scripts_index/
│   │   ├── summarizers/
│   │   │   └── summarizers_index/
│   │   └── utilities/
│   │       └── utilities_index/
│   ├── tests/
│   │   ├── command_center/
│   │   │   └── libraries/
│   │   ├── fixtures/
│   │   │   └── function_inventory/
│   │   ├── schema_validation/
│   │   ├── tests_aggregators/
│   │   ├── tests_command_center/
│   │   │   ├── aggregators/
│   │   │   ├── orchestrators/
│   │   │   ├── producers/
│   │   │   └── viewer/
│   │   ├── tests_consumers/
│   │   ├── tests_library_integration/
│   │   │   ├── duplicates/
│   │   │   └── libraries/
│   │   ├── tests_manifest/
│   │   ├── tests_orchestrators/
│   │   ├── tests_producers/
│   │   ├── tests_summarizers/
│   │   └── tests_utilities/
│   ├── tmp/
│   │   └── coverage_demo/
│   ├── tmp_manual/
│   ├── tmp_tests/
│   ├── tools/
│   └── vendor/
│       └── lizard_ext/
├── docs/
│   ├── automation/
│   ├── standards/
│   │   ├── global/
│   │   └── project/
│   └── templates/
├── tmp_cli_probe/
│   └── inventory_schema/
├── tmp_integration_test/
│   └── inventory_schema/
```
<!-- tree:end -->
