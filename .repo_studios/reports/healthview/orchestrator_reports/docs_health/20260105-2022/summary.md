# Docs Health Run

Run: `20260105-2022` | Completed: 2026-01-05T20:22:52.093952+00:00

## Pipeline Status

| Step | Status | Detail |
| --- | --- | --- |
| doc-index | ✅ success | docs=347, headings=2506 |
| anchor-inventory | ✅ success | docs=143, missing_h1=7, missing_h2=3, slugs=789, duplicates=81, cross_file_docs=114, repeated_docs=0 |
| anchor-validation | ✅ success | status=ok, issues=0 |
| docs-integrity | ✅ success | status=ok, mismatches=0 |
| metrics-stub | ✅ success | status=ok, missing=0 |
| code-doc-churn | ✅ success | missing_docs=2 |
| undocumented-logic | ✅ success | modules_with_findings=40 |
| aggregate | ✅ success | overall=49.08 |

---

## Overall Score

**Artifact:** `.repo_studios/reports/healthview/aggregator_reports/docs_health_signals/20260105-2022`

| Metric | Value |
| --- | ---:|
| Overall Score | 49.08 |

| Category | Score | Status | Weight |
| --- | ---:| --- | ---:|
| freshness | 33.33333333333333 | critical | 0.35 |
| coverage | 56.2 | critical | 0.35 |
| structure | 36.59283682097371 | critical | 0.15 |
| integrity | 100.0 | healthy | 0.1 |
| hygiene | 45.0 | critical | 0.05 |

**Concerns:** ❌ 4 category(ies) are critical

---

## Doc Index

**Artifact:** `.repo_studios/reports/healthview/producer_reports/doc_index/20260105-2022`

| Metric | Value |
| --- | ---:|
| Documents | 347 |
| Headings | 2506 |
| Links | 285 |
| Missing Descriptions | 50 |
| Placeholder Docs | 76 |
| Duplicate Slugs | 8 |
| Link Density | 0.8213256484149856 |

**Concerns:** ⚠️ 50 missing descriptions; ⚠️ 76 placeholder docs; ⚠️ 8 duplicate slugs

---

## Anchor Inventory

**Artifact:** `.repo_studios/reports/healthview/producer_reports/anchor_inventory/20260105-2022`

| Metric | Value |
| --- | ---:|
| Documents Scanned | 143 |
| Missing H1 | 7 |
| Missing H2 | 3 |
| Total Slugs | 789 |
| Cross-file Duplicates | 81 |
| Docs w/ Cross-file Duplicates | 114 |
| Docs w/ Repeated Anchors | 0 |

**Concerns:** ⚠️ 7 missing H1; ⚠️ 3 missing H2

---

## Anchor Validation

**Artifact:** `.repo_studios/reports/healthview/producer_reports/markdown_anchor_validation/20260105-2022`

| Metric | Value |
| --- | ---:|
| Files Scanned | 143 |
| Links Checked | 347 |
| Issue Count | 0 |
| Missing Files | 0 |
| Missing Anchors | 0 |

**Concerns:** None

---

## Docs Integrity

**Artifact:** `.repo_studios/reports/healthview/producer_reports/docs_integrity_validation/20260105-2022`

| Metric | Value |
| --- | ---:|
| JSON Blocks Checked | 2 |
| Mismatched Blocks | 0 |
| Errors | 0 |
| Missing Documents | 0 |

**Concerns:** None

---

## Metrics Stub Coverage

**Artifact:** `.repo_studios/reports/healthview/producer_reports/metrics_anchor_stub_validation/20260105-2022`

| Metric | Value |
| --- | ---:|
| Files Checked | 36 |
| Anchors Referenced | 0 |
| Missing Count | 0 |

**Concerns:** None — informational: no anchors referenced this run

---

## Code ↔ Docs Churn

**Artifact:** `.repo_studios/reports/healthview/producer_reports/code_doc_churn/20260105-2022`

| Metric | Value |
| --- | ---:|
| Commits Examined | 20 |
| Modules Missing Docs | 2 |
| Modules With Docs | 1 |

**Concerns:** ⚠️ 2 module(s) missing docs

---

## Undocumented Logic

**Artifact:** `.repo_studios/reports/healthview/producer_reports/undocumented_logic/20260105-2022`

| Metric | Value |
| --- | ---:|
| Modules Scanned | 84 |
| Modules With Findings | 40 |
| Entities Missing Docs | 392 |
| Docstring Coverage % | 56.2 |

**Concerns:** ❌ 392 missing-doc entities; ⚠️ docstring coverage 56.2%
