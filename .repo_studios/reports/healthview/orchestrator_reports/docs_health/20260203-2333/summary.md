# Docs Health Run

Run: `20260203-2333` | Completed: 2026-02-03T23:33:37.294154+00:00

## Pipeline Status

| Step | Status | Detail |
| --- | --- | --- |
| doc-index | ✅ success | docs=388, headings=3201 |
| anchor-inventory | ✅ success | docs=200, missing_h1=7, missing_h2=3, slugs=1168, duplicates=167, cross_file_docs=169, repeated_docs=7 |
| anchor-validation | ⚠️ skipped | anchor validation skipped |
| docs-integrity | ✅ success | status=ok, mismatches=0 |
| metrics-stub | ✅ success | status=ok, missing=0 |
| code-doc-churn | ✅ success | missing_docs=1 |
| undocumented-logic | ✅ success | modules_with_findings=39 |
| aggregate | ✅ success | overall=60.41 |

---

## Overall Score

**Artifact:** `.repo_studios/reports/healthview/aggregator_reports/docs_health_signals/20260203-2333`

| Metric | Value |
| --- | ---:|
| Overall Score | 60.41 |

| Category | Score | Status | Weight |
| --- | ---:| --- | ---:|
| freshness | 66.66666666666666 | warning | 0.35 |
| coverage | 58.72 | critical | 0.35 |
| structure | 10.180821917808217 | critical | 0.15 |
| integrity | 100.0 | healthy | 0.1 |
| hygiene | 100.0 | healthy | 0.05 |

**Concerns:** ❌ 2 category(ies) are critical

---

## Doc Index

**Artifact:** `.repo_studios/reports/healthview/producer_reports/doc_index/20260203-2333`

| Metric | Value |
| --- | ---:|
| Documents | 388 |
| Headings | 3201 |
| Links | 378 |
| Missing Descriptions | 41 |
| Placeholder Docs | 114 |
| Duplicate Slugs | 7 |
| Link Density | 0.9742268041237113 |

**Concerns:** ⚠️ 41 missing descriptions; ⚠️ 114 placeholder docs; ⚠️ 7 duplicate slugs

---

## Anchor Inventory

**Artifact:** `.repo_studios/reports/healthview/producer_reports/anchor_inventory/20260203-2333`

| Metric | Value |
| --- | ---:|
| Documents Scanned | 200 |
| Missing H1 | 7 |
| Missing H2 | 3 |
| Total Slugs | 1168 |
| Cross-file Duplicates | 167 |
| Docs w/ Cross-file Duplicates | 169 |
| Docs w/ Repeated Anchors | 7 |

**Concerns:** ⚠️ 7 missing H1; ⚠️ 3 missing H2

---

## Anchor Validation

| Metric | Value |
| --- | ---:|
| Files Scanned |  |
| Links Checked |  |
| Issue Count |  |
| Missing Files |  |
| Missing Anchors |  |

**Concerns:** None

---

## Docs Integrity

**Artifact:** `.repo_studios/reports/healthview/producer_reports/docs_integrity_validation/20260203-2333`

| Metric | Value |
| --- | ---:|
| JSON Blocks Checked | 2 |
| Mismatched Blocks | 0 |
| Errors | 0 |
| Missing Documents | 0 |

**Concerns:** None

---

## Metrics Stub Coverage

**Artifact:** `.repo_studios/reports/healthview/producer_reports/metrics_anchor_stub_validation/20260203-2333`

| Metric | Value |
| --- | ---:|
| Files Checked | 36 |
| Anchors Referenced | 0 |
| Missing Count | 0 |

**Concerns:** None — informational: no anchors referenced this run

---

## Code ↔ Docs Churn

**Artifact:** `.repo_studios/reports/healthview/producer_reports/code_doc_churn/20260203-2333`

| Metric | Value |
| --- | ---:|
| Commits Examined | 18 |
| Modules Missing Docs | 1 |
| Modules With Docs | 2 |

**Concerns:** ⚠️ 1 module(s) missing docs

---

## Undocumented Logic

**Artifact:** `.repo_studios/reports/healthview/producer_reports/undocumented_logic/20260203-2333`

| Metric | Value |
| --- | ---:|
| Modules Scanned | 85 |
| Modules With Findings | 39 |
| Entities Missing Docs | 374 |
| Docstring Coverage % | 58.72 |

**Concerns:** ❌ 374 missing-doc entities; ⚠️ docstring coverage 58.7%
