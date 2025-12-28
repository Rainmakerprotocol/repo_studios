# Test Execution Telemetry Run

Run: `20251228-0200` | Completed: 2025-12-28T02:00:27.401064+00:00

## Pipeline Status

| Step | Status | Detail |
| --- | --- | --- |
| collect | ✅ success | log report captured |
| analyse | ✅ success | analysis completed |
| summarize | ✅ success | health summary generated |

---

## Test Results

**Artifact:** `.repo_studios/reports/healthview/rawview/test_log_reports/20251228-0200`

| Metric | Value |
| --- | ---:|
| Total | 452 |
| Passed | 452 |
| Failed | 0 |
| Warnings | 0 |
| Slow | 0 |

**Concerns:** None

---

## Coverage Analysis

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_coverage_inventory/20251228-0200`

| Metric | Value |
| --- | ---:|
| Files | 1 |
| Functions | 24 |
| Covered | 0 |
| Coverage % | 0.0 |

**Concerns:** ⚠️ Coverage at 0.0% — below 50% threshold

---

## Test Hardening

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_hardening/20251228-0200`

| Metric | Value |
| --- | ---:|
| Files Analyzed | 0 |
| Total Issues | 0 |
| High Severity | 0 |

**Concerns:** ⚠️ No test files analyzed — check scope configuration

---

## Churn × Complexity Hotspots

**Artifact:** `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/churn_complexity_heatmap-2025-12-28_020027`

| Rank | File | Score |
| --- | --- | ---:|
| 1 | run_test_execution_telemetry.py | 12.75 |
| 2 | generate_commandview_inventory.py | 12.73 |
| 3 | generate_test_log_health_report.py | 12.34 |
| 4 | scan_monkey_patches.py | 12.07 |
| 5 | generate_churn_complexity_heatmap.py | 11.24 |

**Concerns:** ⚠️ 4 file(s) exceed score threshold (12.0)

---

## Pass Rate Trend

**Artifact:** `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20251228-0200`

| Metric | Value |
| --- | ---:|
| Current | 100.0% |
| Previous | 100.0% |
| Delta | +0.00% |

**Concerns:** None — stable or improving
