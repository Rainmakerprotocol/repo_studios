# Test Execution Telemetry Run

Run: `20260123-2342` | Completed: 2026-01-23T23:44:16.265403+00:00

## Pipeline Status

| Step | Status | Detail |
| --- | --- | --- |
| collect | ✅ success | log report captured |
| analyse | ✅ success | analysis completed |
| summarize | ✅ success | health summary generated |

---

## Test Results

**Artifact:** `.repo_studios/reports/healthview/rawview/test_log_reports/20260123-2342`

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

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_coverage_inventory/20260123-2342`

| Metric | Value |
| --- | ---:|
| Files | 84 |
| Functions | 1604 |
| Covered | 1572 |
| Coverage % | 98.0 |

**Concerns:** None

---

## Test Hardening

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_hardening/20260123-2342`

| Metric | Value |
| --- | ---:|
| Files Analyzed | 147 |
| Total Issues | 292 |
| High Severity | 192 |

**Concerns:** ❌ 192 high-severity issue(s)

---

## Churn × Complexity Hotspots

**Artifact:** `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/20260123-2344`

| Rank | File | Score |
| --- | --- | ---:|
| 1 | scan_monkey_patches.py | 14.54 |
| 2 | run_docs_health_overview.py | 14.29 |
| 3 | run_test_execution_telemetry.py | 14.16 |
| 4 | generate_commandview_inventory.py | 13.61 |
| 5 | run_standards_integrity.py | 13.58 |

**Concerns:** ⚠️ 5 file(s) exceed score threshold (12.0)

---

## Pass Rate Trend

**Artifact:** `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20260123-2342`

| Metric | Value |
| --- | ---:|
| Current | 98.4% |
| Previous | 98.4% |
| Delta | +0.00% |

**Concerns:** None — stable or improving
