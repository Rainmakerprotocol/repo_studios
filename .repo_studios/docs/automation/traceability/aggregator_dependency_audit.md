# Aggregator Dependency Audit (Draft 2025-11-24)

## Purpose

- Capture the current data sources each aggregator script depends on.
- Highlight where aggregators still ingest raw producer artifacts or ad-hoc log scans instead of the hardened consumer bundles.
- Establish modernization targets so the upcoming refactor can align aggregators with the new provenance guarantees.

## Current Aggregator Inputs

| Aggregator Script | Primary Inputs | Observations |
| --- | --- | --- |
| `.repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py` | Prefers consumer bundles (`.repo_studios/reports/consumer_reports/monkey_patch_risk/monkey_patch_risk-*/summary.json` + `bundle_summary.json`), falling back to producer `report.json` when necessary. | Modernized 2025-11-24: records provenance, writes timestamped bundles under `.repo_studios/reports/aggregator_reports/monkey_patch_trends/`, maintains latest pointers, and mirrors markdown into the newest consumer run. |
| `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py` | Prefers consumer test-log bundles (summary + `report.json`) for provenance, supplements with optional precomputed metrics, and falls back to raw JUnit discovery only when summaries are missing. | Modernized 2025-11-24: records git window, bundle summary path, logs directory, and optional metrics source in `bundle_summary.json`, maintains latest pointers, enforces pruning, and exposes pytest coverage exercising consumer-first and logs fallback flows. |

## Modernization Targets

1. **Monkey Patch Trends** _(modernization complete — reference plan: `.repo_studios/docs/automation/traceability/analyze_monkey_patch_trends_modernization_plan.md`)_
   - ✅ Consumes the hardened consumer bundles with fallback to producer scans only when summaries are unavailable.
   - ✅ Captures provenance via `bundle_summary.json` and embeds lineage in aggregator artifacts.
   - ✅ Emits timestamped trend bundles with pruning + latest pointers under `.repo_studios/reports/aggregator_reports/monkey_patch_trends/` and mirrors the markdown into the latest consumer run.

2. **Churn × Complexity Heatmap** _(modernization complete — reference plan: `.repo_studios/docs/automation/traceability/generate_churn_complexity_heatmap_modernization_plan.md`)_
   - ✅ Prefers `generate_test_log_health_report` bundles and records provenance; falls back to JUnit only when summaries are unavailable.
   - ✅ Writes timestamped bundles with pruning/latest pointers under `aggregator_reports/churn_complexity_heatmap/` and mirrors input references in Markdown.
   - ⚖️ Deferred helper extraction: metrics computation still lives in-script; revisit a shared producer helper when additional aggregators surface overlapping churn/complexity needs.

## Next Actions

- todo (done 2025-11-24): Design retention + provenance expectations for aggregator outputs so they align with the consumer bundle guarantees.
- todo (done 2025-11-24): Draft modernization plan for `analyze_monkey_patch_trends.py` (consumer-first ingestion, artifact relocation) and socialize before changing code.
- todo (done 2025-11-24): Draft modernization plan for `generate_churn_complexity_heatmap.py`, including whether a new producer should supply the churn/complexity metrics for reuse (decision deferred pending future aggregator helpers).
