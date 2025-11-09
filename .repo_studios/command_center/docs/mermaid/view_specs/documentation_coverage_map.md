# Documentation Coverage Map View Spec

**Status:** Multi-view coexistence verified with regression coverage (2025-11-09)

## Goal

Highlight documentation quality across functions in a CommandView artifact by grouping items into documented, missing, or unknown buckets. The view helps reviewers spot modules that lack docstrings or contain stale notes before onboarding or remediation cycles.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.functions` (Map) | `docstringQuality.status`, `docstringQuality.exists`, `name`, `id`, `moduleId` | Provides docstring presence and status metadata for every function. |
| View options | `bucketLimit`, `viewLabel` | Optional overrides supplied by the viewer definition; defaults cap each bucket at eight entries. |

## Transformations

1. Normalize the functions collection into a `Map` so downstream logic can rely on consistent iteration.
2. Resolve the active scope based on the viewer zoom level: repository-wide at Level 0, filtered by root at Level 0, by domain at Level 1, by module at Levels 2–3, and by function neighborhood at Level 4 (with graceful fallback when selections have no data).
3. Derive a documentation status for each function (`documented`, `missing`, `unknown`, or `stale`) using `docstringQuality.status` when available and falling back to `exists`.
4. Bucket functions into `documented`, `missing`, and `unknown` groups, treating unrecognized statuses as `unknown` while preserving a `stale` count inside the documented bucket summary.
5. Build human-readable labels that include the function name, module, and status summary, truncating each bucket to the configured limit and appending a `+X more` suffix when additional items are present.
6. Generate Mermaid nodes for the central hub plus each bucket, applying class definitions that align with the Quality Metrics palette (green for documented, amber for stale/unknown, red for missing).
7. Compute aggregate stats used for sidebar summaries and status messaging (counts per bucket plus stale indicator) and tailor the status string to the active scope.

## Mermaid Output Structure

```
graph TD
  doc_coverage_center["Documentation Coverage Map"]
  doc_bucket_documented["Documented\nFunctions: n\n..."]
  doc_bucket_missing[...]
  doc_bucket_unknown[...]
  doc_coverage_center --> doc_bucket_documented
  ...
  classDef docDocumented ...
  class doc_bucket_documented docDocumented;
```

Each bucket lists up to eight representative functions. Additional entries are summarized using a trailing `+X more` line.

## Implementation References

- Builder: `buildDocumentationCoverageMapDiagram()` in `.repo_studios/command_center/viewer/ui/builders/documentation_coverage_map.js`, consumed by `buildDocumentationCoverageMapViewDefinition()` in `.repo_studios/command_center/viewer/ui/viewer.js`.
- Scope resolution helper: `resolveDocumentationCoverageScope()` in `.repo_studios/command_center/viewer/ui/builders/documentation_coverage_scope.js`, reused by the viewer to keep zoom-level decomposition deterministic and testable.
- Styling: Bucket class definitions (`docDocumented`, `docMissing`, `docUnknown`) follow the Quality Metrics color palette for quick visual scanning.
- Availability gating: `requirements: ["docstringQuality"]` ensures the view appears only when normalized function records include docstring metadata.

## Verification & Hardening

- Builder regression coverage in `.repo_studios/tests/tests_command_center/viewer/test_documentation_coverage_map_view.py` validates Mermaid output, status messaging, stats computation, and repeat render stability.
- Scope helper coverage in `.repo_studios/tests/tests_command_center/viewer/test_documentation_coverage_scope.py` exercises root, domain, module, and function-neighborhood filtering along with empty-scope messaging.
- Multi-view coexistence test `.repo_studios/tests/tests_command_center/viewer/test_quality_metrics_multi_view_coexistence.py` confirms toggling between Documentation Coverage and Type Coverage views preserves state, stats, and Mermaid definitions.
- Helper exports (`__test__`) expose normalization utilities for targeted unit tests covering bucket labeling and status mapping.

## Future Enhancements

- Surface docstring freshness metadata once normalization exposes `lastUpdatedAt` timestamps to highlight stale documentation separately from missing entries.
- Blend documentation severity with TODO counts or lint findings to prioritize follow-up work.
- Introduce optional module scoping filters so maintainers can drill into documentation health for a single package or subsystem.