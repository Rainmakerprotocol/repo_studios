# Complexity Heatmap View Spec

**Status:** Data slice documented and validated (2025-11-09)

## Goal

Surface functions with high cyclomatic complexity so maintainers can prioritize refactoring efforts. The heatmap will cluster functions by severity buckets and highlight modules concentrating complex logic.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.functions` (Map) | `cyclomaticComplexity`, `metrics.complexity`, `metrics.lineCount`, `moduleId`, `name`, `id` | Primary source for per-function complexity scores plus supporting metadata (line counts, module ownership). |
| View options | `bucketLimit`, `severityThresholds`, `viewLabel` | Optional overrides that will govern bucket sizing and severity breakpoints once the builder is implemented. |

### Upstream Guarantees

- Cyclomatic complexity metrics are emitted by the CommandView inventory producer (`generate_commandview_inventory.py`) and normalized into `state.normalizedData.functions`.
- Existing regression coverage (`.repo_studios/tests/tests_producers/test_generate_commandview_inventory.py::test_cyclomatic_complexity_counts_branches`) guards the producer output, ensuring every function carries a numeric complexity score.

## Transformations (Planned)

1. Normalize the function collection into a `Map` for deterministic iteration.
2. Extract a single complexity value per function, preferring `cyclomaticComplexity` and falling back to `metrics.complexity` when needed.
3. Bucket functions by severity (e.g., **Low**, **Moderate**, **High**, **Extreme**) using configurable thresholds; retain top offenders per bucket and summarize overflow with a `+X more` sentinel.
4. Derive module-level aggregates to support future heatmap overlays (count of high-complexity functions per module).
5. Generate Mermaid nodes for the hub and each severity bucket, applying color scales aligned with the Quality Metrics palette.
6. Emit aggregate stats (counts per bucket, maximum complexity) to inform status messaging and sidebar summaries.

## Implementation References

- Normalized complexity data lives in `.repo_studios/command_center/viewer/ui/viewer.js` (`createFunctionRecord` and `buildMetricsCache`).
- Future builder module will reside under `.repo_studios/command_center/viewer/ui/builders/complexity_heatmap.js` and integrate with `viewer.js` via a `buildComplexityHeatmapViewDefinition()` helper.

## Verification & Hardening

- Producer regression coverage: `.repo_studios/tests/tests_producers/test_generate_commandview_inventory.py::test_cyclomatic_complexity_counts_branches`.
- Normalization smoke: `.repo_studios/tests/tests_command_center/viewer/test_function_call_graph_view.py` exercises `state.normalizedData.functions` in a module-focused context (confirming complexity values are propagated).
- Additional builder and coexistence tests will be authored once controls are wired.

## Future Enhancements

- Blend Git churn or coverage signals to spotlight complex and volatile functions.
- Allow operators to scope the heatmap by module or domain via viewer options.
- Add tooltip overlays in the UI to expose raw complexity, line counts, and churn metrics per node.
