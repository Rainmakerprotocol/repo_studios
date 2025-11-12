````markdown
# Cyclomatic Complexity Map View Spec

**Status:** Controls wired (2025-11-12)

## Goal

Surface cyclomatic complexity hotspots across the repository so operators can benchmark function complexity, identify modules that exceed agreed thresholds, and stage refactoring candidates before wiring the Quality Metrics pack diagram.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.functions` (Map) | `id`, `name`, `moduleId`, `cyclomaticComplexity`, `metrics.coverage`, `metrics.lineCount`, `docstringQuality` | Normalization copies per-function complexity into `cyclomaticComplexity` and retains coverage/line counts for contextual overlays. |
| `state.normalizedData.modules` (Map) | `moduleId`, `statistics.complexity`, `statistics.coverage` | Module snapshots expose aggregate complexity stats leveraged for module summaries. |
| CommandView payload (`files[].functions`) | `cyclomatic_complexity`, `coverage.executed`, `line_count`, `docstring_quality` | Producer exports raw complexity metrics with coverage and size info that normalization consumes. |
| CommandView payload (`statistics.complexity`) | `repository_average`, `repository_max`, `by_module` | Aggregated metrics support comparison messaging between repository baselines and scoped selections. |

## Transformations

1. `createFunctionRecord()` copies `cyclomatic_complexity` into `cyclomaticComplexity` and preserves coverage and line count metrics for each function.
2. Module aggregation retains complexity distributions inside `state.normalizedData.modules` to power per-module summaries and sort orderings.
3. The builder buckets functions into severity tiers (extreme, high, moderate, low, unknown) using shared thresholds already exercised by the Complexity Heatmap view.
4. Diagram stats aggregate function counts per tier, compute module summaries (averages, maxima, coverage deltas), and surface top offenders with identifiers for drill-down.
5. Status messaging combines repository aggregates with scoped module/function insights and scope fallback notices to highlight risk concentration.

## Mermaid Output Structure

```
graph TD
  classDef moduleSummary fill:#0b1120,stroke:#94a3b8,color:#e2e8f0
  classDef bucketHub fill:#111827,stroke:#64748b,color:#e2e8f0
  classDef complexityExtreme fill:#450a0a,stroke:#fca5a5,color:#fee2e2
  classDef complexityHigh fill:#7f1d1d,stroke:#f87171,color:#fee2e2
  classDef complexityModerate fill:#b45309,stroke:#fbbf24,color:#fffbeb
  classDef complexityLow fill:#166534,stroke:#22c55e,color:#ecfdf5
  classDef complexityUnknown fill:#374151,stroke:#9ca3af,color:#f3f4f6

  subgraph alpha_core_group["alpha.core\nExtreme 1 · High 0 · Moderate 1 · Low 0 · Unknown 0"]
    direction TB
    alpha_core_hub["Functions 2 · Avg CC 13.50 · Max CC 21"]
    class alpha_core_hub moduleSummary;
    alpha_core_extreme_bucket["Extreme Complexity\nFunctions 1"]
    class alpha_core_extreme_bucket bucketHub;
    alpha_core_hub --> alpha_core_extreme_bucket
    alpha_core_extreme_0["controller\nCC 21 · Cov 42% · Lines 230"]
    class alpha_core_extreme_0 complexityExtreme;
    alpha_core_extreme_bucket --> alpha_core_extreme_0
    alpha_core_moderate_bucket["Moderate Complexity\nFunctions 1"]
    class alpha_core_moderate_bucket bucketHub;
    alpha_core_hub --> alpha_core_moderate_bucket
    alpha_core_moderate_0["helper\nCC 8 · Cov 71% · Lines 90"]
    class alpha_core_moderate_0 complexityModerate;
    alpha_core_moderate_bucket --> alpha_core_moderate_0
  end
```

Each module renders as a subgraph housing a summary hub plus severity buckets. Buckets fan out to top functions (limited per module) with overlays for complexity, coverage, and line counts; overflow nodes capture truncated entries. Future iterations may add edges to highlight cross-module callers.

## Implementation References

- `createFunctionRecord()` in `.repo_studios/command_center/viewer/ui/viewer.js` exposes `cyclomaticComplexity`, coverage ratios, and line counts on each function record.
- `buildCyclomaticComplexityMapDiagram()` in `.repo_studios/command_center/viewer/ui/builders/cyclomatic_complexity_map.js` orchestrates aggregation, severity bucketing, and Mermaid emission.
- Complexity thresholds and aggregation helpers introduced for `complexity_heatmap.mmd` are reused for consistent severity classification.
- Producer regression `.repo_studios/tests/tests_producers/test_generate_commandview_inventory.py::test_cyclomatic_complexity_counts_branches` guards the underlying CommandView metric.

## Verification & Hardening

- Existing normalization coverage in `.repo_studios/tests/tests_command_center/viewer/test_complexity_heatmap_view.py` validates that complexity values reach the builders without mutation.
- Deterministic exercises now live in `.repo_studios/tests/tests_command_center/viewer/test_cyclomatic_complexity_map_view.py` and the multi-view regression suite at `.repo_studios/tests/tests_command_center/viewer/test_quality_metrics_multi_view_coexistence.py`.

## Future Enhancements

- Blend churn and coverage overlays directly into node labels to favor high-complexity, low-coverage hotspots.
- Add diff mode to compare complexity shifts between successive CommandView snapshots.
- Provide policy hooks that flag modules exceeding agreed average complexity thresholds for command center reporting.
````