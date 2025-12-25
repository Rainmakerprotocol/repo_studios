# Test Execution Telemetry Summary

- run_slug: `20251225-0033`
- pipeline_status: success
- log_report_available: yes
- warnings_total: 0
- slow_tests_over_threshold: 0
- heatmap_mode: logs_fallback
- hardening_status: ok
- hardening_high_severity: unknown
- coverage_status: ok
- health_report_source: producer
- completed_at: 2025-12-25T00:33:55+00:00

## Runtime Metrics

| Step | Status | Duration (s) | Detail |
| --- | --- | --- | --- |
| collect | success | 0.08 | log report captured |
| analyse | success | 8.09 | analysis completed |
| summarize | success | 0.01 | health summary generated |

## Failure Highlights

- detected_failures: 0
- failure_examples:
  - none

## Artifact Locations

- log_report: `.repo_studios/reports/healthview/rawview/test_log_reports/20251225-0033`
- coverage_report: `.repo_studios/reports/healthview/producer_reports/test_coverage_inventory/20251225-0033`
- heatmap: `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/churn_complexity_heatmap-2025-12-25_003355`
- hardening: `.repo_studios/reports/healthview/producer_reports/test_hardening/20251225-0033`
- health_report: `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20251225-0033`
- health_bundle_summary: `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20251225-0033/bundle_summary.json`

## Step Outcomes

- collect: success
  - detail: log report captured
- analyse: success
  - detail: analysis completed
- summarize: success
  - detail: health summary generated
