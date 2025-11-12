````markdown
# Public vs Private API View Spec

**Status:** Data slice ready (2025-11-12)

## Goal

Contrast the externally exposed API surface of each module with its internal helpers so reviewers can confirm that exported symbols match design intent, spot stray implicit APIs, and prioritize documentation or enforcement work for implicit public contracts.

## Inputs

| Source | Fields Used | Notes |
| --- | --- | --- |
| `state.normalizedData.modules` (Map) | `moduleId`, `exportSummary`, `apiSurface`, `globals` | Module records now expose an `apiSurface` summary built during normalization plus raw global metadata for value kind context. |
| `state.normalizedData.functions` (Map) | `id`, `name`, `lineno`, `metrics.coverage`, `typeHintCoverage`, `docstringQuality` | Function records provide naming, location, and quality metrics referenced by the API surface classifier. |
| `state.normalizedData.classes` (Map) | `id`, `name`, `lineno`, `methodCount`, `docstringQuality` | Class metadata enables the view to highlight exported vs. internal types alongside helper counts. |
| CommandView payload (`files[].exports`) | `symbols`, `missing`, `dynamic`, `lineno` | Declared export set (e.g., `__all__`) drives explicit exposure classification and missing export warnings. |
| CommandView payload (`files[].functions`, `files[].classes`, `files[].globals`) | `name`, `qualified_name`, `line`, `signature`, `docstring_quality`, `value_kind` | Raw definitions underpin export resolution and allow implicit/explicit/ private labeling by naming convention. |
| CommandView payload (`imports_detailed`) | `kind`, `module`, `names[].name`, `names[].asname`, `lineno` | Required to distinguish true re-exports from local definitions when symbols are forwarded from other modules. |

## Transformations

1. Resolve declared exports using `buildModuleExportSummary()` so each symbol is tagged as local function/class/global, re-export, or missing entry.
2. Classify module functions, classes, and globals into `exported`, `implicit`, `internal`, or `private` buckets via `buildModuleApiSurface()`:
   - Symbols in the exported set are labeled **exported**.
   - Leading underscores mark **private** helpers regardless of export status.
   - When `__all__` is present (`hasDeclaredExports`), any non-exported, non-private symbol is considered **internal**.
   - Modules without `__all__` treat non-underscore symbols as **implicit** public APIs to surface accidental exposure risk.
3. Attach per-symbol metadata (line number, docstring quality, coverage/type-hint metrics, value kind, method counts) so builders can drive rich status messaging.
4. Aggregate counts for public vs. internal slices across functions, classes, and globals alongside export/missing/re-export totals for view-wide statistics.
5. Normalize re-export metadata (source module, qualified name, line number) to power diagram annotations and fallback messaging.

## Mermaid Output Structure (planned)

```
graph TD
  classDef exported fill:#0f172a,stroke:#38bdf8,color:#e0f2fe;
  classDef implicit fill:#1f2937,stroke:#22d3ee,color:#f0fdfa;
  classDef internal fill:#1f2937,stroke:#facc15,color:#fef9c3;
  classDef private fill:#111827,stroke:#f87171,color:#fee2e2;
  alpha_api_public_func["public_func()\nexported"]
  alpha_api_utility["utility()\ninternal"]
  alpha_api__helper["_helper()\nprivate"]
  alpha_api_public_func -->|documented| alpha_api_PublicClass
```

The builder will place exported/implicit symbols in dedicated swimlanes opposite private/internal helpers, using color coding for each category. Re-exports will appear as annotated edges referencing their source modules.

## Implementation References

- Normalization helper `buildModuleApiSurface()` (added to `.repo_studios/command_center/viewer/ui/viewer.js`) classifies module symbols and surfaces structured exposure metadata.
- Module ingestion in `normalizeCommandViewData()` now stores the API surface on each module record for direct consumption by future builders.
- Export resolution continues to rely on `buildModuleExportSummary()` for consistent symbol provenance and missing entry tracking.

## Verification & Hardening

- Regression `.repo_studios/tests/tests_command_center/viewer/test_public_private_api_data_normalization.py` asserts that the API surface categorization correctly differentiates exported, internal, implicit, and private symbols (including re-export and missing export tracking).
- Existing export summary regressions (e.g., `test_export_contract_data_normalization.py`) guard upstream inventory expectations so classification receives accurate symbol provenance.
- Builders will reuse the normalized metadata to compute diagram stats; future wiring will extend the automated coverage suite with view and coexistence tests.

## Future Enhancements

- Incorporate policy hooks to flag modules that expose implicit APIs without explicit exports.
- Blend documentation and type-coverage metrics into status details to highlight under-documented public contracts.
- Offer diff mode comparing API surfaces between snapshots to support release readiness reviews.
````