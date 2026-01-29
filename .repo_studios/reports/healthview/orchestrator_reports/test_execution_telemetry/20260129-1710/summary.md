# Test Execution Telemetry Run

Run: `20260129-1710` | Completed: 2026-01-29T17:11:34.038640+00:00

**Total Runtime:** 75.92 seconds


## Pipeline Status

| Step | Status | Detail | Duration (s) |
| --- | --- | --- | ---: |
| collect | ✅ success | log report captured | 66.04 |
| analyse | ✅ success | analysis completed | 9.87 |
| summarize | ✅ success | health summary generated | 0.02 |

---

## Child Script Outcomes

| Script | Status | Exit | Duration (s) |
| --- | --- | ---: | ---: |
| generate_test_coverage_inventory.py | ✅ ok | 0 | 66.00 |
| collect_test_log_reports.py | ✅ ok | 0 | 0.03 |
| analyze_test_hardening.py | ⚠️ issues-found | 1 | 0.72 |
| generate_churn_complexity_heatmap.py | ✅ ok | 0 | 9.15 |
| generate_test_log_health_report.py | ✅ ok | 0 | 0.02 |

---

## Test Results

**Artifact:** `.repo_studios/reports/healthview/rawview/test_log_reports/20260129-1710`

| Metric | Value |
| --- | ---:|
| Total | 64 |
| Passed | 63 |
| Failed | 1 |
| Warnings | 0 |
| Slow (>5s) | 0 |

**Failed Tests:**

- `test_summarizer_generates_overview`: FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\genet\\AppData\\Local\\Temp\\...

**Concerns:** ❌ 1 test(s) failed

---

## Coverage Analysis

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_coverage_inventory/20260129-1710`

| Metric | Value |
| --- | ---:|
| Files | 84 |
| Functions | 1587 |
| Covered | 1554 |
| Coverage % | 97.9 |
| Threshold | 50.0% (heuristic) |

**Concerns:** None

---

## Test Hardening

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_hardening/20260129-1710`

| Metric | Value |
| --- | ---:|
| Files Analyzed | 147 |
| Total Issues | 299 |
| High Severity | 194 |

**Concerns:** ❌ 194 high-severity issue(s)

---

## Churn × Complexity Hotspots

**Artifact:** `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/20260129-1711`

| Rank | File | Score |
| --- | --- | ---:|
| 1 | `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` | 15.67 |
| 2 | `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py` | 14.67 |
| 3 | `.repo_studios/scripts/producers/scan_monkey_patches.py` | 14.54 |
| 4 | `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` | 13.88 |
| 5 | `.repo_studios/scripts/consumers/generate_test_log_health_report.py` | 13.79 |

**Concerns:** ⚠️ 5 file(s) exceed score threshold (12.0)

---

## Pass Rate Trend

**Artifact:** `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20260129-1710`

| Metric | Value |
| --- | ---:|
| Current | 98.4% |
| Previous | 98.4% |
| Delta | +0.00% |

**Concerns:** None — stable or improving

---

## Input Configuration

| Parameter | Value |
| --- | --- |
| logs_dir | `.repo_studios/reports/healthview/rawview/test_execution_runs` |
| tests_dir | `.repo_studios/tests` |
| coverage_xml | `coverage.xml` |
| heatmap_window | 500 |
| metrics_source | `N/A` |

**Retention Settings:**

| Scope | Keep |
| --- | ---: |
| orchestrator | 5 |
| collector | 5 |
| coverage | 5 |
| heatmap | 5 |
| hardening | 5 |
| health | 3 |

---

## Artifacts Index

**Run Directory:** `.repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry`

**Base Package:**

- `manifest.json` — Pipeline manifest with child outcomes
- `summary.md` — This summary report
- `telemetry.json` — Metrics and timing data
- `child_outcomes.json` — Per-script execution records

**Child Artifacts:**

- **log_report:** `.repo_studios/reports/healthview/rawview/test_log_reports/20260129-1710`
- **coverage_report:** `.repo_studios/reports/healthview/producer_reports/test_coverage_inventory/20260129-1710`
- **heatmap:** `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/20260129-1711`
- **hardening:** `.repo_studios/reports/healthview/producer_reports/test_hardening/20260129-1710`
- **health_report:** `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20260129-1710`
- **health_bundle_summary:** `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20260129-1710/bundle_summary.json`
