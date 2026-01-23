# Docs Health Run

Run: `20260123-2342` | Completed: 2026-01-23T23:44:20.289682+00:00

## Pipeline Status

| Step | Status | Detail |
| --- | --- | --- |
| doc-index | ✅ success | docs=333, headings=2465 |
| anchor-inventory | ✅ success | docs=144, missing_h1=7, missing_h2=3, slugs=794, duplicates=81, cross_file_docs=115, repeated_docs=0 |
| anchor-validation | ✅ success | status=ok, issues=0 |
| docs-integrity | ✅ success | status=ok, mismatches=0 |
| metrics-stub | ✅ success | status=ok, missing=0 |
| code-doc-churn | ✅ success | missing_docs=1 |
| undocumented-logic | ✅ success | modules_with_findings=40 |
| aggregate | ✅ success | overall=62.52 |

---

## Overall Score

**Artifact:** `.repo_studios/reports/healthview/aggregator_reports/docs_health_signals/20260123-2344`

| Metric | Value |
| --- | ---:|
| Overall Score | 62.52 |

| Category | Score | Status | Weight |
| --- | ---:| --- | ---:|
| freshness | 66.66666666666666 | warning | 0.35 |
| coverage | 56.3 | critical | 0.35 |
| structure | 36.54439546599495 | critical | 0.15 |
| integrity | 100.0 | healthy | 0.1 |
| hygiene | 80.0 | healthy | 0.05 |

**Concerns:** ❌ 2 category(ies) are critical

---

## Doc Index

**Artifact:** `.repo_studios/reports/healthview/producer_reports/doc_index/20260123-2342`

| Metric | Value |
| --- | ---:|
| Documents | 333 |
| Headings | 2465 |
| Links | 286 |
| Missing Descriptions | 40 |
| Placeholder Docs | 77 |
| Duplicate Slugs | 5 |
| Link Density | 0.8588588588588588 |

**Concerns:** ⚠️ 40 missing descriptions; ⚠️ 77 placeholder docs; ⚠️ 5 duplicate slugs

---

## Anchor Inventory

**Artifact:** `.repo_studios/reports/healthview/producer_reports/anchor_inventory/20260123-2342`

| Metric | Value |
| --- | ---:|
| Documents Scanned | 144 |
| Missing H1 | 7 |
| Missing H2 | 3 |
| Total Slugs | 794 |
| Cross-file Duplicates | 81 |
| Docs w/ Cross-file Duplicates | 115 |
| Docs w/ Repeated Anchors | 0 |

**Concerns:** ⚠️ 7 missing H1; ⚠️ 3 missing H2

---

## Anchor Validation

**Artifact:** `.repo_studios/reports/healthview/producer_reports/markdown_anchor_validation/20260123-2342`

| Metric | Value |
| --- | ---:|
| Files Scanned | 144 |
| Links Checked | 348 |
| Issue Count | 0 |
| Missing Files | 0 |
| Missing Anchors | 0 |

**Concerns:** None

---

## Docs Integrity

**Artifact:** `.repo_studios/reports/healthview/producer_reports/docs_integrity_validation/20260123-2344`

| Metric | Value |
| --- | ---:|
| JSON Blocks Checked | 2 |
| Mismatched Blocks | 0 |
| Errors | 0 |
| Missing Documents | 0 |

**Concerns:** None

---

## Metrics Stub Coverage

| Metric | Value |
| --- | ---:|
| Files Checked |  |
| Anchors Referenced |  |
| Missing Count |  |

**Concerns:** None

---

## Code ↔ Docs Churn

**Artifact:** `.repo_studios/reports/healthview/producer_reports/code_doc_churn/20260123-2344`

| Metric | Value |
| --- | ---:|
| Commits Examined | 8 |
| Modules Missing Docs | 1 |
| Modules With Docs | 2 |

**Concerns:** ⚠️ 1 module(s) missing docs

---

## Undocumented Logic

**Artifact:** `.repo_studios/reports/healthview/producer_reports/undocumented_logic/20260123-2344`

| Metric | Value |
| --- | ---:|
| Modules Scanned | 84 |
| Modules With Findings | 40 |
| Entities Missing Docs | 392 |
| Docstring Coverage % | 56.3 |

**Concerns:** ❌ 392 missing-doc entities; ⚠️ docstring coverage 56.3%
