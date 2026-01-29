# Test Execution Telemetry Run

Run: `20260129-1646` | Completed: 2026-01-29T16:47:47.167492+00:00

## Pipeline Status

| Step | Status | Detail | Duration (s) |
| --- | --- | --- | ---: |
| collect | ✅ success | log report captured | 65.35 |
| analyse | ✅ success | analysis completed | 9.77 |
| summarize | ✅ success | health summary generated | 0.01 |

---

## Test Results

**Artifact:** `.repo_studios/reports/healthview/rawview/test_log_reports/20260129-1646`

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

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_coverage_inventory/20260129-1646`

| Metric | Value |
| --- | ---:|
| Files | 84 |
| Functions | 1581 |
| Covered | 1548 |
| Coverage % | 97.9 |

**Concerns:** None

---

## Test Hardening

**Artifact:** `.repo_studios/reports/healthview/producer_reports/test_hardening/20260129-1646`

| Metric | Value |
| --- | ---:|
| Files Analyzed | 147 |
| Total Issues | 299 |
| High Severity | 194 |

**Concerns:** ❌ 194 high-severity issue(s)

---

## Churn × Complexity Hotspots

**Artifact:** `.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/20260129-1647`

| Rank | File | Score |
| --- | --- | ---:|
| 1 | run_test_execution_telemetry.py | 15.01 |
| 2 | run_docs_health_overview.py | 14.67 |
| 3 | scan_monkey_patches.py | 14.54 |
| 4 | run_standards_integrity.py | 13.88 |
| 5 | generate_test_log_health_report.py | 13.79 |

**Concerns:** ⚠️ 5 file(s) exceed score threshold (12.0)

---

## Pass Rate Trend

**Artifact:** `.repo_studios/reports/healthview/consumer_reports/test_log_health_reports/20260129-1646`

| Metric | Value |
| --- | ---:|
| Current | 98.4% |
| Previous | 98.4% |
| Delta | +0.00% |

**Concerns:** None — stable or improving
