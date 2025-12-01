# Test Execution Telemetry Summary Template

Use this template when authoring Healthview Markdown summaries for Test Execution Telemetry
runs. Replace bracketed placeholders with the values emitted by the orchestrator
(`run_test_execution_telemetry.py`) and remove any sections that do not apply to the run.

## Run Context

- run_slug: `{{ run_slug }}`
- pipeline_status: {{ pipeline_status }}
- log_report_available: {{ log_report_available }}
- warnings_total: {{ warnings_total }}
- slow_tests_over_threshold: {{ slow_tests_over_threshold }}
- heatmap_mode: {{ heatmap_mode }}
- hardening_status: {{ hardening_status }}
- hardening_high_severity: {{ hardening_high_severity }}
- coverage_status: {{ coverage_status }}
- health_report_source: {{ health_report_source }}
- completed_at: {{ completed_at_iso }}

## Runtime Metrics

| Step | Status | Duration (s) | Detail |
| --- | --- | --- | --- |
| collect | {{ step_collect_status }} | {{ step_collect_duration }} | {{ step_collect_detail }} |
| analyse | {{ step_analyse_status }} | {{ step_analyse_duration }} | {{ step_analyse_detail }} |
| summarize | {{ step_summarize_status }} | {{ step_summarize_duration }} | {{ step_summarize_detail }} |

## Failure Highlights

- detected_failures: {{ detected_failures }}
- failure_examples:
  - {{ failure_example_one }}
  - {{ failure_example_two }}

## Artifact Locations

- log_report: `{{ log_report_relative }}`
- coverage_report: `{{ coverage_report_relative }}`
- heatmap: `{{ heatmap_relative }}`
- hardening: `{{ hardening_relative }}`
- health_report: `{{ health_report_relative }}`
- health_bundle_summary: `{{ health_bundle_summary_relative }}`

## Step Outcomes

- collect: {{ step_collect_status }}
  - detail: {{ step_collect_detail }}
- analyse: {{ step_analyse_status }}
  - detail: {{ step_analyse_detail }}
- summarize: {{ step_summarize_status }}
  - detail: {{ step_summarize_detail }}

> Note: If the summarize step is skipped, omit the failure highlights section and replace
> `health_report_source` with `none`.
