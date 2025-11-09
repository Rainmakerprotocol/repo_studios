# Complexity Heatmap View Spec

**Status:** Controls wired with regression coverage (2025-11-09)

## Goal

Surface functions with high cyclomatic complexity so maintainers can prioritize refactoring efforts. The heatmap will cluster functions by severity buckets and highlight modules concentrating complex logic.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.functions` (Map) | `cyclomaticComplexity`, `metrics.complexity`, `metrics.lineCount`, `metrics.coverage`, `moduleId`, `name`, `id` | Primary source for per-function complexity scores plus supporting metadata (line counts, coverage, module ownership). |
| `state.normalizedData.metrics.modules` (Map) | `gitChurn`, `coverageSignals`, `lineCount` | Supplies module-level churn aggregates and supplemental coverage hints used when building overlays and module hotspot summaries. |
| Scope helper (`resolveComplexityHeatmapScope`) | `currentLevel`, `rootId`, `domainId`, `moduleId`, `functionId`, `neighborhoods` | Provides zoom-aware function filtering before the diagram is generated. |
| View options | `bucketLimit`, `severityThresholds`, `moduleAggregateLimit`, `coverageRiskThreshold`, `viewLabel` | Optional overrides governing bucket sizing, severity breakpoints, hotspot rollups, and coverage risk thresholds. |

### Upstream Guarantees

- Cyclomatic complexity metrics are emitted by the CommandView inventory producer (`generate_commandview_inventory.py`) and normalized into `state.normalizedData.functions`.
- Existing regression coverage (`.repo_studios/tests/tests_producers/test_generate_commandview_inventory.py::test_cyclomatic_complexity_counts_branches`) guards the producer output, ensuring every function carries a numeric complexity score.

## Transformations

1. Normalize the scoped function collection into a `Map` for deterministic iteration.
2. Extract a single complexity value per function, preferring `cyclomaticComplexity` and falling back to `metrics.complexity` when needed; capture line counts and coverage ratios for supplemental overlays.
3. Bucket functions by severity (**Low**, **Moderate**, **High**, **Extreme**) using configurable thresholds and capture an `Unknown` bucket for missing data, truncating each bucket to the configured item limit and summarizing overflow with `+X more`.
4. Generate Mermaid nodes for the hub and each severity bucket, applying the shared Quality Metrics palette and embedding `Cx`, line counts, coverage percentages, and churn summaries in each label when available.
5. Aggregate coverage stats (average, counts below the configured risk threshold) and build module hotspot summaries highlighting extreme/high counts, coverage averages, and churn signals.
6. Emit the Mermaid definition plus the enriched stats payload so status messaging and sidebar summaries can surface coverage risk and module hotspots alongside the severity counts.

## Implementation References

- Normalized complexity and module metric data lives in `.repo_studios/command_center/viewer/ui/viewer.js` (`createFunctionRecord`, `createModuleRecord`, and `buildMetricsCache`).
- Builder: `.repo_studios/command_center/viewer/ui/builders/complexity_heatmap.js`, consumed by `buildComplexityHeatmapViewDefinition()` in `.repo_studios/command_center/viewer/ui/viewer.js` with scope filtering from `resolveComplexityHeatmapScope()`.

## Verification & Hardening

- Producer regression coverage: `.repo_studios/tests/tests_producers/test_generate_commandview_inventory.py::test_cyclomatic_complexity_counts_branches`.
- Normalization smoke: `.repo_studios/tests/tests_command_center/viewer/test_function_call_graph_view.py` exercises `state.normalizedData.functions` in a module-focused context (confirming complexity values are propagated).
- Builder regression coverage: `.repo_studios/tests/tests_command_center/viewer/test_complexity_heatmap_view.py` validates bucket assignment, overlays, module hotspot stats, and deterministic output.
- Scope helper regression: `.repo_studios/tests/tests_command_center/viewer/test_complexity_heatmap_scope.py` confirms zoom filtering and empty-scope messaging.
- Multi-view coexistence: `.repo_studios/tests/tests_command_center/viewer/test_quality_metrics_multi_view_coexistence.py` now toggles Complexity, Type, and Documentation views without state drift.

## Future Enhancements

- Provide tooltip overlays in the UI to expose raw complexity, line counts, churn metrics, and recent coverage deltas per node.
- Thread module hotspot summaries into the Command Center sidebar so operators can pivot straight from the heatmap to remediation queues.
- Explore inline trend spark lines once churn history metrics are emitted (commit cadence over time) to complement the current snapshot overlays.
