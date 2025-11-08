# Function Inventory Overview View Spec

**Status:** Data slice defined (2025-11-08)

## Goal

Provide a high-level health snapshot for a selected CommandView artifact, summarizing module counts, function totals, documentation coverage, type-hint adoption, TODO hotspots, and top-level package density. The view helps reviewers identify areas that warrant deeper refactoring or documentation passes before drilling into Level-of-Detail diagrams.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `moduleId`, `id` | Required to determine total module count and derive package root segments. |
| `state.normalizedData.functions` (Map) | `docstringQuality.exists`, `typeHintCoverage`, `annotationCoverage`, `todoTags` | Function-level metadata captured during normalization; coverage fallback reads `annotationCoverage` when `typeHintCoverage` is absent. |
| `deriveRootSegment(moduleId)` helper | Derived root segment | Buckets modules under their top-level package for quick density scanning. |

## Transformations

1. Count all modules and functions available in the normalized registry.
2. Iterate every function record to:
   - Increment docstring coverage counters using `docstringQuality.exists`.
   - Average type-hint coverage, preferring `typeHintCoverage` with fallback to `annotationCoverage`.
   - Track functions carrying one or more TODO tags via `todoTags`.
3. Aggregate module counts by `deriveRootSegment(moduleId)` and capture the top five roots by volume.
4. Format summary strings for Mermaid nodes, ensuring label content stays within ASCII and newline limits.
5. Assign Mermaid class definitions for docstring, type coverage, and TODO highlight nodes to ensure consistent visual cues.

## Mermaid Output Structure

```
Inventory Overview (central node)
├─ Docstring coverage (with/without docstrings)
├─ Type hint adoption (tracked samples + average)
├─ TODO hotspots (function count)
└─ Top 5 root packages with module counts
```

All nodes emit under a `graph TD` diagram and include class styling hooks for coherent coloring.

## Implementation References

- Builder: `buildFunctionInventoryOverviewViewDefinition()` in `.repo_studios/command_center/viewer/ui/viewer.js` (lines ~2247-2330).
- Availability gating: `requirements: ["inventoryBasics", "docstringQuality", "typeCoverage"]` in `VIEW_PACKS` definition ensures the view only activates when requisite metadata is present.
- Normalization source: Function records created by `createFunctionRecord()` capture the `docstring_quality`, `type_hint_coverage`, `annotation_quality.coverage`, and `todo_tags` fields from CommandView payloads.

## Verification & Hardening

- Spot checked `.repo_studios_commandview_20251108-1835.json` to confirm function entries include `docstring_quality.exists`, `type_hint_coverage`, and `todo_tags` fields.
- `evaluateViewAvailability()` now blocks the view if function docstring quality objects are absent, preventing runtime null dereferences.
- Mermaid builder updated to respect `docstringQuality.exists`, aligning with the producer schema and avoiding reliance on deprecated keys (`has_docstring`, `present`).

## Future Enhancements

- Include coverage rate deltas by comparing screening summary aggregates once viewer overlays support dual-source inputs.
- Surface module-level counts alongside function totals in the top-root list when Level 1 domain definitions stabilize.
- Add optional annotations for max cyclomatic complexity or churn stats per root to highlight risk concentration.
