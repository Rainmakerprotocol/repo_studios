# Dependency & Import Hygiene Summary

- run_slug: `20260123-2344`
- pipeline_status: failed
- dependency_status: failed
- dependency_issue_count: 5
- import_graph_status: ok
- placeholder_matches: 5
- placeholder_unallowlisted_matches: 5
- batch_cleanup_status: skipped
- typecheck_status: error
- typecheck_error_count: 1
- typecheck_files_with_issues: 1
- mypy_baseline_status: not requested

## Step Outcomes

- dependency: failed
  - detail: issues detected (5 findings)
- import_graph: success
  - detail: status ok
- placeholders: success
  - detail: total matches 5
- cleanup: skipped
  - detail: batch cleanup skipped via flag
- typecheck: failed
  - detail: status error
- refresh_baselines: skipped
  - detail: baseline refresh not requested
