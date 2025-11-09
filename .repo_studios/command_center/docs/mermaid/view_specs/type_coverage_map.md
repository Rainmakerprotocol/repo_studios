# Type Coverage Map View Spec

**Status:** Multi-view coexistence verified with regression coverage (2025-11-09)

## Goal

Highlight type hint adoption across functions in a CommandView artifact by clustering functions into coverage strength buckets. The view gives maintainers a quick read on where type annotations are strong, moderate, weak, or missing entirely.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.functions` (Map) | `typeHintCoverage`, `annotationCoverage`, `metrics.coverage`, `name`, `id`, `moduleId` | Provides coverage ratios and naming metadata for every function. |
| Scope helper (`resolveTypeCoverageScope`) | `currentLevel`, `rootId`, `domainId`, `moduleId`, `functionId`, `neighborhoods` | Filters the normalized functions using shared zoom logic before diagram generation. |
| View options | `moduleId`, `bucketLimit`, `viewLabel` | Optional overrides supplied by the viewer definition; defaults keep the bucket limit at eight entries per group. |

## Transformations

1. Normalize the functions collection into a `Map` regardless of the incoming structure.
2. Extract coverage values preferring `typeHintCoverage`, falling back to `annotationCoverage`, `coverage`, or `metrics.coverage` when appropriate.
3. Bucket each scoped function into `strong` (≥ 0.8), `moderate` (0.5–0.79), `weak` (< 0.5), or `unknown` when coverage cannot be parsed.
4. Derive human-readable labels (function name + module + coverage percent) for each bucket, truncating to the configured item limit and appending an overflow notice when additional entries exist.
5. Generate Mermaid nodes for the central hub plus each bucket, applying class definitions to keep colors consistent with the Quality Metrics palette. The central label reflects the active zoom scope (root, domain, module, or function neighborhood).
6. Compute aggregate stats for each bucket to drive status messaging and the tracker table.

## Mermaid Output Structure

```
graph TD
  type_coverage_center["Type Coverage Map"]
  type_bucket_strong["Strong >= 80%\nFunctions: n\n..."]
  type_bucket_moderate[...]
  type_bucket_weak[...]
  type_bucket_unknown[...]
  type_coverage_center --> type_bucket_strong
  ...
  classDef typeStrong ...
  class type_bucket_strong typeStrong;
```

Each bucket node lists up to eight representative functions with coverage percentages and module hints. Additional entries are summarized as `+X more`.

## Implementation References

- Builder: `buildTypeCoverageMapDiagram()` in `.repo_studios/command_center/viewer/ui/builders/type_coverage_map.js`, consumed by `buildTypeCoverageMapViewDefinition()` in `.repo_studios/command_center/viewer/ui/viewer.js` with scoped input from `resolveTypeCoverageScope()`.
- Styling: Bucket class definitions (strong/moderate/weak/unknown) bake in palette colors aligned with the viewer's dark theme.
- Availability gating: `requirements: ["typeCoverage"]` ensures the view appears only when normalized function records expose coverage metrics.

## Verification & Hardening

- Scope helper regression `.repo_studios/tests/tests_command_center/viewer/test_type_coverage_scope.py` exercises root/module filtering and empty-scope messaging.
- Builder regression coverage in `.repo_studios/tests/tests_command_center/viewer/test_type_coverage_map_view.py` validates error handling, Mermaid output, stats computation, and render stability.
- Multi-view coexistence test `.repo_studios/tests/tests_command_center/viewer/test_quality_metrics_multi_view_coexistence.py` confirms toggling between the Quality Metrics view and the Health pack overview preserves state.
- Helper exports (`__test__`) expose utilities for unit testing bucket labels, coverage extraction, and sanitization logic.

## Future Enhancements

- Surface aggregate percentages (e.g., percentage of total functions in each bucket) directly in node labels once normalization exposes total counts.
- Blend churn or complexity metrics into the bucket listings to prioritize risky, weakly annotated hotspots.
- Add domain-level aggregate percentages once normalization exposes totals per slice.
- Provide optional table export mirroring the scoped bucket contents for spreadsheet workflows.
- Blend churn or complexity metrics into the bucket listings to prioritize risky, weakly annotated hotspots.