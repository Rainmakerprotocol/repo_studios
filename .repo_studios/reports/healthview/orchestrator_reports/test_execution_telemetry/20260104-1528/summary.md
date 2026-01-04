# Test Execution Telemetry Run

Run: `20260104-1528` | Completed: 2026-01-04T15:28:39.627162+00:00

## Pipeline Status

| Step | Status | Detail |
| --- | --- | --- |
| collect | ✅ success | log report captured |
| analyse | ✅ success | analysis completed |
| summarize | ✅ success | health summary generated |

---

## Test Results

**Artifact:** `.repo_studios/reports/healthview/rawview/test_log_reports/20260104-1528`

| Metric | Value |
| --- | ---:|
| Total | 64 |
| Passed | 63 |
| Failed | 1 |
| Warnings | 0 |
| Slow | 0 |

**Concerns:** ❌ 1 test(s) failed

---

## Coverage Analysis

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_coverage_inventory/20260104-1528`

| Metric | Value |
| --- | ---:|
| Files | 1 |
| Functions | 24 |
| Covered | 0 |
| Coverage % | 0.0 |

**Concerns:** ⚠️ Coverage at 0.0% — below 50.0% heuristic threshold (no min_coverage configured)

---

## Test Hardening

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_hardening/20260104-1528`

| Metric | Value |
| --- | ---:|
| Files Analyzed | 146 |
| Total Issues | 287 |
| High Severity | 188 |

**Concerns:** ❌ 188 high-severity issue(s)

---

## Churn × Complexity Hotspots

**Artifact:** `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/20260104-1528`

| Rank | File | Score |
| --- | --- | ---:|
| 1 | run_test_execution_telemetry.py | 13.83 |
| 2 | scan_monkey_patches.py | 13.44 |
| 3 | generate_test_log_health_report.py | 13.23 |
| 4 | run_docs_health_overview.py | 13.00 |
| 5 | generate_commandview_inventory.py | 12.73 |

**Concerns:** ⚠️ 5 file(s) exceed score threshold (12.0)

---

## Pass Rate Trend

**Artifact:** `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20260104-1528`

| Metric | Value |
| --- | ---:|
| Current | 98.4% |
| Previous | 98.4% |
| Delta | +0.00% |

**Concerns:** None — stable or improving
