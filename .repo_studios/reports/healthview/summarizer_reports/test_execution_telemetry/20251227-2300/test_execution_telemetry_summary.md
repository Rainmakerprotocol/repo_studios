# Test Execution Telemetry Summary

- run_slug: `20251227-2300`
- pipeline_status: success
- log_report_available: yes
- warnings_total: 0
- slow_tests_over_threshold: 0
- heatmap_mode: consumer
- hardening_status: ok
- hardening_high_severity: unknown
- coverage_status: ok
- health_report_source: producer
- completed_at: 2025-12-27T23:00:54+00:00

## Runtime Metrics

| Step | Status | Duration (s) | Detail |
| --- | --- | --- | --- |
| collect | success | 0.08 | log report captured |
| analyse | success | 5.07 | analysis completed |
| summarize | success | 0.01 | health summary generated |

## Failure Highlights

- detected_failures: 0
- failure_examples:
  - none

## Artifact Locations

- log_report: `.repo_studios/reports/healthview/rawview/test_log_reports/20251227-2300`
- coverage_report: `.repo_studios/reports/healthview/producer_reports/test_coverage_inventory/20251227-2300`
- heatmap: `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/churn_complexity_heatmap-2025-12-27_230054`
- hardening: `.repo_studios/reports/healthview/producer_reports/test_hardening/20251227-2300`
- health_report: `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20251227-2300`
- health_bundle_summary: `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20251227-2300/bundle_summary.json`

## Step Outcomes

- collect: success
  - detail: log report captured
- analyse: success
  - detail: analysis completed
- summarize: success
  - detail: health summary generated
