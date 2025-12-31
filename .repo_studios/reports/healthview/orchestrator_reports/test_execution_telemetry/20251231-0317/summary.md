# Test Execution Telemetry Run

Run: `20251231-0317` | Completed: 2025-12-31T03:17:58.970259+00:00

## Pipeline Status

| Step | Status | Detail |
| --- | --- | --- |
| collect | ✅ success | log report captured |
| analyse | ✅ success | analysis completed |
| summarize | ✅ success | health summary generated |

---

## Test Results

**Artifact:** `.repo_studios/reports/healthview/rawview/test_log_reports/20251231-0317`

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

| Metric | Value |
| --- | ---:|
| Files | 0 |
| Functions | 0 |
| Covered | 0 |
| Coverage % | 0.0 |

**Concerns:** ⚠️ Coverage at 0.0% — below 50% threshold

---

## Test Hardening

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_hardening/20251231-0317`

| Metric | Value |
| --- | ---:|
| Files Analyzed | 0 |
| Total Issues | 0 |
| High Severity | 0 |

**Concerns:** ⚠️ No test files analyzed — check scope configuration

---

## Churn × Complexity Hotspots

**Artifact:** `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/churn_complexity_heatmap-2025-12-31_031758`

| Rank | File | Score |
| --- | --- | ---:|
| 1 | run_test_execution_telemetry.py | 12.75 |
| 2 | generate_commandview_inventory.py | 12.73 |
| 3 | generate_test_log_health_report.py | 12.70 |
| 4 | run_docs_health_overview.py | 12.60 |
| 5 | scan_monkey_patches.py | 12.57 |

**Concerns:** ⚠️ 5 file(s) exceed score threshold (12.0)

---

## Pass Rate Trend

**Artifact:** `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20251231-0317`

| Metric | Value |
| --- | ---:|
| Current | 100.0% |
| Previous | 100.0% |
| Delta | +0.00% |

**Concerns:** None — stable or improving
