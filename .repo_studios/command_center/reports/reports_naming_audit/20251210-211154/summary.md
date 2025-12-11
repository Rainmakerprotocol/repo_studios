# Report Naming Audit

- Reports root: `C:\Users\genet\repo_studios\.repo_studios\command_center\reports`
- Generated at: 2025-12-10T21:11:54.465875+00:00
- Scanned files: 246
- Compliant files: 73
- Violations: 173
- Compliance ratio: 0.2967

## Issue Totals

| Issue | Count |
| --- | --- |
| insufficient_depth | 115 |
| invalid_timestamp | 25 |
| invalid_viewer_slug | 6 |
| latest_alias_present | 13 |
| unexpected_artifact_name | 57 |
| unexpected_nesting | 1 |

## Violations

| Path | Issues |
| --- | --- |
| `automation_metrics_demo/latest_metrics_summary.json` | latest_alias_present, insufficient_depth |
| `automation_metrics_demo/metrics_summary-20251103_120000/metrics_summary.json` | insufficient_depth |
| `commandview/duplicate_scan/20251130-0333/scripts_duplicate_matrix.json` | unexpected_artifact_name |
| `commandview/duplicate_scan/20251130-0333/scripts_duplicate_summary.md` | unexpected_artifact_name |
| `commandview/duplicate_scan/20251130-0456/scripts_duplicate_matrix.json` | unexpected_artifact_name |
| `commandview/duplicate_scan/20251130-0456/scripts_duplicate_summary.md` | unexpected_artifact_name |
| `commandview/duplicate_scan/20251130-0457/scripts_duplicate_matrix.json` | unexpected_artifact_name |
| `commandview/duplicate_scan/20251130-0457/scripts_duplicate_summary.md` | unexpected_artifact_name |
| `commandview/function_analysis/20251130-0503/scripts_analysis.json` | unexpected_artifact_name |
| `commandview/standards_index_gaps/20251207-0239/bundle_summary.json` | unexpected_artifact_name |
| `commandview/standards_index_gaps/20251207-0239/candidates.tsv` | unexpected_artifact_name |
| `commandview/standards_index_gaps/20251207-0320/bundle_summary.json` | unexpected_artifact_name |
| `commandview/standards_index_gaps/20251207-0320/candidates.tsv` | unexpected_artifact_name |
| `commandview/standards_index_gaps/20251207-0330/bundle_summary.json` | unexpected_artifact_name |
| `commandview/standards_index_gaps/20251207-0330/candidates.tsv` | unexpected_artifact_name |
| `commandview/standards_index_gaps/20251207-1406/bundle_summary.json` | unexpected_artifact_name |
| `commandview/standards_index_gaps/20251207-1406/candidates.tsv` | unexpected_artifact_name |
| `commandview/standards_index_gaps/20251208-0014/bundle_summary.json` | unexpected_artifact_name |
| `commandview/standards_index_gaps/20251208-0014/candidates.tsv` | unexpected_artifact_name |
| `duplicates_scan/repo-studios__command-center__scripts_duplicate_scan/scripts_duplicate_matrix-2025-10-28-2107.json` | insufficient_depth |
| `duplicates_scan/repo-studios__command-center__scripts_duplicate_scan/scripts_duplicate_summary-2025-10-28-2107.md` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__aggregators_duplicate_scan/aggregators_duplicate_matrix-2025-10-28-0942.json` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__aggregators_duplicate_scan/aggregators_duplicate_summary-2025-10-28-0942.md` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__consumers_duplicate_scan/consumers_duplicate_matrix-2025-10-28-0934.json` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__consumers_duplicate_scan/consumers_duplicate_summary-2025-10-28-0934.md` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__orchestrators_duplicate_scan/orchestrators_duplicate_matrix-2025-10-28-0955.json` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__orchestrators_duplicate_scan/orchestrators_duplicate_summary-2025-10-28-0955.md` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__producers_duplicate_scan/producers_duplicate_matrix-2025-10-28.json` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__producers_duplicate_scan/producers_duplicate_summary-2025-10-28.md` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__summarizers_duplicate_scan/summarizers_duplicate_matrix-2025-10-28-1340.json` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__summarizers_duplicate_scan/summarizers_duplicate_summary-2025-10-28-1340.md` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__utilities_duplicate_scan/utilities_duplicate_matrix-2025-10-28-1344.json` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts__utilities_duplicate_scan/utilities_duplicate_summary-2025-10-28-1344.md` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts_duplicate_scan/scripts_duplicate_matrix-2025-10-27.json` | insufficient_depth |
| `duplicates_scan/repo-studios__scripts_duplicate_scan/scripts_duplicate_summary-2025-10-27.md` | insufficient_depth |
| `duplicates_scan/repo_studios__command_center__scripts_duplicate_scan/scripts_duplicate_matrix-2025-11-27-1757.json` | insufficient_depth |
| `duplicates_scan/repo_studios__command_center__scripts_duplicate_scan/scripts_duplicate_summary-2025-11-27-1757.md` | insufficient_depth |
| `duplicates_scan/repo_studios__scripts__producers_duplicate_scan/producers_duplicate_matrix-2025-11-05-1125.json` | insufficient_depth |
| `duplicates_scan/repo_studios__scripts__producers_duplicate_scan/producers_duplicate_summary-2025-11-05-1125.md` | insufficient_depth |
| `duplicates_scan/repo_studios__scripts__summarizers_duplicate_scan/summarizers_duplicate_matrix-2025-11-04-2010.json` | insufficient_depth |
| `duplicates_scan/repo_studios__scripts__summarizers_duplicate_scan/summarizers_duplicate_summary-2025-11-04-2010.md` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-11-28_214734-2025-11-28_1702/bundle_summary.json` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-11-28_214734-2025-11-28_1702/summary.json` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-11-28_214734-2025-11-28_1702/SUMMARY.md` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-01_131330-2025-11-28_1702/bundle_summary.json` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-01_131330-2025-11-28_1702/summary.json` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-01_131330-2025-11-28_1702/SUMMARY.md` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-07_023927-2025-11-28_1702/bundle_summary.json` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-07_023927-2025-11-28_1702/summary.json` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-07_023927-2025-11-28_1702/SUMMARY.md` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-07_133522-2025-11-28_1702/bundle_summary.json` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-07_133522-2025-11-28_1702/summary.json` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-07_133522-2025-11-28_1702/SUMMARY.md` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-07_133758-2025-11-28_1702/bundle_summary.json` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-07_133758-2025-11-28_1702/summary.json` | insufficient_depth |
| `fault_artifacts_consumer/fault_artifacts-2025-12-07_133758-2025-11-28_1702/SUMMARY.md` | insufficient_depth |
| `fault_artifacts_consumer/latest_bundle_summary.json` | latest_alias_present, insufficient_depth |
| `fault_artifacts_consumer/latest_summary.json` | latest_alias_present, insufficient_depth |
| `fault_artifacts_consumer/latest_SUMMARY.md` | latest_alias_present, insufficient_depth |
| `fault_artifacts_producer/faulthandler_report-20251207_133758/bundle_summary.json` | insufficient_depth |
| `fault_artifacts_producer/faulthandler_report-20251207_133758/report.json` | insufficient_depth |
| `fault_artifacts_producer/faulthandler_report-20251207_133758/report.md` | insufficient_depth |
| `fault_artifacts_producer/faulthandler_report-20251209_232639/bundle_summary.json` | insufficient_depth |
| `fault_artifacts_producer/faulthandler_report-20251209_232639/report.json` | insufficient_depth |
| `fault_artifacts_producer/faulthandler_report-20251209_232639/report.md` | insufficient_depth |
| `fault_artifacts_producer/latest_bundle_summary.json` | latest_alias_present, insufficient_depth |
| `fault_artifacts_producer/latest_report.json` | latest_alias_present, insufficient_depth |
| `fault_artifacts_producer/latest_report.md` | latest_alias_present, insufficient_depth |
| `fault_pipeline_orchestrator/fault_pipeline-20251128_214734/bundle_summary.json` | insufficient_depth |
| `fault_pipeline_orchestrator/fault_pipeline-20251128_214734/pipeline.log` | insufficient_depth |
| `fault_pipeline_orchestrator/fault_pipeline-20251128_214734/summary.json` | insufficient_depth |
| `fault_pipeline_orchestrator/fault_pipeline-20251128_214734/SUMMARY.md` | insufficient_depth |
| `fault_pipeline_orchestrator/latest_bundle_summary.json` | latest_alias_present, insufficient_depth |
| `fault_pipeline_orchestrator/latest_pipeline.log` | latest_alias_present, insufficient_depth |
| `fault_pipeline_orchestrator/latest_summary.json` | latest_alias_present, insufficient_depth |
| `fault_pipeline_orchestrator/latest_SUMMARY.md` | latest_alias_present, insufficient_depth |
| `healthview/standards_overview/20251207-0239/standards_overview.json` | unexpected_artifact_name |
| `healthview/standards_overview/20251207-0239/standards_overview.md` | unexpected_artifact_name |
| `healthview/standards_overview/20251207-1335/standards_overview.json` | unexpected_artifact_name |
| `healthview/standards_overview/20251207-1335/standards_overview.md` | unexpected_artifact_name |
| `healthview/standards_overview/20251207-1338/standards_overview.json` | unexpected_artifact_name |
| `healthview/standards_overview/20251207-1338/standards_overview.md` | unexpected_artifact_name |
| `healthview/standards_overview/20251207-1406/standards_overview.json` | unexpected_artifact_name |
| `healthview/standards_overview/20251207-1406/standards_overview.md` | unexpected_artifact_name |
| `healthview/standards_overview/20251208-0014/standards_overview.json` | unexpected_artifact_name |
| `healthview/standards_overview/20251208-0014/standards_overview.md` | unexpected_artifact_name |
| `healthview/test_execution_telemetry/20251207-0239/test_execution_telemetry_summary.json` | unexpected_artifact_name |
| `healthview/test_execution_telemetry/20251207-0239/test_execution_telemetry_summary.md` | unexpected_artifact_name |
| `healthview/test_execution_telemetry/20251207-0320/test_execution_telemetry_summary.json` | unexpected_artifact_name |
| `healthview/test_execution_telemetry/20251207-0320/test_execution_telemetry_summary.md` | unexpected_artifact_name |
| `healthview/test_execution_telemetry/20251207-0330/test_execution_telemetry_summary.json` | unexpected_artifact_name |
| `healthview/test_execution_telemetry/20251207-0330/test_execution_telemetry_summary.md` | unexpected_artifact_name |
| `index_scan/repo-studios__command-center__scripts_index/scripts_index-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__command-center__scripts_index/scripts_screening-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__aggregators_index/aggregators_index-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__aggregators_index/aggregators_screening-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__consumers_index/consumers_index-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__consumers_index/consumers_screening-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__orchestrators_index/orchestrators_index-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__orchestrators_index/orchestrators_screening-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__producers_index/producers_index-2025-10-27.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__producers_index/producers_screening-2025-10-27.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__summarizers_index/summarizers_index-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__summarizers_index/summarizers_screening-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__utilities_index/utilities_index-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts__utilities_index/utilities_screening-2025-10-28.json` | insufficient_depth |
| `index_scan/repo-studios__scripts_index/scripts_index-2025-10-27.json` | insufficient_depth |
| `index_scan/repo-studios__scripts_index/scripts_screening-2025-10-27.json` | insufficient_depth |
| `index_scan/repo_studios__command_center__scripts__producers_index/producers_commandview_20251106-1014.json` | insufficient_depth |
| `index_scan/repo_studios__command_center__scripts__producers_index/producers_commandview_screening_20251106-1014.json` | insufficient_depth |
| `index_scan/repo_studios__command_center__scripts_index/scripts_commandview_20251130-0457.json` | insufficient_depth |
| `index_scan/repo_studios__command_center__scripts_index/scripts_commandview_screening_20251130-0457.json` | insufficient_depth |
| `index_scan/repo_studios__scripts__producers_index/producers_index-2025-11-05.json` | insufficient_depth |
| `index_scan/repo_studios__scripts__producers_index/producers_screening-2025-11-05.json` | insufficient_depth |
| `index_scan/repo_studios__scripts__summarizers_index/summarizers_index-2025-11-04.json` | insufficient_depth |
| `index_scan/repo_studios__scripts__summarizers_index/summarizers_screening-2025-11-04.json` | insufficient_depth |
| `index_scan/repo_studios__scripts_index/scripts_commandview_20251129-2102.json` | insufficient_depth |
| `index_scan/repo_studios__scripts_index/scripts_commandview_screening_20251129-2102.json` | insufficient_depth |
| `index_scan/repo_studios_index/.repo_studios_commandview_20251128-0217.json` | insufficient_depth |
| `index_scan/repo_studios_index/.repo_studios_commandview_screening_20251128-0217.json` | insufficient_depth |
| `index_scan/sample_pkg_index/sample_pkg_index-2025-10-27.json` | insufficient_depth |
| `index_scan/sample_pkg_index/sample_pkg_screening-2025-10-27.json` | insufficient_depth |
| `index_scan_analysis/repo-studios__command-center__scripts_analysis/scripts_analysis-2025-10-28.json` | insufficient_depth |
| `index_scan_analysis/repo-studios__scripts__aggregators_analysis/aggregators_analysis-2025-10-28.json` | insufficient_depth |
| `index_scan_analysis/repo-studios__scripts__consumers_analysis/consumers_analysis-2025-10-28.json` | insufficient_depth |
| `index_scan_analysis/repo-studios__scripts__orchestrators_analysis/orchestrators_analysis-2025-10-28.json` | insufficient_depth |
| `index_scan_analysis/repo-studios__scripts__producers_analysis/producers_analysis-2025-10-27.json` | insufficient_depth |
| `index_scan_analysis/repo-studios__scripts__summarizers_analysis/summarizers_analysis-2025-10-28.json` | insufficient_depth |
| `index_scan_analysis/repo-studios__scripts__utilities_analysis/utilities_analysis-2025-10-28.json` | insufficient_depth |
| `index_scan_analysis/repo-studios__scripts_analysis/scripts_analysis-2025-10-27.json` | insufficient_depth |
| `index_scan_analysis/repo_studios__command_center__scripts_analysis/scripts_analysis-2025-11-27.json` | insufficient_depth |
| `index_scan_analysis/repo_studios__scripts__producers_analysis/producers_analysis-2025-11-05.json` | insufficient_depth |
| `index_scan_analysis/repo_studios__scripts__summarizers_analysis/summarizers_analysis-2025-11-04.json` | insufficient_depth |
| `rawview/dependency_import_hygiene_cleanup/.gitkeep` | insufficient_depth |
| `rawview/fault_diagnostics_runs/20251128-1702/bundle_summary.json` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_diagnostics_runs/20251128-1702/dumps/combined.txt` | unexpected_nesting, invalid_timestamp |
| `rawview/fault_diagnostics_runs/20251128-1702/MANIFEST.json` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_diagnostics_runs/20251128-1702/stacks.csv` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_diagnostics_runs/20251128-1702/stacks.log` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_diagnostics_runs/20251128-1702/SUMMARY.md` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251128-2229/bundle_summary.json` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251128-2229/MANIFEST.json` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251128-2229/SUMMARY.md` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251128-2231/bundle_summary.json` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251128-2231/MANIFEST.json` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251128-2231/snapshot.txt` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251128-2231/SUMMARY.md` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251209-2322/bundle_summary.json` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251209-2322/MANIFEST.json` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251209-2322/SUMMARY.md` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251209-2326/bundle_summary.json` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251209-2326/MANIFEST.json` | invalid_timestamp, unexpected_artifact_name |
| `rawview/fault_snapshots/20251209-2326/SUMMARY.md` | invalid_timestamp, unexpected_artifact_name |
| `rawview/mypy_baselines/.gitkeep` | insufficient_depth |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_160000/inputs/automation_config.yaml` | invalid_viewer_slug, invalid_timestamp, unexpected_artifact_name |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_160000/inputs/files_sample.json` | invalid_viewer_slug, invalid_timestamp, unexpected_artifact_name |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_160000/inputs/tests_sample.json` | invalid_viewer_slug, invalid_timestamp, unexpected_artifact_name |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_160000/manifest.json` | insufficient_depth |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_160000/metrics_summary.json` | insufficient_depth |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_160000/README.md` | insufficient_depth |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_170000/inputs/automation_config.yaml` | invalid_viewer_slug, invalid_timestamp, unexpected_artifact_name |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_170000/inputs/files_sample.json` | invalid_viewer_slug, invalid_timestamp, unexpected_artifact_name |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_170000/inputs/tests_sample.json` | invalid_viewer_slug, invalid_timestamp, unexpected_artifact_name |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_170000/manifest.json` | insufficient_depth |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_170000/metrics_summary.json` | insufficient_depth |
| `repo-studios__command-center__automation_run/automation_manifest-20251103_170000/README.md` | insufficient_depth |
| `repo-studios__command-center__automation_run/latest_automation_manifest.json` | latest_alias_present, insufficient_depth |
| `repo-studios__command-center__automation_run/latest_metrics_summary.json` | latest_alias_present, insufficient_depth |
| `reports_naming_audit/20251130-131522/summary.json` | insufficient_depth |
| `reports_naming_audit/20251130-131522/summary.md` | insufficient_depth |
| `reports_naming_audit/20251205-151329/summary.json` | insufficient_depth |
| `reports_naming_audit/20251205-151329/summary.md` | insufficient_depth |
| `selector.json` | insufficient_depth |

## Latest Aliases

- `automation_metrics_demo/latest_metrics_summary.json`
- `fault_artifacts_consumer/latest_SUMMARY.md`
- `fault_artifacts_consumer/latest_bundle_summary.json`
- `fault_artifacts_consumer/latest_summary.json`
- `fault_artifacts_producer/latest_bundle_summary.json`
- `fault_artifacts_producer/latest_report.json`
- `fault_artifacts_producer/latest_report.md`
- `fault_pipeline_orchestrator/latest_SUMMARY.md`
- `fault_pipeline_orchestrator/latest_bundle_summary.json`
- `fault_pipeline_orchestrator/latest_pipeline.log`
- `fault_pipeline_orchestrator/latest_summary.json`
- `repo-studios__command-center__automation_run/latest_automation_manifest.json`
- `repo-studios__command-center__automation_run/latest_metrics_summary.json`
